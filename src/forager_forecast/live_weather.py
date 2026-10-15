"""Live weather for the PNW pilot's scoring: which cells, which days, the batched archive request,
and the free tier's budget (Forager RECORD -814; D19, D21, D25).

Every request pins what `open_meteo.archive_request_url` pins for one cell (models=era5_seamless,
elevation=nan, cell_selection=nearest, timezone=UTC, the same daily and hourly variables), with
many cells per request. Open-Meteo refuses a multi-location request unless elevation carries one
value per location (seen live 2026-10-10), so `elevation` is "nan" repeated.

The days are the ones T1's windows need for the scored ISO week: the longest window (90 days)
ending the day before the week's Monday (`weather_windows.window_days`), so no feature sees the
week it scores.

Cost follows Open-Meteo's pricing page (open_meteo.api_call_units): each location counts, and a
span over 14 days counts fractionally. The budget keeps every rolling minute and hour, and every
UTC day, under limits set below the free tier's (600, 5,000, 10,000).
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from urllib.parse import urlencode

from forager_forecast.cells import Cell, IsoWeek
from forager_forecast.open_meteo import (
    ARCHIVE_URL,
    DAILY_VARIABLES,
    HOURLY_VARIABLES,
    MODEL,
    api_call_units,
)
from forager_forecast.t1_design import WINDOW_DAYS, Box


class WrongCell(ValueError):
    """Open-Meteo answered for a grid point other than the cell requested."""


def box_cells(box: Box) -> list[Cell]:
    """Every 0.1 degree centre inside the box, edges inclusive, sorted."""
    south, north = round(box.south * 10), round(box.north * 10)
    west, east = round(box.west * 10), round(box.east * 10)
    return [Cell(la, lo) for la in range(south, north + 1) for lo in range(west, east + 1)]


def window_span(week: IsoWeek) -> tuple[date, date]:
    """First and last day the windows of `week` read: the longest window before its Monday."""
    monday = week.monday()
    return monday - timedelta(days=max(WINDOW_DAYS)), monday - timedelta(days=1)


def multi_archive_url(cells: Sequence[Cell], start: date, end: date) -> str:
    if end < start:
        raise ValueError(f"end {end.isoformat()} is before start {start.isoformat()}")
    if not cells:
        raise ValueError("no cells")
    query = {
        "latitude": ",".join(f"{c.center_latitude:.1f}" for c in cells),
        "longitude": ",".join(f"{c.center_longitude:.1f}" for c in cells),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(DAILY_VARIABLES),
        "hourly": ",".join(HOURLY_VARIABLES),
        "models": MODEL,
        "elevation": ",".join("nan" for _ in cells),
        "cell_selection": "nearest",
        "timezone": "UTC",
    }
    return f"{ARCHIVE_URL}?{urlencode(query)}"


def request_cost(locations: int, start: date, end: date) -> float:
    variables = len(DAILY_VARIABLES) + len(HOURLY_VARIABLES)
    return api_call_units((end - start).days + 1, variables, locations)


@dataclass(frozen=True)
class Budget:
    per_minute: float
    per_hour: float
    per_day: float

    def wait_seconds(
        self, ledger: Sequence[tuple[datetime, float]], now: datetime, cost: float
    ) -> float:
        """Seconds to wait before a request of `cost` keeps every window under its limit."""
        for name in ("per_minute", "per_hour", "per_day"):
            if cost > getattr(self, name):
                raise ValueError(f"a request of {cost} calls exceeds {name} {getattr(self, name)}")
        waits = [0.0]
        for span, limit in (
            (timedelta(minutes=1), self.per_minute),
            (timedelta(hours=1), self.per_hour),
        ):
            inside = sorted((t, c) for t, c in ledger if t > now - span)
            used = sum(c for _t, c in inside)
            for t, c in inside:  # drop the oldest until the request fits
                if used + cost <= limit:
                    break
                used -= c
                waits.append((t + span - now).total_seconds())
        day_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
        used_today = sum(c for t, c in ledger if t >= day_start)
        if used_today + cost > self.per_day:
            waits.append((day_start + timedelta(days=1) - now).total_seconds())
        return max(waits)


def is_rate_limited(status: int, body) -> bool:
    if status == 429:
        return True
    if isinstance(body, dict) and body.get("error"):
        return "limit" in str(body.get("reason", "")).lower()
    return False


def split_by_cell(cells: Sequence[Cell], body) -> dict[Cell, dict]:
    """One response object per requested cell, in request order, each checked against the grid
    point Open-Meteo echoes back."""
    items = body if isinstance(body, list) else [body]
    if len(items) != len(cells):
        raise WrongCell(f"{len(items)} responses for {len(cells)} cells")
    out = {}
    for cell, item in zip(cells, items, strict=True):
        lat, lon = item.get("latitude"), item.get("longitude")
        if (
            lat is None
            or lon is None
            or not math.isclose(lat, cell.center_latitude, abs_tol=1e-4)
            or not math.isclose(lon, cell.center_longitude, abs_tol=1e-4)
        ):
            raise WrongCell(f"cell {cell.id} answered at {lat}, {lon}")
        out[cell] = item
    return out

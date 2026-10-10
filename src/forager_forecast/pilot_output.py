"""The PNW pilot's scoring inputs and outputs (Forager RECORD -814; D12, D53, D55, D56).

Inputs: Open-Meteo archive bodies, one per cell, turned into the arrays `scripts/pnw_weather.py`
stores (`<variable>_points`, `<variable>_values`, `start`), so the scoring script reads them back
through the training path itself (`pnw_weather.load` and `pnw_weather.weather_matrix`) and no
feature code is copied here. ERA5-Land variables are keyed by the 0.1 degree cell; precipitation
by the ERA5 0.25 degree point nearest the cell centre (`cells.quarter_cell_for`, D46, D54), as the
store's files are. Every cell sharing a quarter point must report the same rain; a disagreement
raises rather than picking one.

Outputs: D55's cell properties, one GeoJSON FeatureCollection per week (the combined file the
dispatch names) and the same features split by 1 degree block (D55 (1)), plus the manifest. The
number is called sighting chance and nothing else (D12).

A block is named by the south-west corner of the 1 degree square holding the cell centre:
n47w123 holds centres with 47 <= latitude < 48 and -123 <= longitude < -122. A cell whose centre
sits on a block edge belongs to the block north or east of it, so its polygon reaches 0.05 degree
into the neighbouring block.
"""

import math
from collections.abc import Mapping, Sequence
from datetime import date, timedelta

import numpy as np

from forager_forecast.cells import Cell, quarter_cell_for
from forager_forecast.weather_windows import DailyWeather

LAND_VARIABLES = {
    "temperature": "temperature_mean_c",
    "soil_temperature": "soil_temperature_mean_c",
    "soil_moisture": "soil_moisture_mean",
}

GROUP = {
    "key": "cantharellus",
    "display_name": "Chanterelles",
    "gbif_taxon_key": 9623860,  # t1_design.CANTHARELLUS_GENUS_KEY
    # https://api.inaturalist.org/v1/taxa?q=Cantharellus&rank=genus, read 2026-10-10: 47348 is
    # the fungus genus (892745 is an animal genus of the same name).
    "inaturalist_taxon_id": 47348,
    "rank": "genus",
}

# Plain labels for the weather features, by prefix (daily_grid.FEATURES), with the unit.
_DRIVER_LABELS = {
    "temperature_mean": ("Air temperature, mean of the last {w} days", "°C"),
    "precipitation_sum": ("Rain, total of the last {w} days", "mm"),
    "soil_temperature_mean": ("Soil temperature, mean of the last {w} days", "°C"),
    "soil_moisture_mean": ("Soil moisture, mean of the last {w} days", "m³/m³"),
}


# What the training grids hold after pnw_weather's conversion (°C, mm, m³/m³), as Open-Meteo
# declares it, and the range a value in that unit can take in the PNW. A value outside the range
# means a unit or offset went wrong (reviewer B1: a kelvin offset applied to soil moisture).
OPEN_METEO_UNITS = {
    ("daily_units", "temperature_2m_mean"): "°C",
    ("daily_units", "precipitation_sum"): "mm",
    ("hourly_units", "soil_temperature_0_to_7cm"): "°C",
    ("hourly_units", "soil_moisture_0_to_7cm"): "m³/m³",
}
PLAUSIBLE = {
    "temperature": (-60.0, 60.0),
    "soil_temperature": (-60.0, 70.0),
    "soil_moisture": (0.0, 1.0),
    "precipitation": (0.0, 500.0),
}


class UnitMismatch(ValueError):
    """A weather value is not in the unit the training grids hold."""


def check_units(payload: dict) -> None:
    for (section, variable), unit in OPEN_METEO_UNITS.items():
        got = payload.get(section, {}).get(variable)
        if got != unit:
            raise UnitMismatch(f"{variable} arrived in {got!r}, the training grids hold {unit!r}")


def check_ranges(arrays: Mapping[str, np.ndarray]) -> None:
    """Every non-NaN value of each variable inside its plausible range, in the npz layout."""
    for variable, (low, high) in PLAUSIBLE.items():
        values = np.asarray(arrays[f"{variable}_values"], dtype=float)
        finite = values[np.isfinite(values)]
        if finite.size and (finite.min() < low or finite.max() > high):
            raise UnitMismatch(
                f"{variable} spans {finite.min():.4g} to {finite.max():.4g}, outside {low} to "
                f"{high}: a unit or offset is wrong"
            )


class RainDisagrees(ValueError):
    """Two cells sharing one ERA5 point reported different rain for one day."""


def weather_arrays(
    per_cell: Mapping[Cell, Mapping[date, DailyWeather]], start: date, end: date
) -> dict[str, np.ndarray]:
    """pnw_weather's npz layout for the cells given, days start..end, NaN where a day is absent."""
    n = (end - start).days + 1
    days = [start + timedelta(days=i) for i in range(n)]
    cells = sorted(per_cell)
    out: dict[str, np.ndarray] = {"start": np.array(start.isoformat())}
    for variable, attr in LAND_VARIABLES.items():
        values = np.full((len(cells), n), np.nan)
        for r, cell in enumerate(cells):
            for i, d in enumerate(days):
                row = per_cell[cell].get(d)
                if row is not None:
                    values[r, i] = getattr(row, attr)
        out[f"{variable}_points"] = np.array(
            [(c.lat_tenths, c.lon_tenths) for c in cells], dtype=np.int32
        ).reshape(-1, 2)
        out[f"{variable}_values"] = values
    rain: dict[tuple[int, int], np.ndarray] = {}
    source: dict[tuple[int, int], Cell] = {}
    for cell in cells:
        q = quarter_cell_for(cell.center_latitude, cell.center_longitude)
        key = (q.lat_quarters, q.lon_quarters)
        series = np.full(n, np.nan)
        for i, d in enumerate(days):
            row = per_cell[cell].get(d)
            if row is not None:
                series[i] = row.precipitation_mm
        if key in rain:
            both = ~np.isnan(rain[key]) & ~np.isnan(series)
            if not np.array_equal(rain[key][both], series[both]):
                bad = int(np.argmax(both & (rain[key] != series)))
                raise RainDisagrees(
                    f"cells {source[key].id} and {cell.id} share ERA5 point q{key[0]}_{key[1]} "
                    f"but differ on {days[bad].isoformat()}: {rain[key][bad]} and {series[bad]}"
                )
            rain[key] = np.where(np.isnan(rain[key]), series, rain[key])
        else:
            rain[key], source[key] = series, cell
    points = sorted(rain)
    out["precipitation_points"] = np.array(points, dtype=np.int32).reshape(-1, 2)
    out["precipitation_values"] = (
        np.vstack([rain[p] for p in points]) if points else np.zeros((0, n))
    )
    return out


def cell_polygon(cell: Cell) -> list[list[list[float]]]:
    """The cell's 0.1 degree square, WGS84, counter-clockwise, closed (RFC 7946)."""
    s, n = (cell.lat_tenths - 0.5) / 10, (cell.lat_tenths + 0.5) / 10
    w, e = (cell.lon_tenths - 0.5) / 10, (cell.lon_tenths + 0.5) / 10
    ring = [[w, s], [e, s], [e, n], [w, n], [w, s]]
    return [[[round(x, 2), round(y, 2)] for x, y in ring]]


def block_id(cell: Cell) -> str:
    lat = math.floor(cell.lat_tenths / 10)
    lon = math.floor(cell.lon_tenths / 10)
    ns = "n" if lat >= 0 else "s"
    ew = "e" if lon >= 0 else "w"
    return f"{ns}{abs(lat):02d}{ew}{abs(lon):03d}"


def driver_label(feature: str) -> tuple[str, str] | None:
    """(label with unit, unit) for a weather window feature, None for calendar and place."""
    prefix, _, window = feature.rpartition("_")
    if prefix not in _DRIVER_LABELS or not window.endswith("d"):
        return None
    text, unit = _DRIVER_LABELS[prefix]
    return f"{text.format(w=window[:-1])} ({unit})", unit


def drivers(
    names: Sequence[str], values: np.ndarray, contributions: np.ndarray, top: int = 3
) -> list[dict]:
    """The weather features that moved this cell's score most, by the size of their contribution
    (LightGBM pred_contrib, in log-odds), largest first, with the feature's own value."""
    ranked = sorted(
        (i for i, n in enumerate(names) if driver_label(n) is not None),
        key=lambda i: (-abs(float(contributions[i])), names[i]),
    )
    out = []
    for i in ranked[:top]:
        label, _unit = driver_label(names[i])
        out.append({"label": label, "value": round(float(values[i]), 3)})
    return out


def cell_feature(
    cell: Cell,
    week_start: date,
    chance: float,
    weather_through: date | None,
    model_version: str,
    driver_list: list[dict],
    uncertainty: tuple[float, float] | None = None,
) -> dict:
    if not 0.0 <= chance <= 1.0:
        raise ValueError(f"chance {chance} for {cell.id} is outside 0 to 1")
    low, high = uncertainty if uncertainty else (None, None)
    return {
        "type": "Feature",
        "id": cell.id,
        "geometry": {"type": "Polygon", "coordinates": cell_polygon(cell)},
        "properties": {
            "group": GROUP["key"],
            "week": week_start.isoformat(),
            "chance": round(float(chance), 4),
            "uncertainty_low": low,
            "uncertainty_high": high,
            "applicable": True,
            "drivers": driver_list,
            "weather_through": weather_through.isoformat() if weather_through else None,
            "model_version": model_version,
        },
    }


def collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def blocks(features: list[dict]) -> dict[str, dict]:
    by: dict[str, list[dict]] = {}
    for f in features:
        lat_t, lon_t = (int(x) for x in f["id"].split("_"))
        by.setdefault(block_id(Cell(lat_t, lon_t)), []).append(f)
    return {k: collection(v) for k, v in sorted(by.items())}

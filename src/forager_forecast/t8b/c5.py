"""C5, the unseen season (plan section 7; D159 (5)): the frozen model against T1's calendar on
ISO weeks 27 to 52 of 2026, scored once, from a GBIF download taken after 2027-02-15.

The scorer takes the two frozen models (frozen.load has already checked each against its recorded
checksum) and the 2026 units built from the later download, and returns the skill, its interval
and the pass. It refuses:
- while any C5 reading is unruled (design.PENDING, step "c5");
- a download created before 2027-02-16T00:00Z (PENDING C5-after, proposed);
- any unit outside ISO 2026 weeks 27 to 52, since the units are built by other code and a stray
  unit would mean that code is wrong.
Weeks whose outcome had already been read are left out, and named, as the plan says. Step 1 found
none (the report's item 6), so `excluded_weeks` is empty unless a later finding says otherwise.

"Beats" is PENDING C5-beats, proposed: the pooled Brier skill is above zero; the 1,000-resample
cell interval (seed 20260918, T8's bar.skill_interval) is reported beside it, not required.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import numpy as np

from forager_forecast.t8 import bar as tb
from forager_forecast.t8b import design
from forager_forecast.t8b import frozen as fz


class C5Refused(RuntimeError):
    """C5 cannot be scored on what it was given."""


@dataclass(frozen=True)
class C5Units:
    unit: np.ndarray  # unit ids
    cell: np.ndarray  # cell id per unit (the bootstrap's clusters)
    iso_year: np.ndarray
    iso_week: np.ndarray
    y: np.ndarray  # 0/1 Cantharellus positive
    x_main: np.ndarray  # the main model's columns, in its frozen feature order
    x_calendar: np.ndarray  # the calendar's columns


def earliest_download() -> datetime:
    day = design.C5_DOWNLOAD_AFTER + timedelta(days=1)
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def check_download(created: datetime) -> None:
    """Refuses a download GBIF created before the day after 2027-02-15 (UTC)."""
    if created.tzinfo is None:
        raise C5Refused("the download's created time carries no time zone")
    if created < earliest_download():
        raise C5Refused(
            f"the download was created {created.isoformat()}; C5 needs one from "
            f"{earliest_download().isoformat()} on"
        )


def _check_units(u: C5Units) -> None:
    n = len(u.y)
    for name in ("unit", "cell", "iso_year", "iso_week"):
        if len(getattr(u, name)) != n:
            raise C5Refused(f"{name} has {len(getattr(u, name))} entries for {n} units")
    if len(u.x_main) != n or len(u.x_calendar) != n:
        raise C5Refused("the model inputs are not one row per unit")
    if not np.isin(u.y, (0.0, 1.0)).all():
        raise C5Refused("outcomes are not all 0 or 1")
    if (np.asarray(u.iso_year) != design.C5_YEAR).any():
        raise C5Refused(f"a unit is not in ISO year {design.C5_YEAR}")
    if not np.isin(u.iso_week, design.C5_WEEKS).all():
        raise C5Refused("a unit is outside ISO weeks 27 to 52")
    if len(set(np.asarray(u.unit).tolist())) != n:
        raise C5Refused("unit ids repeat")


def score_c5(
    main: fz.FrozenModel,
    calendar: fz.FrozenModel,
    units: C5Units,
    download_created: datetime,
    excluded_weeks: Sequence[int] = (),
) -> dict:
    design.require_ruled("c5")
    check_download(download_created)
    _check_units(units)
    left_out = sorted(int(w) for w in set(excluded_weeks))
    keep = ~np.isin(units.iso_week, left_out)
    if not keep.any():
        raise C5Refused("no unit is left to score")
    y = np.asarray(units.y, dtype=np.float64)[keep]
    p = fz.predict(main, units.x_main[keep])
    q = fz.predict(calendar, units.x_calendar[keep])
    figures = tb.skill_interval(p, q, y, np.asarray(units.cell)[keep])
    return {
        "condition": "C5",
        "passed": bool(figures["skill"] > 0.0),
        "needs": "Brier skill against T1's calendar above zero (PENDING C5-beats, proposed)",
        **figures,
        "weeks_left_out": left_out,
        "main": main.name,
        "calendar": calendar.name,
        "download_created": download_created.isoformat(),
    }

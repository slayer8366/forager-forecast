"""D28's midnight check, measured: is midnight on the 1st special, or common on every day?

The owner's provisional "keep the midnight check" (Forager RECORD -601) drops a record whose clock
time is exactly 00:00:00 on the 1st of a month; RECORD -602 asks for it to be measured first. The
measure was fixed and committed before any count was read
(docs/audits/2026-10-06-d28-midnight-measure.md, commit 00d23f6): per dataset, midnight records on
the 1st against midnight records on any day, tested one-sided against the 1st's calendar share
12/365.2425, which is the other days' midnight rate carried to the 1st. At least 300 midnight
records to be tested; a family level of 0.01, Bonferroni over the datasets tested; "clear excess"
also needs the 95% Clopper-Pearson lower end at twice the expected share. It applies no rule.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import time

from forager_forecast.records.date_quality import (
    CALENDAR_SHARE,
    FAMILY_LEVEL,
    REFERENCE_SHARE,
    binomial_upper_tail,
    clopper_pearson,
)
from forager_forecast.records.filters import SOURCE_STAGE, Steps, is_default_date
from forager_forecast.records.occurrence import Record

# Fixed before any count was read (docs/audits/2026-10-06-d28-midnight-measure.md).
EXPECTED_SHARE = CALENDAR_SHARE  # 12/365.2425: the 1st's share of calendar days
MIN_MIDNIGHT = 300  # expected on the 1st is then about 9.9
CLEAR_FACTOR = 2.0  # clear excess: the interval's lower end at twice the expected share or more

MIDNIGHT = time(0, 0, 0)

TOO_FEW = "too few to test"
COMMON = "midnight is common on every day"
SMALL = "small excess on the 1st"
CLEAR = "midnight on the 1st is special"


def is_midnight(record: Record) -> bool:
    """Exactly 00:00:00 as the loader parsed it: the clock half of is_default_date."""
    return record.event_time == MIDNIGHT


def filters_before_date_step(steps: Steps) -> tuple:
    """The filters a record must clear to reach the step list's date step."""
    positions = [i for i, step in enumerate(steps.filters) if step.drops is is_default_date]
    if len(positions) != 1:
        raise ValueError(f"no default-date step in the list (found {len(positions)})")
    return steps.filters[: positions[0]]


@dataclass
class DatasetMidnight:
    dataset_key: str
    timed: int = 0
    midnight_by_day: Counter[int] = field(default_factory=Counter)
    timed_not_midnight: int = 0
    timed_not_midnight_on_first: int = 0
    first_midnight_reaching_date_step: Counter[str] = field(default_factory=Counter)

    @property
    def m(self) -> int:
        return sum(self.midnight_by_day.values())

    @property
    def k(self) -> int:
        return self.midnight_by_day[1]


class MidnightTable:
    """On_pass sink: every record at the source stage, by datasetKey (before any filter).

    lists names step lists whose date-step reach is counted for midnight on the 1st (informative).
    """

    def __init__(self, lists: Mapping[str, Steps] | None = None) -> None:
        self._before = {name: filters_before_date_step(s) for name, s in (lists or {}).items()}
        self._by_dataset: dict[str, DatasetMidnight] = {}

    def add(self, stage: str, record: Record) -> None:
        if stage != SOURCE_STAGE or record.event_time is None:
            return
        row = self._by_dataset.get(record.dataset_key)
        if row is None:
            row = self._by_dataset[record.dataset_key] = DatasetMidnight(record.dataset_key)
        row.timed += 1
        day = record.event_date.day
        if not is_midnight(record):
            row.timed_not_midnight += 1
            if day == 1:
                row.timed_not_midnight_on_first += 1
            return
        row.midnight_by_day[day] += 1
        if day == 1:
            for name, before in self._before.items():
                if not any(step.drops(record) for step in before):
                    row.first_midnight_reaching_date_step[name] += 1

    def datasets(self) -> dict[str, DatasetMidnight]:
        return dict(self._by_dataset)


@dataclass(frozen=True)
class MidnightAssessment:
    dataset_key: str
    timed: int
    m: int
    k: int
    any_day_share: float | None
    share_on_first: float | None
    ratio_to_expected: float | None
    ratio_to_one_in_thirty: float | None
    own_calendar_share: float | None
    interval: tuple[float, float] | None
    p_value: float | None
    level_each: float | None
    verdict: str


def _assess_one(row: DatasetMidnight, level_each: float | None, tested: bool) -> MidnightAssessment:
    m, k = row.m, row.k
    share = k / m if m else None
    interval = clopper_pearson(k, m) if m else None
    p_value = binomial_upper_tail(k, m, EXPECTED_SHARE) if m else None
    if not tested:
        verdict = TOO_FEW
    elif p_value >= level_each:
        verdict = COMMON
    elif interval[0] >= CLEAR_FACTOR * EXPECTED_SHARE:
        verdict = CLEAR
    else:
        verdict = SMALL
    return MidnightAssessment(
        dataset_key=row.dataset_key,
        timed=row.timed,
        m=m,
        k=k,
        any_day_share=m / row.timed if row.timed else None,
        share_on_first=share,
        ratio_to_expected=share / EXPECTED_SHARE if share is not None else None,
        ratio_to_one_in_thirty=share / REFERENCE_SHARE if share is not None else None,
        own_calendar_share=(
            row.timed_not_midnight_on_first / row.timed_not_midnight
            if row.timed_not_midnight
            else None
        ),
        interval=interval,
        p_value=p_value,
        level_each=level_each if tested else None,
        verdict=verdict,
    )


def assess_midnight(rows: Iterable[DatasetMidnight]) -> list[MidnightAssessment]:
    """Each dataset's verdict under the measure fixed before any count (module docstring)."""
    rows = list(rows)
    tested = [row for row in rows if row.m >= MIN_MIDNIGHT]
    level_each = FAMILY_LEVEL / len(tested) if tested else None
    return [_assess_one(row, level_each, row.m >= MIN_MIDNIGHT) for row in rows]


def pooled(rows: Iterable[DatasetMidnight]) -> DatasetMidnight:
    """All datasets as one row, for a whole-download line that is shown and is not a verdict."""
    out = DatasetMidnight("(all datasets)")
    for row in rows:
        out.timed += row.timed
        out.midnight_by_day.update(row.midnight_by_day)
        out.timed_not_midnight += row.timed_not_midnight
        out.timed_not_midnight_on_first += row.timed_not_midnight_on_first
        out.first_midnight_reaching_date_step.update(row.first_midnight_reaching_date_step)
    return out

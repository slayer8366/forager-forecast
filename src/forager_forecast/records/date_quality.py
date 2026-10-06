"""D28: the day-of-month table for date-only records, by dataset, and the candidate date rules.

D28 keeps the stricter date rule provisionally (a date-only record on the first of a month is
dropped as a defaulted date) and asks for a table that shows, per dataset, whether date-only
records fall on the 1st about one time in thirty, as real dates would, or clearly more often.
"The owner rules on the final rule before any model is fit." This module builds that table and
the test fixed before any count was read (docs/audits/2026-10-06-d27-d29-verify-report.md,
section 3, committed in ea579c2 at 2026-10-06T10:56:58-07:00), and the three candidate rules as
step lists, so their effect on the survivor counts can be shown. It applies no rule: the step
lists in records/filters.py keep the provisional one.

Plain standard-library arithmetic: the exact binomial tail and the Clopper-Pearson interval both
come from the regularized incomplete beta function, by the continued fraction (Numerical Recipes,
2nd ed., section 6.4), evaluated in log space so a dataset of millions of records does not
underflow before the tail is formed.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from datetime import time

from forager_forecast.records.filters import SOURCE_STAGE, FilterStep, Steps, is_default_date
from forager_forecast.records.occurrence import Record

# Fixed before any count was read (verify report, section 3).
REFERENCE_SHARE = 1 / 30  # D28's "one in thirty"
CALENDAR_SHARE = 12 / 365.2425  # the 1st's share of calendar days; shown beside, never a verdict
MIN_DATE_ONLY = 300  # below this the expected count on the 1st is under 10
FAMILY_LEVEL = 0.01  # one-sided, Bonferroni over the datasets tested
CLEAR_EXCESS_SHARE = 2 / 30  # at twice the reference, at least half the 1st's records are excess
INTERVAL_LEVEL = 0.95

TOO_FEW = "too few to test"
CLOSE = "close to 1 in 30"
SMALL = "small excess"
CLEAR = "clear excess"


def is_date_only(record: Record) -> bool:
    """The eventDate carried no clock time (the loader leaves event_time None only then)."""
    return record.event_time is None


def is_midnight_first_with_clock(record: Record) -> bool:
    """The first of a month at 00:00:00 written as a clock time: the T1 dispatch's own wording.

    Every candidate rule drops these; D28 is about date-only records on the 1st only.
    """
    return record.event_date.day == 1 and record.event_time == time(0, 0, 0)


@dataclass
class DatasetDays:
    """One dataset's loaded records, and its date-only records by day of month."""

    dataset_key: str
    loaded: int = 0
    date_only_by_day: Counter[int] = field(default_factory=Counter)
    midnight_first_with_clock: int = 0

    @property
    def n(self) -> int:
        return sum(self.date_only_by_day.values())

    @property
    def k(self) -> int:
        return self.date_only_by_day[1]


class DayOfMonthTable:
    """On_pass sink: every record at the source stage, by datasetKey (before any filter)."""

    def __init__(self) -> None:
        self._by_dataset: dict[str, DatasetDays] = {}

    def add(self, stage: str, record: Record) -> None:
        if stage != SOURCE_STAGE:
            return
        row = self._by_dataset.get(record.dataset_key)
        if row is None:
            row = self._by_dataset[record.dataset_key] = DatasetDays(record.dataset_key)
        row.loaded += 1
        if is_date_only(record):
            row.date_only_by_day[record.event_date.day] += 1
        elif is_midnight_first_with_clock(record):
            row.midnight_first_with_clock += 1

    def datasets(self) -> dict[str, DatasetDays]:
        return dict(self._by_dataset)


# The incomplete beta function and what is built on it.


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 1_000_000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        step = d * c
        h *= step
        if abs(step - 1.0) < 1e-15:
            return h
    raise ArithmeticError(f"incomplete beta did not converge for a={a}, b={b}, x={x}")


def regularized_beta(x: float, a: float, b: float) -> float:
    """I_x(a, b) for a, b > 0 and 0 <= x <= 1."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_front = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(log_front) * _beta_continued_fraction(a, b, x) / a
    return 1.0 - math.exp(log_front) * _beta_continued_fraction(b, a, 1.0 - x) / b


def binomial_upper_tail(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p): the one-sided exact test's p-value for an excess."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return regularized_beta(p, k, n - k + 1)


def _beta_quantile(target: float, a: float, b: float) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if regularized_beta(mid, a, b) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def clopper_pearson(k: int, n: int, level: float = INTERVAL_LEVEL) -> tuple[float, float]:
    """The exact two-sided interval for a binomial share k / n."""
    if not 0 <= k <= n or n <= 0:
        raise ValueError(f"need 0 <= k <= n and n > 0, got k={k}, n={n}")
    tail = (1.0 - level) / 2.0
    lower = 0.0 if k == 0 else _beta_quantile(tail, k, n - k + 1)
    upper = 1.0 if k == n else _beta_quantile(1.0 - tail, k + 1, n - k)
    return lower, upper


@dataclass(frozen=True)
class Assessment:
    dataset_key: str
    n: int
    k: int
    share: float | None
    ratio_to_reference: float | None
    ratio_to_calendar: float | None
    interval: tuple[float, float] | None
    p_value: float | None
    excess_on_first: float
    level_each: float | None
    verdict: str


def assess(rows: Iterable[DatasetDays]) -> list[Assessment]:
    """Each dataset's verdict under the test fixed before any count (module docstring).

    The level is split over the datasets with at least MIN_DATE_ONLY date-only records only.
    """
    rows = list(rows)
    tested = [row for row in rows if row.n >= MIN_DATE_ONLY]
    level_each = FAMILY_LEVEL / len(tested) if tested else None
    out = []
    for row in rows:
        n, k = row.n, row.k
        share = k / n if n else None
        interval = clopper_pearson(k, n) if n else None
        p_value = binomial_upper_tail(k, n, REFERENCE_SHARE) if n else None
        if n < MIN_DATE_ONLY:
            verdict = TOO_FEW
        elif p_value >= level_each:
            verdict = CLOSE
        elif interval[0] >= CLEAR_EXCESS_SHARE:
            verdict = CLEAR
        else:
            verdict = SMALL
        out.append(
            Assessment(
                dataset_key=row.dataset_key,
                n=n,
                k=k,
                share=share,
                ratio_to_reference=share / REFERENCE_SHARE if share is not None else None,
                ratio_to_calendar=share / CALENDAR_SHARE if share is not None else None,
                interval=interval,
                p_value=p_value,
                excess_on_first=k - n * REFERENCE_SHARE,
                level_each=level_each if n >= MIN_DATE_ONLY else None,
                verdict=verdict,
            )
        )
    return out


# The candidate rules, as the predicate of the date step.

DROP_ALL: Callable[[Record], bool] = is_default_date  # the provisional rule (D28, D65)
KEEP_ALL: Callable[[Record], bool] = is_midnight_first_with_clock  # the T1 dispatch's wording


@dataclass(frozen=True)
class DefaultDateInDatasets:
    """Per-dataset rule: midnight on the 1st always; date-only on the 1st only in these datasets."""

    datasets: frozenset[str]

    def __call__(self, record: Record) -> bool:
        if is_midnight_first_with_clock(record):
            return True
        return (
            record.event_date.day == 1
            and is_date_only(record)
            and record.dataset_key in self.datasets
        )


def with_date_rule(steps: Steps, drops: Callable[[Record], bool]) -> Steps:
    """The same step list with its default-date step's predicate replaced; names unchanged."""
    positions = [i for i, step in enumerate(steps.filters) if step.drops is is_default_date]
    if len(positions) != 1:
        raise ValueError(f"no default-date step to replace (found {len(positions)})")
    (at,) = positions
    filters = list(steps.filters)
    filters[at] = FilterStep(filters[at].name, drops)
    return replace(steps, filters=tuple(filters))

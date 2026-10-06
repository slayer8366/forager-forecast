"""T6, the observation layer: an effort surface per weather cell and ISO week (D101 to D108).

People report mushrooms where and when they go out, so a busy cell-week may be a crowded one. This
module estimates how many outings (distinct observer-days, D102) to expect in a cell, week and
day-type from four multiplicative parts (D106):

    expected outings (cell c, ISO week w, day-type d)
        = cell level(c) x year level(year of w) x season(band of c, week-of-year of w)
          x outings per day(d) x days(d)

where the band is the 5 degree latitude band of the cell's centre and day-type splits the week into
weekend (Saturday, Sunday, 2 days) and weekday (Monday to Friday, 5 days) (D105). Fitted from totals
by iterative proportional fitting (Bishop, Fienberg and Holland 1975, Discrete Multivariate
Analysis), so no table of zeros is ever built: the frame is every cell with an outing (D101) x the
573 whole ISO weeks x 2 day-types, about 49 million cells of which about 2% are non-zero.

Two rules here go beyond the proposal's wording and were fixed in this file before any fit ran:

- The sparse-cell pull (D106: lambda pseudo-weeks of the band's average added to each cell) is also
  applied to each band's season slot, toward that band's flat level. Without it a band with no
  outings in some week-of-year in the training years gets a season of zero there and an infinite
  held-out deviance. The proposal named the pull for cells only.
- Where a band has no training outings at all, its average is the continental one, for both pulls.

Domain logic only: no files, no zip, no Android or UI. scripts/t6_fit.py does the reading and
writing.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

from forager_forecast.cells import Cell, IsoWeek, cell_for, iso_week_of
from forager_forecast.records.occurrence import Record

# D101: the 573 ISO weeks lying wholly inside these two days.
FIRST_DAY = date(2015, 1, 1)
LAST_DAY = date(2025, 12, 31)
YEARS: tuple[int, ...] = tuple(range(2015, 2026))

# D105: day-types, and their days per week.
WEEKEND = 0
WEEKDAY = 1
DAYS_PER_TYPE = np.array([2.0, 5.0])

# D106: week-of-year slots (ISO week 53 is folded into week 52's slot) and latitude bands.
N_SLOTS = 52
BAND_TENTHS = 50  # 5 degrees, in the tenths of a degree cells are named by

# D103: lichens, read as GBIF class Lecanoromycetes.
BENCHMARK_CLASS_KEY = 180

# D108: the CC0 and CC BY track, by each record's own licence field (D48). The three values D26's
# download carries are CC_BY_NC_4_0, CC_BY_4_0 and CC0_1_0
# (docs/pulls/gbif-fungi-us-canada-2015-2025.datasets.json, records_by_own_license_field).
CC_TRACK_LICENSES = frozenset({"CC0_1_0", "CC_BY_4_0"})
KNOWN_LICENSES = frozenset({"CC0_1_0", "CC_BY_4_0", "CC_BY_NC_4_0"})

# D31 and D104: the seed for every random draw, the bootstrap, and the grid.
SEED = 20260918
BOOTSTRAP_RESAMPLES = 1000
GRID_PULL: tuple[float, ...] = (0.1, 0.3, 1.0, 3.0, 10.0)
GRID_SMOOTHING: tuple[int, ...] = (1, 3, 5, 9)

TERMS_FULL = frozenset({"cell", "year", "season", "day"})


# Units -------------------------------------------------------------------------------------------


def frame_weeks() -> tuple[IsoWeek, ...]:
    """The ISO weeks lying wholly inside FIRST_DAY to LAST_DAY, in order (D101)."""
    weeks = []
    week = iso_week_of(FIRST_DAY)
    monday = week.monday()
    while True:
        sunday = date.fromordinal(monday.toordinal() + 6)
        if sunday > LAST_DAY:
            break
        if monday >= FIRST_DAY:
            weeks.append(iso_week_of(monday))
        monday = date.fromordinal(monday.toordinal() + 7)
    return tuple(weeks)


def season_slot(week: IsoWeek) -> int:
    """0 for ISO week 1 up to 51 for week 52; week 53 shares week 52's slot."""
    return min(week.week, N_SLOTS) - 1


def day_type(day: date) -> int:
    return WEEKEND if day.weekday() >= 5 else WEEKDAY


def band_of(cell: Cell) -> int:
    """The 5 degree latitude band of the cell's centre, named by its southern edge in degrees.

    A centre exactly on a multiple of 5 degrees belongs to the band north of it."""
    return (cell.lat_tenths // BAND_TENTHS) * 5


def observer_of(record: Record) -> str:
    """recordedBy as written (trimmed by the loader); empty means one anonymous observer per
    dataset (D102)."""
    return record.recorded_by if record.recorded_by else f"anonymous:{record.dataset_key}"


def is_benchmark(record: Record) -> bool:
    return record.class_key == BENCHMARK_CLASS_KEY


# Outings -----------------------------------------------------------------------------------------


@dataclass
class OutingCounter:
    """Collects outings, distinct (observer, cell, day), from records that passed T6's steps.

    Four sets are kept: all licences and the CC0/CC BY track (D108), each for all fungi and for
    the benchmark (D103). An outing is in the CC track when it has at least one CC0 or CC BY
    record, which is the same as counting outings from those records alone. Records whose day
    falls in one of the two partial weeks are counted and left out (D101). A licence value outside
    KNOWN_LICENSES is counted by value and kept out of the CC track.
    """

    outside_frame_weeks: int = 0
    records_added: int = 0
    license_not_recognised: Counter[str] = field(default_factory=Counter)
    _week_index: dict[IsoWeek, int] = field(default_factory=dict)
    _outings: dict[tuple[str, bool], dict[tuple, tuple[Cell, int, int]]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self._week_index = {week: i for i, week in enumerate(frame_weeks())}
        for track in ("all", "cc"):
            for benchmark in (False, True):
                self._outings[(track, benchmark)] = {}

    def add(self, record: Record) -> None:
        self.records_added += 1
        week = iso_week_of(record.event_date)
        week_index = self._week_index.get(week)
        if week_index is None:
            self.outside_frame_weeks += 1
            return
        cell = cell_for(record.latitude, record.longitude)
        key = (observer_of(record), cell.lat_tenths, cell.lon_tenths, record.event_date)
        value = (cell, week_index, day_type(record.event_date))
        tracks = ["all"]
        if record.license not in KNOWN_LICENSES:
            self.license_not_recognised[record.license] += 1
        elif record.license in CC_TRACK_LICENSES:
            tracks.append("cc")
        for track in tracks:
            self._outings[(track, False)][key] = value
            if is_benchmark(record):
                self._outings[(track, True)][key] = value

    def outing_count(self, track: str, benchmark: bool) -> int:
        return len(self._outings[(track, benchmark)])

    def counts(
        self, track: str, benchmark: bool, frame: Sequence[Cell] | None = None
    ) -> OutingCounts:
        """Outings per (cell, week, day-type). The frame is every cell with an all-fungi outing in
        the track (D101), so a benchmark count takes the matching all-fungi frame."""
        outings = self._outings[(track, benchmark)]
        if frame is None:
            if benchmark:
                raise ValueError("a benchmark count needs the all-fungi frame of its track")
            frame = sorted({cell for cell, _, _ in outings.values()})
        index = {cell: i for i, cell in enumerate(frame)}
        tally: Counter[tuple[int, int, int]] = Counter()
        for cell, week_index, day in outings.values():
            if cell not in index:
                raise ValueError(f"cell {cell.id} has an outing but is not in the frame")
            tally[(index[cell], week_index, day)] += 1
        return OutingCounts.from_entries(frame, ((c, w, d, n) for (c, w, d), n in tally.items()))


@dataclass(frozen=True)
class OutingCounts:
    """Non-zero outings on the frame: every listed cell x frame_weeks() x the two day-types."""

    cells: tuple[Cell, ...]
    cell: np.ndarray  # entry -> cell index
    week: np.ndarray  # entry -> index into frame_weeks()
    day: np.ndarray  # entry -> WEEKEND or WEEKDAY
    count: np.ndarray  # entry -> outings (float64)
    band_ids: tuple[int, ...]
    cell_band: np.ndarray  # cell index -> band index into band_ids
    week_year: np.ndarray  # week index -> year index into YEARS
    week_slot: np.ndarray  # week index -> season slot
    weeks_per_year_slot: np.ndarray  # (len(YEARS), N_SLOTS): frame weeks in that year and slot

    @classmethod
    def from_entries(
        cls, cells: Sequence[Cell], entries: Iterable[tuple[int, int, int, float]]
    ) -> OutingCounts:
        rows = list(entries)
        cell = np.array([r[0] for r in rows], dtype=np.int64)
        week = np.array([r[1] for r in rows], dtype=np.int64)
        day = np.array([r[2] for r in rows], dtype=np.int64)
        count = np.array([r[3] for r in rows], dtype=np.float64)
        weeks = frame_weeks()
        if rows:
            if cell.min() < 0 or cell.max() >= len(cells):
                raise ValueError("entry names a cell outside the frame")
            if week.min() < 0 or week.max() >= len(weeks):
                raise ValueError("entry names a week outside the frame")
            if not set(np.unique(day)) <= {WEEKEND, WEEKDAY}:
                raise ValueError("entry names an unknown day-type")
            if (count < 0).any():
                raise ValueError("negative count")
            keys = cell * (len(weeks) * 2) + week * 2 + day
            if len(np.unique(keys)) != len(keys):
                raise ValueError("an entry repeats")
        bands = [band_of(c) for c in cells]
        band_ids = tuple(sorted(set(bands)))
        band_index = {b: i for i, b in enumerate(band_ids)}
        year_index = {y: i for i, y in enumerate(YEARS)}
        week_year = np.array([year_index[w.year] for w in weeks], dtype=np.int64)
        week_slot = np.array([season_slot(w) for w in weeks], dtype=np.int64)
        per = np.zeros((len(YEARS), N_SLOTS))
        np.add.at(per, (week_year, week_slot), 1.0)
        return cls(
            cells=tuple(cells),
            cell=cell,
            week=week,
            day=day,
            count=count,
            band_ids=band_ids,
            cell_band=np.array([band_index[b] for b in bands], dtype=np.int64),
            week_year=week_year,
            week_slot=week_slot,
            weeks_per_year_slot=per,
        )

    @property
    def n_cells(self) -> int:
        return len(self.cells)

    @property
    def n_bands(self) -> int:
        return len(self.band_ids)

    @property
    def entry_year(self) -> np.ndarray:
        return self.week_year[self.week]

    def total(self, year: int | None = None) -> float:
        if year is None:
            return float(self.count.sum())
        return float(self.count[self.entry_year == YEARS.index(year)].sum())


# The model ---------------------------------------------------------------------------------------


@dataclass(frozen=True, order=True)
class Config:
    pull: float  # pseudo-weeks of the band's average (D106)
    smoothing: int  # centred, wrapping moving window over week-of-year, in weeks

    @property
    def id(self) -> str:
        return f"pull={self.pull:g},smoothing={self.smoothing}"


def configs() -> tuple[Config, ...]:
    """The D104 grid, in grid order (the tie-break)."""
    return tuple(Config(p, s) for p in GRID_PULL for s in GRID_SMOOTHING)


@dataclass(frozen=True)
class Surface:
    """The four parts. year_level is NaN for a year the surface was not fitted on."""

    cell_level: np.ndarray  # per cell
    year_level: np.ndarray  # per year in YEARS
    season: np.ndarray  # (bands, N_SLOTS)
    day_rate: np.ndarray  # outings per day, (WEEKEND, WEEKDAY)
    terms: frozenset[str]
    config: Config | None
    iterations: int = 0

    @property
    def weekend_ratio(self) -> float:
        return float(self.day_rate[WEEKEND] / self.day_rate[WEEKDAY])


def circular_window_sum(values: np.ndarray, window: int) -> np.ndarray:
    """Sum over a centred window along the last axis, wrapping around the year's end."""
    if window < 1 or window % 2 == 0:
        raise ValueError(f"window must be a positive odd number of weeks, got {window}")
    half = window // 2
    return sum(np.roll(values, shift, axis=-1) for shift in range(-half, half + 1))


def _band_average(obs: np.ndarray, exposure: np.ndarray) -> np.ndarray:
    """Per band obs / exposure, the continental value where a band has no outings."""
    with np.errstate(divide="ignore", invalid="ignore"):
        average = obs / exposure
    continental = obs.sum() / exposure.sum()
    return np.where(obs > 0, average, continental)


def fit(
    counts: OutingCounts,
    train_years: Sequence[int],
    config: Config,
    terms: frozenset[str] = TERMS_FULL,
    cell_weights: np.ndarray | None = None,
    tolerance: float = 1e-10,
    max_iterations: int = 20000,
) -> Surface:
    """Iterative proportional fitting of the parts named in terms, on the training years.

    A part not in terms stays at 1 (outings per day stay equal on both day-types). cell_weights
    multiply each cell's outings and exposure, for the bootstrap clustered by cell.
    """
    unknown = set(terms) - TERMS_FULL
    if unknown:
        raise ValueError(f"unknown terms {sorted(unknown)}")
    if config.pull < 0:
        raise ValueError("pull must be zero or more")
    n, nb = counts.n_cells, counts.n_bands
    train = np.zeros(len(YEARS), dtype=bool)
    for year in train_years:
        train[YEARS.index(year)] = True
    if not train.any():
        raise ValueError("no training year")
    weights = np.ones(n) if cell_weights is None else np.asarray(cell_weights, dtype=np.float64)
    selected = train[counts.entry_year]
    ci = counts.cell[selected]
    wk = counts.week[selected]
    weighted = counts.count[selected] * weights[ci]
    obs_cell = np.bincount(ci, weights=counts.count[selected], minlength=n)
    obs_year = np.bincount(counts.week_year[wk], weights=weighted, minlength=len(YEARS))
    obs_season = np.bincount(
        counts.cell_band[ci] * N_SLOTS + counts.week_slot[wk],
        weights=weighted,
        minlength=nb * N_SLOTS,
    ).reshape(nb, N_SLOTS)
    obs_day = np.bincount(counts.day[selected], weights=weighted, minlength=2)
    weeks = counts.weeks_per_year_slot * train[:, None]
    q = config.pull / weeks.sum()
    band = counts.cell_band

    cell_level = np.ones(n)
    year_level = train.astype(np.float64)
    season = np.ones((nb, N_SLOTS))
    day_total = DAYS_PER_TYPE.copy()  # outings per day x days, per day-type

    for iteration in range(1, max_iterations + 1):
        before = (cell_level.copy(), year_level.copy(), season.copy(), day_total.copy())
        if "cell" in terms:
            per_slot = (weeks * year_level[:, None]).sum(axis=0)
            exposure = (season @ per_slot)[band] * day_total.sum()
            average = _band_average(
                np.bincount(band, weights=weights * obs_cell, minlength=nb),
                np.bincount(band, weights=weights * exposure, minlength=nb),
            )
            cell_level = (obs_cell + q * average[band] * exposure) / (exposure * (1.0 + q))
        if "year" in terms:
            band_mass = np.bincount(band, weights=weights * cell_level, minlength=nb)
            per_slot = (band_mass[:, None] * season).sum(axis=0)
            unit = weeks @ per_slot * day_total.sum()
            with np.errstate(divide="ignore", invalid="ignore"):
                year_level = np.where(train, obs_year / unit, 0.0)
        if "season" in terms:
            band_mass = np.bincount(band, weights=weights * cell_level, minlength=nb)
            per_slot = (weeks * year_level[:, None]).sum(axis=0)
            exposure = band_mass[:, None] * per_slot[None, :] * day_total.sum()
            numerator = circular_window_sum(obs_season, config.smoothing)
            denominator = circular_window_sum(exposure, config.smoothing)
            average = _band_average(obs_season.sum(axis=1), exposure.sum(axis=1))
            # A band with no weighted cells (dropped by a bootstrap resample) has no season to
            # estimate; it keeps the value it had, which no expected value then uses.
            with np.errstate(divide="ignore", invalid="ignore"):
                updated = (numerator + q * average[:, None] * denominator) / (
                    denominator * (1.0 + q)
                )
            season = np.where(denominator > 0, updated, season)
        if "day" in terms:
            band_mass = np.bincount(band, weights=weights * cell_level, minlength=nb)
            per_slot = (weeks * year_level[:, None]).sum(axis=0)
            unit = band_mass @ (season @ per_slot)
            day_total = obs_day / unit
        if "cell" in terms:
            # The parts are only defined up to scale: a band's season can grow while its cells
            # shrink. Moving each part's scale into the cell levels changes no expected value and
            # stops that drift from hiding convergence.
            if "season" in terms:
                band_scale = season.mean(axis=1)
                season = season / band_scale[:, None]
                cell_level = cell_level * band_scale[band]
            if "year" in terms:
                year_scale = year_level[train].mean()
                year_level = year_level / year_scale
                cell_level = cell_level * year_scale
            if "day" in terms:
                day_scale = day_total.sum() / DAYS_PER_TYPE.sum()
                day_total = day_total / day_scale
                cell_level = cell_level * day_scale
        after = (cell_level, year_level, season, day_total)
        for value in after:
            if not np.all(np.isfinite(value)):
                raise FloatingPointError(
                    f"fit produced a non-finite value at iteration {iteration}"
                )
        change = max(
            float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1e-300), initial=0.0))
            for a, b in zip(after, before, strict=True)
        )
        if change < tolerance:
            return Surface(
                cell_level=cell_level,
                year_level=np.where(train, year_level, np.nan),
                season=season,
                day_rate=day_total / DAYS_PER_TYPE,
                terms=frozenset(terms),
                config=config,
                iterations=iteration,
            )
    raise RuntimeError(f"fit did not converge in {max_iterations} iterations ({config.id})")


def combine(
    fungal: Surface, lichen: Surface, counts: OutingCounts, train_years: Sequence[int]
) -> Surface:
    """The effort surface (D103, D106): cell, year and day-type from the all-fungi fit, the season's
    shape from the lichen fit.

    Each band's lichen season is rescaled to the all-fungi season's total over the training weeks,
    so a band keeps its level and takes the lichen shape; then each training year's level is
    rescaled so the year's expected total equals the all-fungi fit's.
    """
    train = np.zeros(len(YEARS), dtype=bool)
    for year in train_years:
        train[YEARS.index(year)] = True
    all_weeks = (counts.weeks_per_year_slot * train[:, None]).sum(axis=0)
    fungal_band = fungal.season @ all_weeks
    lichen_band = lichen.season @ all_weeks
    if np.any(lichen_band <= 0):
        raise ValueError("a band's lichen season is zero over the training weeks")
    season = lichen.season * (fungal_band / lichen_band)[:, None]
    band_mass = np.bincount(counts.cell_band, weights=fungal.cell_level, minlength=counts.n_bands)
    fungal_year = counts.weeks_per_year_slot @ (band_mass @ fungal.season)
    combined_year = counts.weeks_per_year_slot @ (band_mass @ season)
    with np.errstate(invalid="ignore"):
        year_level = np.where(train, fungal.year_level * fungal_year / combined_year, np.nan)
    return Surface(
        cell_level=fungal.cell_level,
        year_level=year_level,
        season=season,
        day_rate=fungal.day_rate,
        terms=TERMS_FULL,
        config=fungal.config,
    )


# Scoring -----------------------------------------------------------------------------------------


def interpolated_year_level(year_level: np.ndarray, year: int) -> float:
    """A year's level from its fitted neighbours: the geometric mean of the years either side, or
    the nearest fitted year at an end."""
    i = YEARS.index(year)
    fitted = [j for j in range(len(YEARS)) if j != i and np.isfinite(year_level[j])]
    if not fitted:
        raise ValueError("no fitted year to interpolate from")
    below = [j for j in fitted if j < i]
    above = [j for j in fitted if j > i]
    if below and above:
        return float(math.sqrt(year_level[max(below)] * year_level[min(above)]))
    return float(year_level[max(below)] if below else year_level[min(above)])


def _held_out(
    counts: OutingCounts, year: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    selected = counts.entry_year == YEARS.index(year)
    return (
        counts.cell[selected],
        counts.week[selected],
        counts.day[selected],
        counts.count[selected],
    )


def _per_cell_deviance(
    counts: OutingCounts,
    ci: np.ndarray,
    y: np.ndarray,
    mu_entry: np.ndarray,
    mu_cell: np.ndarray,
) -> np.ndarray:
    """2 x (sum of y log(y / mu) over non-zero entries - y + mu) per cell. Zero entries add mu,
    which mu_cell carries in full."""
    positive = y > 0
    terms = np.zeros_like(y)
    terms[positive] = y[positive] * np.log(y[positive] / mu_entry[positive])
    y_cell = np.bincount(ci, weights=y, minlength=counts.n_cells)
    log_cell = np.bincount(ci, weights=terms, minlength=counts.n_cells)
    return 2.0 * (log_cell - y_cell + mu_cell)


def surface_deviance(
    surface: Surface, counts: OutingCounts, year: int, given_total: bool = True
) -> np.ndarray:
    """Poisson deviance per cell over every frame cell x week of the year x day-type, zeros
    included (D104). given_total: scaled so the year's expected total equals its observed total
    (the headline). Otherwise the year's level comes from interpolated_year_level (shown beside)."""
    ci, wk, dy, y = _held_out(counts, year)
    weeks = counts.weeks_per_year_slot[YEARS.index(year)]
    per_cell = (
        surface.cell_level
        * (surface.season @ weeks)[counts.cell_band]
        * (surface.day_rate * DAYS_PER_TYPE).sum()
    )
    if given_total:
        scale = y.sum() / per_cell.sum()
    else:
        scale = interpolated_year_level(surface.year_level, year)
    mu_entry = (
        scale
        * surface.cell_level[ci]
        * surface.season[counts.cell_band[ci], counts.week_slot[wk]]
        * surface.day_rate[dy]
        * DAYS_PER_TYPE[dy]
    )
    return _per_cell_deviance(counts, ci, y, mu_entry, scale * per_cell)


def constant_deviance(counts: OutingCounts, year: int, total: float | None = None) -> np.ndarray:
    """The constant-effort model (D104): the year's total spread evenly over every frame cell-day.
    total defaults to the year's observed total."""
    ci, _wk, dy, y = _held_out(counts, year)
    n_weeks = counts.weeks_per_year_slot[YEARS.index(year)].sum()
    if total is None:
        total = float(y.sum())
    per_cell_day = total / (counts.n_cells * n_weeks * 7.0)
    mu_entry = per_cell_day * DAYS_PER_TYPE[dy]
    mu_cell = np.full(counts.n_cells, total / counts.n_cells)
    return _per_cell_deviance(counts, ci, y, mu_entry, mu_cell)


def interpolated_total(counts: OutingCounts, year: int, train_years: Sequence[int]) -> float:
    totals = np.full(len(YEARS), np.nan)
    for train_year in train_years:
        totals[YEARS.index(train_year)] = counts.total(train_year)
    return interpolated_year_level(totals, year)


def dense_poisson_deviance(y: np.ndarray, mu: np.ndarray) -> float:
    """Plain Poisson deviance over a dense table; for tests of the per-cell form."""
    y = np.asarray(y, dtype=np.float64)
    mu = np.asarray(mu, dtype=np.float64)
    terms = np.where(y > 0, y * np.log(np.where(y > 0, y, 1.0) / mu), 0.0)
    return float(2.0 * (terms - y + mu).sum())


# Bootstrap and verdicts --------------------------------------------------------------------------


def cluster_weights(n_cells: int, resamples: int = BOOTSTRAP_RESAMPLES, seed: int = SEED):
    """Per resample, how many times each cell is drawn: n_cells draws with replacement."""
    rng = np.random.default_rng(seed)
    p = np.full(n_cells, 1.0 / n_cells)
    for _ in range(resamples):
        yield rng.multinomial(n_cells, p).astype(np.float64)


def percentile_interval(values: Sequence[float], level: float = 0.95) -> tuple[float, float]:
    tail = (1.0 - level) / 2.0 * 100.0
    low, high = np.percentile(np.asarray(values, dtype=np.float64), [tail, 100.0 - tail])
    return float(low), float(high)


def weekend_condition_1(ratio_interval: tuple[float, float]) -> bool:
    """D105 (i): the weekend-to-weekday interval lies wholly above 1."""
    return ratio_interval[0] > 1.0


def lower_deviance_condition(difference_interval: tuple[float, float]) -> bool:
    """D104 and D105 (ii): model minus comparison, whose interval lies wholly below zero."""
    return difference_interval[1] < 0.0


# Output (D107) -----------------------------------------------------------------------------------


class NoEffortValue(LookupError):
    """The surface has no value for this cell or week; never a made-up one (D107)."""


@dataclass(frozen=True)
class EffortSurface:
    """The stored surface, read back from data/t6/<track>/, and effort(cell, week) for T7 and T8."""

    cell_level: dict[Cell, float]
    cell_band: dict[Cell, int]
    year_level: dict[int, float]
    season: dict[tuple[int, int], float]
    weekly_day_total: float

    def effort(self, cell: Cell, week: IsoWeek) -> tuple[float, float]:
        """Expected outings in the cell-week, both day-types summed, and its natural log."""
        if cell not in self.cell_level:
            raise NoEffortValue(f"cell {cell.id} is not in the effort frame")
        if week not in _FRAME_WEEK_SET:
            raise NoEffortValue(f"week {week.id} is not one of the frame's 573 whole weeks")
        value = (
            self.cell_level[cell]
            * self.year_level[week.year]
            * self.season[(self.cell_band[cell], season_slot(week))]
            * self.weekly_day_total
        )
        return value, math.log(value)

    @classmethod
    def read(cls, folder: Path, which: str = "effort") -> EffortSurface:
        cell_level: dict[Cell, float] = {}
        cell_band: dict[Cell, int] = {}
        with (folder / "cell_level.csv").open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                cell = Cell(int(row["lat_tenths"]), int(row["lon_tenths"]))
                cell_level[cell] = float(row["all_fungi"])
                cell_band[cell] = int(row["band"])
        with (folder / "year_level.csv").open(encoding="utf-8", newline="") as handle:
            year_level = {int(r["year"]): float(r[which]) for r in csv.DictReader(handle)}
        with (folder / "season.csv").open(encoding="utf-8", newline="") as handle:
            season = {
                (int(r["band"]), int(r["slot"])): float(r[which]) for r in csv.DictReader(handle)
            }
        with (folder / "day_type.csv").open(encoding="utf-8", newline="") as handle:
            weekly = sum(
                float(r["all_fungi_per_day"]) * float(r["days"]) for r in csv.DictReader(handle)
            )
        return cls(cell_level, cell_band, year_level, season, weekly)


_FRAME_WEEK_SET = frozenset(frame_weeks())


def write_surface(
    folder: Path,
    counts: OutingCounts,
    fungal: Surface,
    lichen: Surface,
    effort: Surface,
    manifest: dict,
) -> dict[str, str]:
    """Writes the four tables and the manifest; returns file name -> sha256."""
    import hashlib

    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "cell_level.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("cell_id", "lat_tenths", "lon_tenths", "band", "all_fungi", "lichen"))
        for i, cell in enumerate(counts.cells):
            writer.writerow(
                (
                    cell.id,
                    cell.lat_tenths,
                    cell.lon_tenths,
                    counts.band_ids[counts.cell_band[i]],
                    repr(float(fungal.cell_level[i])),
                    repr(float(lichen.cell_level[i])),
                )
            )
    with (folder / "year_level.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("year", "all_fungi", "lichen", "effort"))
        for j, year in enumerate(YEARS):
            writer.writerow(
                (
                    year,
                    repr(float(fungal.year_level[j])),
                    repr(float(lichen.year_level[j])),
                    repr(float(effort.year_level[j])),
                )
            )
    with (folder / "season.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("band", "slot", "iso_week", "all_fungi", "lichen", "effort"))
        for b, band in enumerate(counts.band_ids):
            for s in range(N_SLOTS):
                writer.writerow(
                    (
                        band,
                        s,
                        s + 1,
                        repr(float(fungal.season[b, s])),
                        repr(float(lichen.season[b, s])),
                        repr(float(effort.season[b, s])),
                    )
                )
    with (folder / "day_type.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("day_type", "days", "all_fungi_per_day", "lichen_per_day"))
        for d, name in ((WEEKEND, "weekend"), (WEEKDAY, "weekday")):
            writer.writerow(
                (
                    name,
                    int(DAYS_PER_TYPE[d]),
                    repr(float(fungal.day_rate[d])),
                    repr(float(lichen.day_rate[d])),
                )
            )
    (folder / "effort_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    digests = {}
    for name in (
        "cell_level.csv",
        "year_level.csv",
        "season.csv",
        "day_type.csv",
        "effort_manifest.json",
    ):
        digests[name] = hashlib.sha256((folder / name).read_bytes()).hexdigest()
    return digests

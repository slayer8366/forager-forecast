"""The jump check (plan section 2; D133 (2)): six counts J1 to J6 and the reading rule.

The counts are taken from the survivors of T1's steps in T1's box, from D26's zip, and read no
weather. This module holds only the tallies and the rule; scripts/t8_count.py does the reading.

The rule, fixed in the plan before counting (quoted):
- "Reporting-led" if over half the rise comes from new observers with 10 or more positives each,
  or from one dataset other than the main one, or falls in at most 3 weeks and 5 cells.
- "Surge-consistent" if none of those hold, distinct observers at least doubled, and at least 4 of
  the 6 other mycorrhizal genera rose 1.5 times or more.
- "Undetermined" otherwise.

The plan does not settle which years make "the rise", who is "new", which dataset is "the main
one", how "at most 3 weeks and 5 cells" is measured, or which six genera J5 counts. Those are the
readings J-* in design.PENDING; `JumpReading` carries them, and PROPOSED_READING is the proposal,
not a ruling. With no rise at all, the rule has nothing to read and returns "undetermined".
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

REPORTING_LED = "reporting-led"
SURGE_CONSISTENT = "surge-consistent"
UNDETERMINED = "undetermined"

# The rule's numbers (plan section 2), fixed.
SHARE_OVER = 0.5
HEAVY_POSITIVES = 10
MAX_WEEKS = 3
MAX_CELLS = 5
OBSERVER_FACTOR = 2.0
GENUS_FACTOR = 1.5
GENERA_NEEDED = 4

CONCENTRATION_BOTH = "both marginals"
CONCENTRATION_BLOCK = "block"
CONCENTRATION_EITHER = "either marginal"

NEW_SINCE_BASELINE = "no record in the baseline year"
NEW_SINCE_ALL_PRIOR = "no record in any earlier year"


@dataclass(frozen=True)
class JumpRecord:
    """One record surviving T1's steps in T1's box, with the fields J1 to J6 read."""

    year: int  # calendar year of the event date, as T1's records summary counts them
    observer: str  # effort.observer_of: recordedBy as written, or one anonymous per dataset
    dataset: str
    iso_week: int  # 1 to 53, the ISO week number of the event date
    cell: str  # the 0.1 degree cell id
    unit: str  # the T1 unit id, cell@Monday
    genus_key: int | None
    has_species: bool
    unit_year: int | None = None  # the ISO year of its T1 unit; None if it is in no T1 unit


@dataclass(frozen=True)
class JumpReading:
    baseline_year: int
    rise_years: tuple[int, ...]  # a condition must hold in every one of them
    new_observer: str
    concentration: str
    genera: Mapping[str, int]  # J5: genus name -> GBIF genus key

    def __post_init__(self) -> None:
        if not self.rise_years or self.baseline_year in self.rise_years:
            raise ValueError("rise years must be given and differ from the baseline")
        if self.new_observer not in (NEW_SINCE_BASELINE, NEW_SINCE_ALL_PRIOR):
            raise ValueError(f"unknown new-observer reading {self.new_observer!r}")
        if self.concentration not in (
            CONCENTRATION_BOTH,
            CONCENTRATION_BLOCK,
            CONCENTRATION_EITHER,
        ):
            raise ValueError(f"unknown concentration reading {self.concentration!r}")
        if len(self.genera) != 6:
            raise ValueError("J5 counts six genera")


# GBIF backbone genus keys for the proposed J5 list are not resolved yet: the count script resolves
# them with GBIF's species-match API (kingdom Fungi, rank GENUS) and records each answer, as
# t1_design records Cantharellus's key. The names below are the proposal (design.PENDING J-genera).
PROPOSED_GENERA: tuple[str, ...] = (
    "Boletus",
    "Hydnum",
    "Russula",
    "Lactarius",
    "Suillus",
    "Amanita",
)


def proposed_reading(genus_keys: Mapping[str, int]) -> JumpReading:
    return JumpReading(
        baseline_year=2023,
        rise_years=(2024,),
        new_observer=NEW_SINCE_BASELINE,
        concentration=CONCENTRATION_BOTH,
        genera={name: genus_keys[name] for name in PROPOSED_GENERA},
    )


@dataclass
class RiseTally:
    """J1 to J4 for one rise year against the baseline."""

    rise_year: int
    baseline_records: int
    rise_records: int
    baseline_observers: int  # J1
    rise_observers: int  # J1
    new_heavy_records: int  # J2: rise-year records by new observers with >= 10 each
    new_heavy_observers: int
    main_dataset: str  # J3
    rise_by_dataset: dict[str, int] = field(default_factory=dict)  # J3
    rise_by_week: dict[int, int] = field(default_factory=dict)  # J4
    rise_by_cell: dict[str, int] = field(default_factory=dict)  # J4
    block_rise: int = 0  # J4: rise inside the top weeks x top cells
    genus_ratio: dict[str, float] = field(default_factory=dict)  # J5

    @property
    def rise(self) -> int:
        return self.rise_records - self.baseline_records

    def _share(self, part: float) -> float:
        return part / self.rise if self.rise > 0 else float("nan")

    @property
    def new_heavy_share(self) -> float:
        return self._share(self.new_heavy_records)

    @property
    def top_other_dataset(self) -> tuple[str, float]:
        others = {d: r for d, r in self.rise_by_dataset.items() if d != self.main_dataset}
        if not others:
            return "", float("nan")
        best = max(sorted(others), key=lambda d: others[d])
        return best, self._share(others[best])

    @property
    def top_weeks_share(self) -> float:
        return self._share(_top_sum(self.rise_by_week.values(), MAX_WEEKS))

    @property
    def top_cells_share(self) -> float:
        return self._share(_top_sum(self.rise_by_cell.values(), MAX_CELLS))

    @property
    def block_share(self) -> float:
        return self._share(self.block_rise)


@dataclass
class JumpTallies:
    """J1 to J6 by year, and J1 to J5 per rise year as the reading needs them."""

    reading: JumpReading
    cantharellus_by_year: dict[int, int]
    observers_by_year: dict[int, int]  # J1
    records_by_dataset_year: dict[str, dict[int, int]]  # J3
    genus_rate_by_year: dict[str, dict[int, float]]  # J5
    species_share_by_year: dict[int, float]  # J6
    per_rise_year: dict[int, RiseTally]


def _top_sum(values: Iterable[int], k: int) -> int:
    return sum(sorted(values, reverse=True)[:k])


def tally(
    records: Iterable[JumpRecord],
    units_by_year: Mapping[int, int],
    cantharellus_key: int,
    reading: JumpReading,
) -> JumpTallies:
    """The six counts. units_by_year is T1's unit count per year, the J5 denominator."""
    canth: list[JumpRecord] = []
    genus_units: dict[str, dict[int, set[str]]] = {g: defaultdict(set) for g in reading.genera}
    key_to_genus = {k: g for g, k in reading.genera.items()}
    if cantharellus_key in key_to_genus:
        raise ValueError("Cantharellus cannot be one of J5's other genera")
    for r in records:
        if r.genus_key == cantharellus_key:
            canth.append(r)
        elif r.genus_key in key_to_genus:
            genus_units[key_to_genus[r.genus_key]][r.year].add(r.unit)
    by_year: Counter[int] = Counter(r.year for r in canth)
    observers: dict[int, set[str]] = defaultdict(set)
    per_observer: dict[int, Counter[str]] = defaultdict(Counter)
    by_dataset: dict[str, Counter[int]] = defaultdict(Counter)
    by_week: dict[int, Counter[int]] = defaultdict(Counter)
    by_cell: dict[int, Counter[str]] = defaultdict(Counter)
    by_week_cell: dict[int, Counter[tuple[int, str]]] = defaultdict(Counter)
    species: Counter[int] = Counter()
    for r in canth:
        observers[r.year].add(r.observer)
        per_observer[r.year][r.observer] += 1
        by_dataset[r.dataset][r.year] += 1
        by_week[r.year][r.iso_week] += 1
        by_cell[r.year][r.cell] += 1
        by_week_cell[r.year][(r.iso_week, r.cell)] += 1
        species[r.year] += r.has_species
    years = sorted(set(units_by_year) | set(by_year))
    rate = {
        g: {
            y: (len(genus_units[g].get(y, ())) / units_by_year[y]) if units_by_year.get(y) else 0.0
            for y in years
        }
        for g in reading.genera
    }
    b = reading.baseline_year
    per_rise: dict[int, RiseTally] = {}
    for ry in reading.rise_years:
        if reading.new_observer == NEW_SINCE_BASELINE:
            seen = observers[b]
        else:
            seen = set().union(*(observers[y] for y in years if y < ry))
        heavy = {
            o: n for o, n in per_observer[ry].items() if o not in seen and n >= HEAVY_POSITIVES
        }
        baseline_by_dataset = {d: c[b] for d, c in by_dataset.items()}
        main = max(sorted(baseline_by_dataset), key=lambda d: baseline_by_dataset[d], default="")
        weeks = set(by_week[b]) | set(by_week[ry])
        cells = set(by_cell[b]) | set(by_cell[ry])
        rise_week = {w: by_week[ry][w] - by_week[b][w] for w in weeks}
        rise_cell = {c: by_cell[ry][c] - by_cell[b][c] for c in cells}
        top_w = set(sorted(sorted(rise_week), key=lambda w: -rise_week[w])[:MAX_WEEKS])
        top_c = set(sorted(sorted(rise_cell), key=lambda c: -rise_cell[c])[:MAX_CELLS])
        block = sum(
            by_week_cell[ry][(w, c)] - by_week_cell[b][(w, c)] for w in top_w for c in top_c
        )
        ratio = {}
        for g in reading.genera:
            before, after = rate[g].get(b, 0.0), rate[g].get(ry, 0.0)
            ratio[g] = (after / before) if before > 0 else (float("inf") if after > 0 else 0.0)
        per_rise[ry] = RiseTally(
            rise_year=ry,
            baseline_records=by_year[b],
            rise_records=by_year[ry],
            baseline_observers=len(observers[b]),
            rise_observers=len(observers[ry]),
            new_heavy_records=sum(heavy.values()),
            new_heavy_observers=len(heavy),
            main_dataset=main,
            rise_by_dataset={d: c[ry] - c[b] for d, c in sorted(by_dataset.items())},
            rise_by_week=dict(sorted(rise_week.items())),
            rise_by_cell=dict(sorted(rise_cell.items())),
            block_rise=block,
            genus_ratio=ratio,
        )
    return JumpTallies(
        reading=reading,
        cantharellus_by_year={y: by_year[y] for y in years},
        observers_by_year={y: len(observers[y]) for y in years},
        records_by_dataset_year={d: dict(sorted(c.items())) for d, c in sorted(by_dataset.items())},
        genus_rate_by_year=rate,
        species_share_by_year={y: (species[y] / by_year[y]) if by_year[y] else float("nan")
                               for y in years},
        per_rise_year=per_rise,
    )  # fmt: skip


@dataclass(frozen=True)
class JumpVerdict:
    label: str
    reasons: tuple[str, ...]


def _reporting_conditions(t: RiseTally, concentration: str) -> dict[str, str]:
    """The reporting-led conditions that hold for one rise year, by kind."""
    held: dict[str, str] = {}
    if t.new_heavy_share > SHARE_OVER:
        held["new observers"] = (
            f"{t.rise_year}: new observers with {HEAVY_POSITIVES}+ records carry "
            f"{t.new_heavy_share:.3f} of the rise"
        )
    name, share = t.top_other_dataset
    if share > SHARE_OVER:
        held["dataset"] = f"{t.rise_year}: dataset {name} (not the main one) carries {share:.3f}"
    weeks, cells = t.top_weeks_share > SHARE_OVER, t.top_cells_share > SHARE_OVER
    concentrated = {
        CONCENTRATION_BOTH: weeks and cells,
        CONCENTRATION_EITHER: weeks or cells,
        CONCENTRATION_BLOCK: t.block_share > SHARE_OVER,
    }[concentration]
    if concentrated:
        held["concentration"] = (
            f"{t.rise_year}: concentrated ({concentration}): top {MAX_WEEKS} weeks "
            f"{t.top_weeks_share:.3f}, top {MAX_CELLS} cells {t.top_cells_share:.3f}, block "
            f"{t.block_share:.3f}"
        )
    return held


def read_jump(tallies: JumpTallies) -> JumpVerdict:
    """The plan's rule, applied to the tallies under their reading. A condition must hold in every
    rise year the reading names."""
    reading = tallies.reading
    rises = [tallies.per_rise_year[y] for y in reading.rise_years]
    if any(t.rise <= 0 for t in rises):
        return JumpVerdict(
            UNDETERMINED,
            tuple(f"{t.rise_year}: no rise over {reading.baseline_year} ({t.rise})" for t in rises),
        )
    held = [_reporting_conditions(t, reading.concentration) for t in rises]
    # A reporting condition holds only if the same kind of condition holds in every rise year.
    common = set.intersection(*(set(h) for h in held))
    if common:
        return JumpVerdict(REPORTING_LED, tuple(h[kind] for kind in sorted(common) for h in held))
    doubled = all(t.rise_observers >= OBSERVER_FACTOR * t.baseline_observers for t in rises)
    rose = [sum(r >= GENUS_FACTOR for r in t.genus_ratio.values()) for t in rises]
    genera_ok = all(n >= GENERA_NEEDED for n in rose)
    reasons = (
        f"distinct observers {[(t.baseline_observers, t.rise_observers) for t in rises]}, "
        f"doubled: {doubled}",
        f"genera rising {GENUS_FACTOR}x or more: {rose} of 6, enough: {genera_ok}",
    )
    if doubled and genera_ok:
        return JumpVerdict(SURGE_CONSISTENT, reasons)
    return JumpVerdict(UNDETERMINED, reasons)

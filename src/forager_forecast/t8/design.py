"""T8's fixed choices, transcribed from the plan and D133, and the readings still open.

Sources: docs/dispatch/2026-10-19-t8-plan.md (sections 1 to 9) and D133 (planning/DECISIONS.md).
These are not parameters: the plan fixes them before any count or fit, so they live in one place.

Where the plan or D133 leaves a choice open that changes a result, the code is built on a proposed
reading and the reading is listed in PENDING below. The count and fit scripts call
`require_ruled` for the readings their step depends on and refuse to run until each one is ruled
by the owner and recorded in RULED with its decision row. Nothing here may be ruled by a coder.
"""

from dataclasses import dataclass

# D31, plan section 1: the seed for every random draw (bootstrap, swaps, tuning grid).
SEED = 20260918

# Plan section 1: years and the thin-fold rule (D33 (2)).
FIRST_YEAR = 2015
LAST_YEAR = 2025
YEARS: tuple[int, ...] = tuple(range(FIRST_YEAR, LAST_YEAR + 1))
MIN_POSITIVES_INFORMATIVE = 30

# Plan section 3: the 2015-2023 line reported beside, with no verdict.
BESIDE_LINE_YEARS: tuple[int, ...] = tuple(range(2015, 2024))

# Plan section 3 and T1 report :289: the headline unit count. The run refuses any other.
T1_HEADLINE_UNITS = 52718

# Plan section 3: T1's three step lists (scripts/pnw_t1_records.py), the T1 calendar file each one's
# units are keyed by (in the pilot data folder's fits/), and the unit count each must hold. The
# sensitivity runs use their own T1 units, with no verdict: D33 (3) (T1 report :400-401) and
# D33 (4) (:364-365).
T1_LISTS: dict[str, tuple[str, int]] = {
    "t1_1000m": ("primary_t1_1000m_calendar", T1_HEADLINE_UNITS),
    "t1_5000m": ("primary_t1_5000m_calendar", 56927),
    "t1_1000m_cc": ("primary_t1_1000m_cc_calendar", 9640),
}
HEADLINE_LIST = "t1_1000m"

# D103: lichens, GBIF class Lecanoromycetes (the same key effort.BENCHMARK_CLASS_KEY holds).
LICHEN_CLASS_KEY = 180


@dataclass(frozen=True)
class Measure:
    """One weather measure (plan section 5): a reduction of one variable over a window of days."""

    name: str
    variable: str  # "precipitation", "soil_moisture" or "soil_temperature" (t1_pnw.npz names)
    reduction: str  # "sum" or "mean"
    days: int


# Plan section 5 and D133 (4): fixed now, no search.
MEASURES: tuple[Measure, ...] = (
    Measure("W1", "precipitation", "sum", 14),
    Measure("W2", "precipitation", "sum", 56),
    Measure("W3", "soil_moisture", "mean", 7),
    Measure("W4", "soil_temperature", "mean", 14),
)

# Plan section 5: the window ends the day before the week (T1's rule): it covers Monday - days
# through Monday - 1. The forecast timing ends 7 days earlier: Monday - 7 - days through Monday - 8.
# The value is the gap in days between the window's last day and the scored Monday.
HEADLINE_END_GAP = 1
FORECAST_END_GAP = 8

# Plan section 6 and D133 (6): each measure is a smooth curve of 3 degrees of freedom.
MEASURE_DF = 3

# Plan section 7 and D133 (5): the bar.
BOOTSTRAP_RESAMPLES = 1000
N_SWAPS = 199
# "The gain has to beat all but 9 of the swaps": p = (1 + swaps at or above) / (1 + 199) <= 0.05.
MAX_SWAPS_AT_OR_ABOVE = 9
C3_ALPHA = 0.05


@dataclass(frozen=True)
class Pending:
    """A reading the plan and D133 leave open, built on a proposal, not in force until ruled."""

    id: str
    question: str
    proposed: str
    alternatives: tuple[str, ...]
    step: str  # "count" or "fit"


PENDING: dict[str, Pending] = {
    p.id: p
    for p in (
        # The jump check (plan section 2). Each changes which label the rule returns.
        Pending(
            "J-rise",
            "Which years define 'the rise' in J2 to J5 and 'at least doubled' in J1?",
            "2023 to 2024 only",
            (
                "2023 to 2025 only",
                "2023 to the mean of 2024 and 2025",
                "each of 2024 and 2025 separately, a condition holding if it holds in both",
            ),
            "count",
        ),  # fmt: skip
        Pending(
            "J-unit",
            "What is counted: records or positive cell-weeks?",
            "Cantharellus records surviving T1's steps in T1's box",
            ("positive cell-weeks (T1 units)",),
            "count",
        ),
        Pending(
            "J-new-observer",
            "Who is a 'new observer' in J2?",
            "an observer with no Cantharellus record in the baseline year (2023)",
            (
                "no Cantharellus record in any year before the rise year",
                "no fungal record of any kind before the rise year",
            ),
            "count",
        ),  # fmt: skip
        Pending(
            "J-main-dataset",
            "Which is 'the main' dataset in J3?",
            "the dataset with the most Cantharellus records in the baseline year",
            ("the dataset with the most Cantharellus records over 2015 to 2025",),
            "count",
        ),
        Pending(
            "J-concentration",
            "How is 'falls in at most 3 weeks and 5 cells' read in J4?",
            "the 3 ISO weeks with the largest rise carry over half the rise, and the 5 cells with "
            "the largest rise carry over half the rise (both)",
            (
                "the rise inside the block of the top 3 weeks by the top 5 cells is over half",
                "either marginal concentration on its own",
            ),
            "count",
        ),  # fmt: skip
        Pending(
            "J-genera",
            "Which are the 'six other' mycorrhizal genera of J5, and how is their rate taken?",
            "Boletus, Hydnum, Russula, Lactarius, Suillus, Amanita (Ash's paused draft, d6f916a); "
            "rate = cell-weeks with the genus / T1 units of the year",
            ("another list the owner names", "rate = genus records / all fungal records"),
            "count",
        ),
        Pending(
            "J-species",
            "What counts as 'named to species' in J6?",
            "the record carries a GBIF speciesKey",
            ("taxonRank is SPECIES or below",),
            "count",
        ),
        Pending(
            "L-outcome",
            "What is the lichen outcome of the turnout guard (C4)?",
            "a T1 unit is lichen-positive if at least one record of class 180 survives T1's steps "
            "in it; lichen outings are distinct (observer, day) among those records",
            ("a count of lichen records", "lichen records under T6's steps instead of T1's"),
            "count",
        ),
        # The models and the bar (plan sections 4 to 7).
        Pending(
            "M-calendar-place",
            "The flexibility of the day-of-year cycle and the place smooth in the main model.",
            "day of year as 3 Fourier harmonics (6 df); latitude and longitude each a natural "
            "spline of 3 df, added (6 df); unpenalised",
            (
                "2 or 4 harmonics",
                "a tensor-product smooth of latitude and longitude",
                "penalised smooths with the penalty chosen by inner leave-one-year-out",
            ),
            "fit",
        ),  # fmt: skip
        Pending(
            "M-effort-form",
            "How the log of T6's expected outings enters both models.",
            "one linear term with a fitted coefficient",
            ("an offset (coefficient fixed at 1)", "a natural spline of 3 df"),
            "fit",
        ),
        Pending(
            "M-effort-training",
            "Which effort value the training cell-weeks of a fold get.",
            "the fold's surface (fitted without the held-out year) at each training year's own "
            "fitted level; only the held-out year's level is interpolated",
            (
                "every unit's effort from the surface fitted without its own year, interpolated, "
                "used in every fold (leaks the held-out year's outings into training effort)",
            ),
            "fit",
        ),  # fmt: skip
        Pending(
            "M-effort-config",
            "T6's pull and smoothing in each fold's refit.",
            "the configuration T6's own evaluation chose for that held-out year "
            "(docs/audits/2026-10-06-t6-fit/{all,cc}_results.json, chosen_per_fold)",
            ("the stored surface's configuration in every fold",),
            "fit",
        ),
        Pending(
            "M-swap",
            "How a whole-year weather swap is drawn and aligned.",
            "a random derangement of the 11 years (no year keeps its own weather), redrawn if it "
            "repeats an earlier swap; a unit in ISO year Y, week k reads year pi(Y)'s weather for "
            "ISO week k (week 53 reads week 52 where pi(Y) has none); the model is refitted "
            "under leave-one-year-out for every swap",
            ("a random permutation (fixed points allowed)", "alignment by calendar day"),
            "fit",
        ),
        Pending(
            "M-challenger-swaps",
            "C3 for the challenger: 199 swaps each re-tuned is about 199 times T1's tree run.",
            "199 swaps with each fold's configuration fixed at the one chosen on true weather",
            ("199 swaps each re-tuned (days of compute)", "challenger's C3 reported only"),
            "fit",
        ),
        Pending(
            "M-forecast-bar",
            "What 'the forecast timing must pass' runs (D133 (4)).",
            "C1 to C4 at the forecast timing, with its own 199 swaps; reported beside, no verdict "
            "on T8, recorded as the gate for showing anything",
            ("C1, C2 and C4 only, no swaps",),
            "fit",
        ),
        Pending(
            "M-measure-alone",
            "What 'each measure is also checked alone' runs (plan section 5).",
            "the no-weather model plus that one measure, with its own 199 swaps; reported only",
            ("the full model with only that measure swapped",),
            "fit",
        ),
        Pending(
            "M-ecoregion",
            "Leave-one-ecoregion-out (reported, no verdict): blocks, minimum, effort.",
            "each cell's level III code by cell centre (a centre in no polygon is its own block "
            "'none'); a block with under 30 positives is uninformative and kept in the pool; "
            "trained on the other blocks over all years; effort from T6's surface fitted on all "
            "years with its stored configuration; main against no-weather only",
            ("another minimum", "leave one ecoregion and one year out together"),
            "fit",
        ),
        Pending(
            "M-sensitivity",
            "What the D33 (3) and D33 (4) sensitivity runs compute (plan section 3, 'no verdict').",
            "the main model's C1 to C4 on their own T1 units at the headline timing, with their "
            "own 199 swaps, all labelled no verdict",
            ("C1, C2 and C4 only, no swaps", "C1 only, against their own stored calendar"),
            "fit",
        ),
        Pending(
            "M-sensitivity-effort",
            "Which of T6's two tracks gives the sensitivity runs their effort.",
            "the 'all' track for D33 (3) (5,000 m); the 'cc' track (counts cc_*.npz, folds from "
            "cc_results.json) for D33 (4), the commercial-safe track (D29)",
            ("the 'all' track for both",),
            "fit",
        ),
    )
}

# Readings the owner has ruled, as reading id -> decision row. J-rise was ruled as one of its
# alternatives (both comparisons, each separately), not the proposal; jump.ruled_reading builds it.
RULED: dict[str, str] = {
    "J-rise": "D134",
    "J-unit": "D134",
    "J-new-observer": "D134",
    "J-main-dataset": "D134",
    "J-concentration": "D134",
    "J-genera": "D134",
    "J-species": "D134",
    "L-outcome": "D134",
}


class NotRuled(RuntimeError):
    """A step was asked to run while a reading it depends on is still open."""


def open_readings(step: str) -> list[Pending]:
    return [p for p in PENDING.values() if p.step == step and p.id not in RULED]


def require_ruled(step: str) -> None:
    """Refuses while any reading the step depends on has no ruling in RULED."""
    missing = open_readings(step)
    if missing:
        raise NotRuled(
            f"{len(missing)} reading(s) for the {step} are not ruled: "
            + ", ".join(p.id for p in missing)
        )

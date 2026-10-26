"""T8b's fixed choices, transcribed from the plan and D159, and the readings still open.

Sources: docs/dispatch/2026-10-25-t8b-plan.md (sections 2 to 9) and D159 (planning/DECISIONS.md:8).
Everything D159 leaves as it was in T8 is imported from t8.design, not copied, so the two tests
cannot drift apart: the seed, the years, the units, the bar's numbers and the timings.

Where the plan or D159 leaves a choice open that changes a result, the code is built on a proposed
reading and the reading is listed in PENDING below, as T8's design.py did. `require_ruled` refuses a
step until every reading it depends on has a decision row in RULED. Nothing here may be ruled by a
coder: RULED is empty.
"""

from datetime import date
from fractions import Fraction

from forager_forecast.t8.design import (  # noqa: F401  (re-exported: D159 (1), (6))
    BOOTSTRAP_RESAMPLES,
    C3_ALPHA,
    FORECAST_END_GAP,
    HEADLINE_END_GAP,
    HEADLINE_LIST,
    MAX_SWAPS_AT_OR_ABOVE,
    MEASURE_DF,
    MIN_POSITIVES_INFORMATIVE,
    N_SWAPS,
    SEED,
    T1_HEADLINE_UNITS,
    YEARS,
    Measure,
    NotRuled,
    Pending,
)

# D159 (2), plan section 5: five measures, fixed now, no search. Windows end the day before the
# week (HEADLINE_END_GAP = 1, T8's rule). Variable names are this package's daily grids:
#   rain: Daymet V4 `prcp` (mm per day), one series per 0.1 degree cell (daymet.py);
#   soil_moisture_l2: ERA5-Land `volumetric_soil_water_layer_2` (m3 m-3), 7 to 28 cm;
#   soil_temperature_l2: ERA5-Land `soil_temperature_level_2` (deg C), 7 to 28 cm;
#   dewpoint_depression: ERA5-Land daily mean `2m_temperature` minus daily mean
#     `2m_dewpoint_temperature` (K, which is deg C for a difference).
MEASURES: tuple[Measure, ...] = (
    Measure("M1", "rain", "sum", 14),
    Measure("M2", "rain", "sum", 56),
    Measure("M3", "soil_moisture_l2", "mean", 14),
    Measure("M4", "soil_temperature_l2", "mean", 14),
    Measure("M5", "dewpoint_depression", "mean", 7),
)
RAIN = "rain"
LAND_VARIABLES = ("soil_moisture_l2", "soil_temperature_l2", "dewpoint_depression")

# ERA5-Land variable names as the store's NetCDF files carry them (short name -> long name). The
# land point test (-822) asks for a value in all four source variables.
ERA5_LAND_SHORT = {
    "swvl2": "volumetric_soil_water_layer_2",
    "stl2": "soil_temperature_level_2",
    "t2m": "2m_temperature",
    "d2m": "2m_dewpoint_temperature",
}

# D159 (5), plan section 7: the unseen season. ISO weeks 27 to 52 of 2026, scored once from a
# GBIF download taken after 2027-02-15.
C5_YEAR = 2026
C5_WEEKS: tuple[int, ...] = tuple(range(27, 53))
C5_DOWNLOAD_AFTER = date(2027, 2, 15)

# Plan section 3: the jump check's numbers.
JUMP_BASELINE_YEAR = 2023
JUMP_RISE_YEAR = 2024
JUMP_SHARE_MOVE = Fraction(1, 3)  # exact, so a share moving by exactly a third does not count
PARTLY_REPORTING = "partly reporting"
UNDETERMINED = "undetermined"


PENDING: dict[str, Pending] = {
    p.id: p
    for p in (
        # The measures (plan section 5, D159 (2)).
        Pending(
            "B-daymet-cell",
            "How a 0.1 degree cell's rain is taken from Daymet's 1 km pixels.",
            "the mean, day by day, of every Daymet pixel whose centre (the file's own lat and lon) "
            "falls in the cell by D46's nearest-centre rule (cells.cell_for), counting only pixels "
            "that carry a value on every day pulled",
            (
                "the one pixel containing the cell centre",
                "an area-weighted mean over the cell's exact footprint",
            ),
            "fit",
        ),  # fmt: skip
        Pending(
            "B-daymet-no-land",
            "A cell with no Daymet pixel carrying values (water on Daymet's land mask).",
            "RECORD -822's rule on the 0.1 degree cell grid: the nearest of the 8 neighbouring "
            "cells that has Daymet pixels, by great-circle distance between cell centres, ties "
            "north then east (coastal.land_point); a cell with none is refused, never filled",
            (
                "the nearest Daymet pixel to the cell centre, at any distance",
                "ERA5 0.25 degree rain (T8's source) for those cells only",
            ),
            "fit",
        ),  # fmt: skip
        Pending(
            "B-daymet-leap",
            "Daymet drops 31 December in leap years (V4 R1 user guide, 'The Daymet Calendar'). "
            "A window touching 2016-12-31, 2020-12-31 or 2024-12-31 has no value for that day, "
            "and T8's rule refuses a window touching a missing day; the units cannot change "
            "(D159 (1)).",
            "count Daymet days: a w-day window is the w Daymet days ending the day before the "
            "week, so it reaches one calendar day further back when it spans a dropped "
            "31 December; every total is a sum of w delivered values, none filled",
            (
                "the sum over the w - 1 delivered days, scaled by w / (w - 1)",
                "31 December given 30 December's value (a fill, which T8 never does)",
                "the sum over the w - 1 delivered days, unscaled",
            ),
            "fit",
        ),  # fmt: skip
        Pending(
            "B-daymet-day",
            "Which calendar day a Daymet daily value belongs to. Daymet's day follows its station "
            "inputs' local observing day; ERA5-Land's are UTC days (D52).",
            "Daymet's day d is calendar day d, with no shift, beside ERA5-Land's UTC day d",
            ("shift Daymet one day earlier, where stations report the morning after",),
            "fit",
        ),
        Pending(
            "B-pull-start",
            "The first day pulled. The plan's '2014-11' covers the headline windows, but the "
            "week-late timing's 56-day window for a unit on Monday 2014-12-29 (ISO 2015-W01) "
            "starts on 2014-10-27.",
            "pull Daymet and ERA5-Land from 2014-10-01, so both timings have every window",
            ("pull from 2014-11-01 and refuse any week-late window that reaches before it",),
            "pull",
        ),  # fmt: skip
        # The models (plan section 6, D159 (4)).
        Pending(
            "B-clamp-range",
            "Which rows set a fold's clamp range under a weather swap.",
            "the training rows of the weather matrix the model is fitted on (under a swap, the "
            "swapped weather), so the clamp is part of the model's form; for trees the clamp "
            "changes no prediction either way (see clamp.py)",
            ("the training rows of the true weather, in every swap",),
            "fit",
        ),  # fmt: skip
        Pending(
            "B-forecast-bar",
            "What the week-late timing runs (plan section 7, reported beside).",
            "as D136 ruled for T8 (M-forecast-bar): C1 to C4 at the forecast timing (gap 8), with "
            "its own 199 swaps at the tuning chosen on true weather at that timing, no verdict",
            ("C1, C2 and C4 only, no swaps",),
            "fit",
        ),  # fmt: skip
        Pending(
            "B-measure-shuffle",
            "What 'each measure's own shuffle' runs (plan section 7, reported beside).",
            "the main tree model with only that measure's column swapped (the other four true), "
            "the same 199 swaps, each fold's tuning fixed at the true-weather choice; no verdict",
            ("T8's M-measure-alone: the no-weather model plus that measure, with its own swaps",),
            "fit",
        ),  # fmt: skip
        Pending(
            "B-ecoregion",
            "Leave-one-ecoregion-out with the tree model (plan section 6, no verdict). Not built "
            "in step 1.",
            "as D136's M-ecoregion, with the tree model tuned by inner leave-one-block-out on the "
            "training blocks",
            ("the tuning chosen on true weather for the pooled years", "the additive model only"),
            "fit",
        ),  # fmt: skip
        # C5 (plan section 7, D159 (5)).
        Pending(
            "C5-beats",
            "What 'beats T1's calendar' means for C5 (C1 says 'interval wholly above zero'; C5 "
            "says 'Brier skill above zero, with its interval reported').",
            "the pooled Brier skill over the 2026 units is above zero; its 1,000-resample cell "
            "interval (seed 20260918) is reported, not required",
            ("the interval wholly above zero, as C1",),
            "c5",
        ),  # fmt: skip
        Pending(
            "C5-frozen-fit",
            "What 'the model, frozen after C1 to C4' is fitted on.",
            "the main tree model refitted once on all 2015 to 2025 units, its configuration chosen "
            "by T1's inner leave-one-year-out over those eleven years, clamp ranges from those "
            "eleven years; saved with its checksum before any 2026 record is read",
            ("one of the eleven fold models (which one would need a rule)",),
            "c5",
        ),  # fmt: skip
        Pending(
            "C5-calendar",
            "Which calendar C5 is scored against: T1's stored calendar predictions end at 2025.",
            "T1's calendar form (LightGBM on day-of-year sine and cosine, latitude, longitude) "
            "refitted on all 2015 to 2025 units the same way, frozen beside the main model",
            ("the calendar model the 2026 pilot used, if one was fitted on all eleven years",),
            "c5",
        ),  # fmt: skip
        Pending(
            "C5-effort",
            "2026's effort value. T6's frame stops at 2025 (effort_term.surface_values refuses a "
            "week outside it), so the code has no path for a 2026 unit's effort.",
            "the surface fitted on all eleven years, at 2025's fitted level (as a held-out 2025 "
            "takes 2024's), with the frame extended to 2026's weeks by season slot",
            ("refit T6's surface with 2026's fungal outings from the C5 download, after freezing",),
            "c5",
        ),  # fmt: skip
        Pending(
            "C5-units",
            "Which 2026 cell-weeks are scored.",
            "T1's steps (scripts/pnw_t1_records.py) on the C5 download with the year changed to "
            "2026, keeping ISO 2026 weeks 27 to 52 in cells with weather, as T1 did",
            ("only cells among T1's 2015 to 2025 cells",),
            "c5",
        ),  # fmt: skip
        Pending(
            "C5-after",
            "What 'a GBIF download taken after 2027-02-15' checks.",
            "the download's own `created` time, read from GBIF's download record, is on or after "
            "2027-02-16T00:00Z",
            ("the time the zip was fetched",),
            "c5",
        ),
        # The jump check (plan section 3).
        Pending(
            "R-share-move",
            "What 'moved by more than a third' means for a share.",
            "relative: |share_2024 / share_2023 - 1| > 1/3",
            (
                "absolute: |share_2024 - share_2023| > 1/3 (33 percentage points)",
                "on the odds of the share",
            ),
            "count",
        ),  # fmt: skip
        Pending(
            "R-years",
            "Which years the jump check compares.",
            "2023 to 2024 only, as plan section 3 is written",
            ("2023 to 2024 and 2023 to 2025, each holding, as D134 ruled J-rise for T8",),
            "count",
        ),
        Pending(
            "R-accuracy",
            "Which records 'survive the 1,000 m filter', out of which.",
            "records with a stated accuracy of at most 1,000 m (T1's filter, t1_design.py:47), out "
            "of all records in the box, with or without a stated accuracy",
            ("strictly under 1,000 m, as plan section 3 (ii) is worded",),
            "count",
        ),  # fmt: skip
        Pending(
            "R-licence",
            "Which licences are 'GBIF-eligible'.",
            "CC0, CC BY and CC BY-NC (any version); a record with no licence is not eligible",
            ("CC0 and CC BY only (the commercial-safe track, D29)",),
            "count",
        ),
        Pending(
            "R-grade",
            "Which iNaturalist observations the totals count.",
            "research grade only, the grade GBIF carries",
            ("every quality grade",),
            "count",
        ),
    )
}

# Readings the owner has ruled, as reading id -> decision row. None yet.
RULED: dict[str, str] = {}


def open_readings(step: str) -> list[Pending]:
    return [p for p in PENDING.values() if p.step == step and p.id not in RULED]


def require_ruled(step: str) -> None:
    """Refuses while any reading the step depends on has no ruling in RULED."""
    missing = open_readings(step)
    if missing:
        raise NotRuled(
            f"{len(missing)} T8b reading(s) for the {step} are not ruled: "
            + ", ".join(p.id for p in missing)
        )

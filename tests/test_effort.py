"""T6's effort surface (D101 to D108): units, outings, the fit, scoring, verdicts and output."""

import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from forager_forecast import effort as ef
from forager_forecast.cells import Cell, IsoWeek, cell_for
from forager_forecast.records.filters import Pipeline, t6_effort_steps
from forager_forecast.records.occurrence import Record, record_from_row

REPO = Path(__file__).resolve().parents[1]


def rec(
    gbif_id=1,
    taxon=10,
    lat=45.01,
    lon=-122.01,
    day=date(2020, 6, 6),
    observer="ann",
    dataset="d1",
    license="CC_BY_NC_4_0",
    class_key=None,
    uncertainty=10.0,
    withheld="",
):
    return Record(
        gbif_id=gbif_id,
        taxon_key=taxon,
        genus_key=None,
        latitude=lat,
        longitude=lon,
        event_date=day,
        event_time=None,
        coordinate_uncertainty_m=uncertainty,
        license=license,
        dataset_key=dataset,
        recorded_by=observer,
        information_withheld=withheld,
        class_key=class_key,
    )


# Units ---------------------------------------------------------------------------------------


def test_frame_is_the_573_whole_iso_weeks():
    weeks = ef.frame_weeks()
    assert len(weeks) == 573
    assert weeks[0] == IsoWeek(2015, 2)
    assert weeks[-1] == IsoWeek(2025, 52)
    assert IsoWeek(2015, 1) not in weeks and IsoWeek(2026, 1) not in weeks
    assert IsoWeek(2015, 53) in weeks and IsoWeek(2020, 53) in weeks


def test_week_53_shares_week_52s_slot():
    assert ef.season_slot(IsoWeek(2020, 1)) == 0
    assert ef.season_slot(IsoWeek(2020, 52)) == 51
    assert ef.season_slot(IsoWeek(2020, 53)) == 51


def test_weekend_is_saturday_and_sunday():
    assert ef.day_type(date(2020, 6, 6)) == ef.WEEKEND  # Saturday
    assert ef.day_type(date(2020, 6, 7)) == ef.WEEKEND  # Sunday
    assert ef.day_type(date(2020, 6, 5)) == ef.WEEKDAY  # Friday
    assert ef.day_type(date(2020, 6, 8)) == ef.WEEKDAY  # Monday


def test_band_is_five_degrees_on_the_cell_centre():
    assert ef.band_of(Cell(249, 0)) == 20
    assert ef.band_of(Cell(250, 0)) == 25
    assert ef.band_of(Cell(499, 0)) == 45
    assert ef.band_of(Cell(195, -1555)) == 15


def test_grid_matches_the_file_committed_before_any_fit():
    grid = json.loads((REPO / "docs/audits/2026-10-06-t6-proposal/tuning_grid.json").read_text())
    assert tuple(grid["grid"]["sparse_cell_pull_pseudo_weeks"]) == ef.GRID_PULL
    assert tuple(grid["grid"]["season_smoothing_weeks"]) == ef.GRID_SMOOTHING
    assert grid["seed"] == ef.SEED == 20260918
    assert grid["bootstrap"]["resamples"] == ef.BOOTSTRAP_RESAMPLES
    assert len(ef.configs()) == 20 == grid["budget"]


# Steps and outings ---------------------------------------------------------------------------


def test_loader_reads_class_key():
    row = {
        "gbifID": "5",
        "acceptedTaxonKey": "7",
        "genusKey": "",
        "decimalLatitude": "45",
        "decimalLongitude": "-122",
        "coordinateUncertaintyInMeters": "5",
        "eventDate": "2020-06-06",
        "license": "CC0_1_0",
        "datasetKey": "d",
        "recordedBy": "x",
        "informationWithheld": "",
        "dataGeneralizations": "",
        "classKey": "180",
    }
    assert record_from_row(row).class_key == 180
    row["classKey"] = ""
    assert record_from_row(row).class_key is None


def test_t6_steps_keep_1000_m_and_drop_obscured_missing_and_wider():
    records = [
        rec(gbif_id=1, uncertainty=1000.0),
        rec(gbif_id=2, uncertainty=1000.5, observer="b"),
        rec(gbif_id=3, uncertainty=None, observer="c"),
        rec(gbif_id=4, withheld="Coordinate uncertainty increased", observer="d"),
        rec(gbif_id=5, uncertainty=250.0, observer="ann"),  # same taxon, observer, cell, day as 1
        rec(gbif_id=6, uncertainty=250.0, observer="eve"),  # another observer: kept
    ]
    pipeline = Pipeline(t6_effort_steps())
    survivors = pipeline.run(records)
    assert [r.gbif_id for r in survivors] == [1, 6]
    assert [(c.step, c.before, c.dropped) for c in pipeline.counts] == [
        ("not user-obscured", 6, 1),
        ("coordinate uncertainty present and at most 1,000 m", 5, 2),
        ("date kept as given (D97, D98)", 3, 0),
        ("one record per taxon, observer, cell and day", 3, 1),
    ]


def test_outings_are_distinct_observer_cell_days():
    counter = ef.OutingCounter()
    counter.add(rec(gbif_id=1, taxon=10))
    counter.add(rec(gbif_id=2, taxon=11))  # same person, cell, day: same outing
    counter.add(rec(gbif_id=3, observer="bob"))  # another person
    counter.add(rec(gbif_id=4, day=date(2020, 6, 8)))  # another day
    counter.add(rec(gbif_id=5, lat=46.01))  # another cell
    assert counter.outing_count("all", False) == 4


def test_empty_observer_is_one_anonymous_observer_per_dataset():
    counter = ef.OutingCounter()
    counter.add(rec(gbif_id=1, observer="", dataset="d1"))
    counter.add(rec(gbif_id=2, observer="", dataset="d1", taxon=99))
    counter.add(rec(gbif_id=3, observer="", dataset="d2"))
    assert counter.outing_count("all", False) == 2


def test_tracks_by_licence_and_benchmark():
    counter = ef.OutingCounter()
    counter.add(rec(gbif_id=1, observer="a", license="CC0_1_0", class_key=180))
    counter.add(rec(gbif_id=2, observer="b", license="CC_BY_4_0"))
    counter.add(rec(gbif_id=3, observer="c", license="CC_BY_NC_4_0", class_key=180))
    counter.add(rec(gbif_id=4, observer="d", license="something else"))
    assert counter.outing_count("all", False) == 4
    assert counter.outing_count("all", True) == 2
    assert counter.outing_count("cc", False) == 2
    assert counter.outing_count("cc", True) == 1
    assert counter.license_not_recognised == {"something else": 1}


def test_partial_weeks_are_counted_and_left_out():
    counter = ef.OutingCounter()
    counter.add(rec(gbif_id=1, day=date(2015, 1, 2)))  # 2015-W01
    counter.add(rec(gbif_id=2, day=date(2025, 12, 30)))  # 2026-W01
    counter.add(rec(gbif_id=3, day=date(2015, 1, 5)))  # 2015-W02, kept
    assert counter.outside_frame_weeks == 2
    assert counter.outing_count("all", False) == 1


def test_counts_land_in_the_right_cell_week_and_day_type():
    counter = ef.OutingCounter()
    counter.add(rec(gbif_id=1, day=date(2020, 6, 6), class_key=180))
    counter.add(rec(gbif_id=2, day=date(2020, 6, 6), observer="bob"))
    counter.add(rec(gbif_id=3, day=date(2020, 6, 8), lat=30.01))
    counts = counter.counts("all", False)
    lichen = counter.counts("all", True, frame=counts.cells)
    weeks = ef.frame_weeks()
    got = {
        (counts.cells[c].id, weeks[w].id, d, n)
        for c, w, d, n in zip(counts.cell, counts.week, counts.day, counts.count, strict=True)
    }
    assert got == {
        (cell_for(45.01, -122.01).id, "2020-W23", ef.WEEKEND, 2.0),
        (cell_for(30.01, -122.01).id, "2020-W24", ef.WEEKDAY, 1.0),
    }
    assert lichen.cells == counts.cells and lichen.total() == 1.0
    with pytest.raises(ValueError):
        counter.counts("all", True)


# The fit -------------------------------------------------------------------------------------


def synthetic(seed=0, cells_per_band=(4, 3), integer=False):
    """A full table drawn from known parts, on cells in two bands."""
    rng = np.random.default_rng(seed)
    cells = []
    for b, n in enumerate(cells_per_band):
        for i in range(n):
            cells.append(Cell(400 + 50 * b + i, -1200 - i))
    n_cells = len(cells)
    weeks = ef.frame_weeks()
    a = rng.uniform(0.2, 3.0, n_cells)
    y = rng.uniform(0.5, 2.0, len(ef.YEARS))
    s = rng.uniform(0.3, 2.0, (len(cells_per_band), ef.N_SLOTS))
    rate = np.array([0.9, 0.4])
    band = np.array([ef.band_of(c) for c in cells])
    band_ids = sorted(set(band))
    bi = np.array([band_ids.index(x) for x in band])
    entries, mu = [], {}
    for c in range(n_cells):
        for w, week in enumerate(weeks):
            for d in (0, 1):
                m = (
                    a[c]
                    * y[ef.YEARS.index(week.year)]
                    * s[bi[c], ef.season_slot(week)]
                    * rate[d]
                    * ef.DAYS_PER_TYPE[d]
                )
                mu[(c, w, d)] = m
                value = rng.poisson(m) if integer else m
                if value > 0:
                    entries.append((c, w, d, float(value)))
    return ef.OutingCounts.from_entries(cells, entries), mu, rate


def test_fit_recovers_exact_parts_from_their_own_expectations():
    counts, mu, rate = synthetic()
    surface = ef.fit(counts, ef.YEARS, ef.Config(0.0, 1))
    assert surface.weekend_ratio == pytest.approx(rate[0] / rate[1], rel=1e-8)
    weeks = ef.frame_weeks()
    for (c, w, d), m in list(mu.items())[::997]:
        week = weeks[w]
        got = (
            surface.cell_level[c]
            * surface.year_level[ef.YEARS.index(week.year)]
            * surface.season[counts.cell_band[c], ef.season_slot(week)]
            * surface.day_rate[d]
            * ef.DAYS_PER_TYPE[d]
        )
        assert got == pytest.approx(m, rel=1e-7)


def test_fit_equals_statsmodels_poisson_glm_on_a_small_table():
    sm = pytest.importorskip("statsmodels.api")
    counts, _mu, _rate = synthetic(seed=3, cells_per_band=(3, 2), integer=True)
    surface = ef.fit(counts, ef.YEARS, ef.Config(0.0, 1))
    weeks = ef.frame_weeks()
    observed = {
        (c, w, d): n
        for c, w, d, n in zip(counts.cell, counts.week, counts.day, counts.count, strict=True)
    }
    rows, response, offset = [], [], []
    n_bands = counts.n_bands
    # Cells nested in bands: each band's slot 0 is its reference, one year is the reference.
    n_columns = counts.n_cells + len(ef.YEARS) - 1 + n_bands * (ef.N_SLOTS - 1) + 1
    for c in range(counts.n_cells):
        for w, week in enumerate(weeks):
            for d in (0, 1):
                x = np.zeros(n_columns)
                x[c] = 1.0
                y_index = ef.YEARS.index(week.year)
                if y_index:
                    x[counts.n_cells + y_index - 1] = 1.0
                slot = ef.season_slot(week)
                if slot:
                    column = counts.cell_band[c] * (ef.N_SLOTS - 1) + slot - 1
                    x[counts.n_cells + len(ef.YEARS) - 1 + column] = 1.0
                x[-1] = 1.0 if d == ef.WEEKEND else 0.0
                rows.append(x)
                response.append(observed.get((c, w, d), 0.0))
                offset.append(math.log(ef.DAYS_PER_TYPE[d]))
    glm = sm.GLM(
        np.array(response), np.array(rows), family=sm.families.Poisson(), offset=np.array(offset)
    ).fit(tol=1e-12, maxiter=200)
    assert surface.weekend_ratio == pytest.approx(math.exp(glm.params[-1]), rel=1e-6)
    fitted = glm.fittedvalues
    for i in range(0, len(rows), 1013):
        c = i // (len(weeks) * 2)
        w = (i // 2) % len(weeks)
        d = i % 2
        week = weeks[w]
        got = (
            surface.cell_level[c]
            * surface.year_level[ef.YEARS.index(week.year)]
            * surface.season[counts.cell_band[c], ef.season_slot(week)]
            * surface.day_rate[d]
            * ef.DAYS_PER_TYPE[d]
        )
        assert got == pytest.approx(fitted[i], rel=1e-5)


def test_pull_gives_an_unseen_cell_a_positive_level_and_grows_with_lambda():
    counts, _mu, _rate = synthetic(seed=1)
    # Drop every outing of cell 0 from the training years: only 2025 keeps it.
    keep = ~((counts.cell == 0) & (counts.entry_year != ef.YEARS.index(2025)))
    sparse = ef.OutingCounts.from_entries(
        counts.cells,
        zip(
            counts.cell[keep], counts.week[keep], counts.day[keep], counts.count[keep], strict=True
        ),
    )
    train = ef.YEARS[:-1]
    assert ef.fit(sparse, train, ef.Config(0.0, 1)).cell_level[0] == 0.0
    small = ef.fit(sparse, train, ef.Config(0.1, 1)).cell_level[0]
    large = ef.fit(sparse, train, ef.Config(10.0, 1)).cell_level[0]
    assert 0.0 < small < large


def test_season_smoothing_wraps_around_the_year():
    values = np.zeros((1, ef.N_SLOTS))
    values[0, 0] = 1.0
    summed = ef.circular_window_sum(values, 3)
    assert summed[0, 51] == 1.0 and summed[0, 1] == 1.0 and summed[0, 2] == 0.0
    with pytest.raises(ValueError):
        ef.circular_window_sum(values, 2)


def test_a_term_left_out_stays_at_one():
    counts, _mu, _rate = synthetic(seed=2)
    surface = ef.fit(
        counts, ef.YEARS, ef.Config(0.1, 1), terms=frozenset({"cell", "year", "season"})
    )
    assert surface.weekend_ratio == 1.0
    cell_only = ef.fit(counts, ef.YEARS, ef.Config(0.1, 1), terms=frozenset({"cell"}))
    assert np.all(cell_only.season == 1.0)


def test_unit_cell_weights_equal_the_unweighted_fit():
    counts, _mu, _rate = synthetic(seed=4, integer=True)
    plain = ef.fit(counts, ef.YEARS, ef.Config(1.0, 3))
    weighted = ef.fit(counts, ef.YEARS, ef.Config(1.0, 3), cell_weights=np.ones(counts.n_cells))
    assert weighted.weekend_ratio == pytest.approx(plain.weekend_ratio, rel=1e-12)


def test_combined_surface_keeps_band_level_and_takes_lichen_shape():
    counts, _mu, _rate = synthetic(seed=5)
    lichen_counts, _m, _r = synthetic(seed=6)
    train = ef.YEARS
    fungal = ef.fit(counts, train, ef.Config(0.1, 1))
    lichen = ef.fit(lichen_counts, train, ef.Config(0.1, 1))
    combined = ef.combine(fungal, lichen, counts, train)
    weeks_per_slot = counts.weeks_per_year_slot.sum(axis=0)
    np.testing.assert_allclose(combined.season @ weeks_per_slot, fungal.season @ weeks_per_slot)
    shape = combined.season / lichen.season
    np.testing.assert_allclose(shape, shape[:, :1] * np.ones((1, ef.N_SLOTS)))
    mass = np.bincount(counts.cell_band, weights=fungal.cell_level)
    per_year_f = fungal.year_level * (counts.weeks_per_year_slot @ (mass @ fungal.season))
    per_year_c = combined.year_level * (counts.weeks_per_year_slot @ (mass @ combined.season))
    np.testing.assert_allclose(per_year_c, per_year_f)


# Scoring -------------------------------------------------------------------------------------


def dense_mu(surface, counts, year, scale):
    weeks = ef.frame_weeks()
    out = {}
    for c in range(counts.n_cells):
        for w, week in enumerate(weeks):
            if week.year != year:
                continue
            for d in (0, 1):
                out[(c, w, d)] = (
                    scale
                    * surface.cell_level[c]
                    * surface.season[counts.cell_band[c], ef.season_slot(week)]
                    * surface.day_rate[d]
                    * ef.DAYS_PER_TYPE[d]
                )
    return out


def dense_y(counts, keys):
    observed = {
        (c, w, d): n
        for c, w, d, n in zip(counts.cell, counts.week, counts.day, counts.count, strict=True)
    }
    return np.array([observed.get(k, 0.0) for k in keys])


def test_per_cell_deviance_given_total_equals_the_dense_deviance():
    counts, _mu, _rate = synthetic(seed=7, integer=True)
    train = [y for y in ef.YEARS if y != 2019]
    surface = ef.fit(counts, train, ef.Config(0.3, 3))
    per_cell = ef.surface_deviance(surface, counts, 2019)
    unscaled = dense_mu(surface, counts, 2019, 1.0)
    keys = list(unscaled)
    y = dense_y(counts, keys)
    mu = np.array([unscaled[k] for k in keys])
    mu *= y.sum() / mu.sum()
    assert per_cell.sum() == pytest.approx(ef.dense_poisson_deviance(y, mu), rel=1e-9)


def test_interpolated_scoring_uses_the_neighbouring_years():
    counts, _mu, _rate = synthetic(seed=8, integer=True)
    train = [y for y in ef.YEARS if y != 2019]
    surface = ef.fit(counts, train, ef.Config(0.3, 1))
    level = math.sqrt(
        surface.year_level[ef.YEARS.index(2018)] * surface.year_level[ef.YEARS.index(2020)]
    )
    assert ef.interpolated_year_level(surface.year_level, 2019) == pytest.approx(level)
    per_cell = ef.surface_deviance(surface, counts, 2019, given_total=False)
    unscaled = dense_mu(surface, counts, 2019, level)
    keys = list(unscaled)
    assert per_cell.sum() == pytest.approx(
        ef.dense_poisson_deviance(dense_y(counts, keys), np.array([unscaled[k] for k in keys])),
        rel=1e-9,
    )


def test_interpolation_at_an_end_takes_the_nearest_year():
    levels = np.full(len(ef.YEARS), np.nan)
    levels[1:] = np.arange(1, len(ef.YEARS)) * 2.0
    assert ef.interpolated_year_level(levels, 2015) == 2.0


def test_constant_model_deviance_equals_the_dense_deviance():
    counts, _mu, _rate = synthetic(seed=9, integer=True)
    per_cell = ef.constant_deviance(counts, 2021)
    weeks = ef.frame_weeks()
    keys = [
        (c, w, d)
        for c in range(counts.n_cells)
        for w, wk in enumerate(weeks)
        if wk.year == 2021
        for d in (0, 1)
    ]
    y = dense_y(counts, keys)
    per_day = y.sum() / (counts.n_cells * sum(1 for wk in weeks if wk.year == 2021) * 7)
    mu = np.array([per_day * ef.DAYS_PER_TYPE[d] for _c, _w, d in keys])
    assert mu.sum() == pytest.approx(y.sum())
    assert per_cell.sum() == pytest.approx(ef.dense_poisson_deviance(y, mu), rel=1e-9)


def test_a_true_surface_beats_constant_effort_on_its_own_data():
    counts, _mu, _rate = synthetic(seed=10, integer=True)
    train = [y for y in ef.YEARS if y != 2022]
    surface = ef.fit(counts, train, ef.Config(0.1, 1))
    assert (
        ef.surface_deviance(surface, counts, 2022).sum() < ef.constant_deviance(counts, 2022).sum()
    )


# Bootstrap and verdicts ----------------------------------------------------------------------


def test_cluster_weights_draw_every_cell_count_and_repeat_by_seed():
    first = list(ef.cluster_weights(50, resamples=3, seed=ef.SEED))
    again = list(ef.cluster_weights(50, resamples=3, seed=ef.SEED))
    assert all(w.sum() == 50 for w in first)
    assert all(np.array_equal(a, b) for a, b in zip(first, again, strict=True))
    assert not np.array_equal(first[0], first[1])


def test_verdicts_need_the_whole_interval_on_one_side():
    assert ef.weekend_condition_1((1.01, 1.4))
    assert not ef.weekend_condition_1((0.99, 1.4))
    assert not ef.weekend_condition_1((1.0, 1.4))
    assert ef.lower_deviance_condition((-50.0, -0.1))
    assert not ef.lower_deviance_condition((-50.0, 0.0))
    assert not ef.lower_deviance_condition((-50.0, 3.0))


def test_percentile_interval():
    assert ef.percentile_interval(list(range(101))) == pytest.approx((2.5, 97.5))


# Output --------------------------------------------------------------------------------------


def test_written_surface_reads_back_and_refuses_outside_the_frame(tmp_path):
    counts, _mu, _rate = synthetic(seed=11)
    fungal = ef.fit(counts, ef.YEARS, ef.Config(0.1, 1))
    lichen = ef.fit(counts, ef.YEARS, ef.Config(0.1, 1))
    combined = ef.combine(fungal, lichen, counts, ef.YEARS)
    digests = ef.write_surface(tmp_path, counts, fungal, lichen, combined, {"track": "test"})
    assert set(digests) == {
        "cell_level.csv",
        "year_level.csv",
        "season.csv",
        "day_type.csv",
        "effort_manifest.json",
    }
    stored = ef.EffortSurface.read(tmp_path)
    cell = counts.cells[2]
    week = IsoWeek(2020, 53)
    value, log_value = stored.effort(cell, week)
    expected = (
        combined.cell_level[2]
        * combined.year_level[ef.YEARS.index(2020)]
        * combined.season[counts.cell_band[2], 51]
        * (combined.day_rate * ef.DAYS_PER_TYPE).sum()
    )
    assert value == pytest.approx(expected, rel=1e-12)
    assert log_value == pytest.approx(math.log(expected))
    with pytest.raises(ef.NoEffortValue):
        stored.effort(Cell(0, 0), week)
    with pytest.raises(ef.NoEffortValue):
        stored.effort(cell, IsoWeek(2026, 1))


def test_a_resample_without_a_band_still_fits():
    counts, _mu, rate = synthetic(seed=12)
    weights = np.where(counts.cell_band == 1, 0.0, 2.0)
    surface = ef.fit(counts, ef.YEARS, ef.Config(0.1, 3), cell_weights=weights)
    assert np.all(np.isfinite(surface.season)) and np.all(np.isfinite(surface.cell_level))
    assert surface.weekend_ratio == pytest.approx(rate[0] / rate[1], rel=1e-6)

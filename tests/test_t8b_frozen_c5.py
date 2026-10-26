"""D159 (5): the frozen model's save and load under a recorded checksum, and the C5 scorer on a
later download. Small synthetic data and real LightGBM on a tiny grid."""

import hashlib
from datetime import UTC, datetime

import numpy as np
import pytest
from t8b_files import rule_all, unrule_all

from forager_forecast import t1_model as tm
from forager_forecast.t8b import c5, design
from forager_forecast.t8b import frozen as fz

TINY = [
    {"id": "c0", "num_leaves": 3, "learning_rate": 0.1, "num_boost_round": 5,
     "min_data_in_leaf": 5, "feature_fraction": 1.0, "lambda_l2": 0.0},
    {"id": "c1", "num_leaves": 7, "learning_rate": 0.1, "num_boost_round": 10,
     "min_data_in_leaf": 5, "feature_fraction": 1.0, "lambda_l2": 1.0},
]  # fmt: skip
FEATURES = ("doy_sin", "doy_cos", "latitude", "longitude", "effort", "M1")


def data(n_per_year=60, seed=2):
    rng = np.random.default_rng(seed)
    years = np.repeat(np.arange(2015, 2026), n_per_year)
    x = rng.normal(size=(len(years), 6))
    p = 1 / (1 + np.exp(-(-1.5 + 1.2 * x[:, 5])))
    y = (rng.random(len(years)) < p).astype(float)
    return x, y, years


@pytest.fixture(scope="module")
def main_model():
    x, y, years = data()
    return fz.fit_frozen("main", x, y, years, TINY, FEATURES, (5,))


def test_the_frozen_configuration_is_t1s_inner_choice_over_all_eleven_years(main_model):
    x, y, years = data()

    def fitter(config, train_x, train_y, test_x):
        return tm.fit_predict(config, train_x, train_y, test_x, 1)

    best, _ = tm.inner_choice(TINY, x, y, years, fitter)
    assert main_model.config == best
    assert main_model.training_years == tuple(range(2015, 2026))


def test_the_clamp_range_frozen_is_the_training_range(main_model):
    x, _y, _years = data()
    assert main_model.weather_columns == (5,)
    assert main_model.clamp_low == (float(x[:, 5].min()),)
    assert main_model.clamp_high == (float(x[:, 5].max()),)


def test_save_records_the_files_sha256_and_load_gives_the_same_predictions(main_model, tmp_path):
    path = tmp_path / "main.frozen.json"
    digest = fz.save(main_model, path)
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()
    again = fz.load(path, digest)
    x, _y, _years = data(seed=7)
    assert np.array_equal(fz.predict(again, x), fz.predict(main_model, x))


def test_a_different_checksum_or_an_edited_file_is_refused(main_model, tmp_path):
    path = tmp_path / "main.frozen.json"
    digest = fz.save(main_model, path)
    with pytest.raises(fz.ChecksumDiffers):
        fz.load(path, "0" * 64)
    path.write_bytes(path.read_bytes().replace(b'"main"', b'"mainx"'))
    with pytest.raises(fz.ChecksumDiffers):
        fz.load(path, digest)


def test_saving_twice_gives_the_same_checksum(main_model, tmp_path):
    assert fz.save(main_model, tmp_path / "a.json") == fz.save(main_model, tmp_path / "b.json")


# C5 ----------------------------------------------------------------------------------------------


def test_the_download_must_be_taken_after_15_february_2027():
    with pytest.raises(c5.C5Refused, match="2027-02-16"):
        c5.check_download(datetime(2027, 2, 15, 23, 59, tzinfo=UTC))
    c5.check_download(datetime(2027, 2, 16, 0, 0, tzinfo=UTC))


def units_2026(n=400, seed=4, weeks=None):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 6))
    p = 1 / (1 + np.exp(-(-1.5 + 1.2 * x[:, 5])))
    y = (rng.random(n) < p).astype(float)
    week = rng.integers(27, 53, size=n) if weeks is None else np.asarray(weeks)
    return c5.C5Units(
        unit=np.array([f"u{i}" for i in range(n)]),
        cell=np.array([f"c{i % 40}" for i in range(n)]),
        iso_year=np.full(n, 2026),
        iso_week=week,
        y=y,
        x_main=x,
        x_calendar=x[:, :4],
    )


@pytest.fixture(scope="module")
def calendar_model():
    x, y, years = data()
    return fz.fit_frozen("calendar", x[:, :4], y, years, TINY, FEATURES[:4], ())


AFTER = datetime(2027, 3, 1, tzinfo=UTC)


def test_c5_refuses_while_its_readings_are_open(main_model, calendar_model, monkeypatch):
    unrule_all(monkeypatch)
    with pytest.raises(design.NotRuled):
        c5.score_c5(main_model, calendar_model, units_2026(), AFTER)


def test_c5_scores_the_frozen_model_against_the_calendar_on_2026(
    monkeypatch, main_model, calendar_model
):
    rule_all(monkeypatch, "c5")
    u = units_2026()
    out = c5.score_c5(main_model, calendar_model, u, AFTER)
    p = fz.predict(main_model, u.x_main)
    q = fz.predict(calendar_model, u.x_calendar)
    assert out["skill"] == pytest.approx(tm.brier_skill(p, q, u.y))
    assert out["passed"] == (out["skill"] > 0)
    assert out["resamples"] == 1000 and out["seed"] == 20260918
    assert out["low"] <= out["skill"] <= out["high"]
    assert out["units"] == 400 and out["weeks_left_out"] == []


def test_c5_refuses_a_unit_outside_2026_weeks_27_to_52(monkeypatch, main_model, calendar_model):
    rule_all(monkeypatch, "c5")
    with pytest.raises(c5.C5Refused, match="week"):
        c5.score_c5(main_model, calendar_model, units_2026(n=3, weeks=[26, 30, 40]), AFTER)
    u = units_2026(n=3, weeks=[27, 30, 52])
    u = c5.C5Units(u.unit, u.cell, np.array([2026, 2025, 2026]), u.iso_week, u.y, u.x_main,
                   u.x_calendar)  # fmt: skip
    with pytest.raises(c5.C5Refused, match="2026"):
        c5.score_c5(main_model, calendar_model, u, AFTER)


def test_c5_refuses_an_early_download(monkeypatch, main_model, calendar_model):
    rule_all(monkeypatch, "c5")
    with pytest.raises(c5.C5Refused):
        c5.score_c5(main_model, calendar_model, units_2026(), datetime(2027, 1, 2, tzinfo=UTC))


def test_weeks_whose_outcome_was_already_read_are_left_out_and_named(
    monkeypatch, main_model, calendar_model
):
    rule_all(monkeypatch, "c5")
    u = units_2026()
    out = c5.score_c5(main_model, calendar_model, u, AFTER, excluded_weeks=(41, 42))
    keep = ~np.isin(u.iso_week, [41, 42])
    assert out["units"] == int(keep.sum())
    assert out["weeks_left_out"] == [41, 42]

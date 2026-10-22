"""T8's evaluation end to end on synthetic worlds: built to pass, and built so weather is noise."""

from datetime import date

import numpy as np
import pytest

from forager_forecast import t1_model as tm
from forager_forecast.t8 import models as md
from forager_forecast.t8 import run as tr
from forager_forecast.t8 import weather as tw
from forager_forecast.t8.design import N_SWAPS, YEARS


def world(weather_effect, per_year=160, seed=11):
    rng = np.random.default_rng(seed)
    years = np.repeat(np.array(YEARS), per_year)
    n = len(years)
    cells = rng.integers(0, 120, size=n)
    week = rng.integers(1, 53, size=n)
    mondays = [date.fromisocalendar(int(y), int(w), 1) for y, w in zip(years, week, strict=True)]
    lat = 42 + 7.5 * (cells % 12) / 12 + rng.normal(0, 0.01, n)
    lon = -125 + 4 * (cells // 12) / 10 + rng.normal(0, 0.01, n)
    log_e = rng.normal(0, 0.5, n)
    table = {s: rng.normal(size=(n, 4)) for s in YEARS}
    weather = np.vstack([table[int(y)][i] for i, y in enumerate(years)])
    angle = md.day_of_year_angle(mondays)
    eta = -2.5 + 1.0 * np.cos(angle - 4.9) + 0.6 * log_e + weather_effect * weather[:, 0]
    y = (rng.random(n) < 1 / (1 + np.exp(-eta))).astype(float)
    lichen_eta = -2.0 + 0.6 * log_e
    lichen_y = (rng.random(n) < 1 / (1 + np.exp(-lichen_eta))).astype(float)
    inputs = md.Inputs(y, years, mondays, lat, lon, {h: log_e for h in YEARS}, weather)
    t1_p = np.full(n, y.mean())
    return inputs, t1_p, cells, lichen_y, table


@pytest.fixture(scope="module")
def swaps():
    return tw.draw_swaps(YEARS, N_SWAPS)


def test_a_world_where_weather_drives_reports_passes_the_bar(swaps):
    inputs, t1_p, cells, lichen_y, table = world(weather_effect=1.2)
    run = tr.additive_bar(inputs, t1_p, cells, lichen_y, md.PROPOSED_SPEC, table, swaps)
    assert [c.name for c in run.bar.conditions if not c.passed] == []
    assert run.bar.passed
    assert run.bar.conditions[2].figures["swaps_at_or_above"] == 0


def test_a_world_where_weather_is_noise_fails_on_c2_and_c3(swaps):
    inputs, t1_p, cells, lichen_y, table = world(weather_effect=0.0)
    run = tr.additive_bar(inputs, t1_p, cells, lichen_y, md.PROPOSED_SPEC, table, swaps)
    failing = [c.name for c in run.bar.conditions if not c.passed]
    assert "C2" in failing and "C3" in failing
    assert not run.bar.passed


def test_report_beside_items_carry_no_verdict(swaps):
    inputs, t1_p, cells, _ly, table = world(weather_effect=1.2, per_year=60)
    p = md.loyo_additive(inputs, md.PROPOSED_SPEC, True)
    p0 = md.loyo_additive(inputs, md.PROPOSED_SPEC, False)
    rows = tr.per_year_table(inputs.y, inputs.years, p, {"t1_calendar": t1_p, "no_weather": p0})
    assert [r["year"] for r in rows] == list(YEARS)
    assert all(r["label"] == tr.NO_VERDICT for r in rows)
    held = inputs.years == 2019
    assert rows[4]["skill_vs_no_weather"] == pytest.approx(
        tm.brier_skill(p[held], p0[held], inputs.y[held])
    )
    line = tr.beside_line(inputs.y, inputs.years, p, {"no_weather": p0}, cells)
    assert line["years"] == [2015, 2023] and line["label"] == tr.NO_VERDICT
    assert line["no_weather"]["units"] == int(np.isin(inputs.years, range(2015, 2024)).sum())
    alone = tr.measure_alone(inputs, md.PROPOSED_SPEC, p0, cells, table, swaps[:N_SWAPS], 0)
    assert alone["measure"] == "W1" and alone["label"] == tr.NO_VERDICT
    assert alone["swaps"] == N_SWAPS
    assert set(tr.describe(p, inputs.y)) == {"brier", "auc", "reliability"}


def test_ecoregion_report_holds_out_each_block():
    inputs, _t1, cells, _ly, _table = world(weather_effect=1.2, per_year=80)
    blocks = np.where(inputs.latitude > 46, "north", "south")
    out = tr.ecoregion_report(inputs, md.PROPOSED_SPEC, blocks, inputs.log_effort[2015], cells)
    assert [b["block"] for b in out["blocks"]] == ["north", "south"]
    assert out["label"] == tr.NO_VERDICT

"""T8's fit end to end on synthetic files laid out as the real inputs are: T1's unit file, the
count's lichen file, a daily weather npz, T6's counts with SHA256SUMS and T6's results. Every
identity check refuses on one changed value. No real data is read."""

import hashlib
import json
from datetime import date

import numpy as np
import pytest

from forager_forecast import effort as ef
from forager_forecast.cells import Cell, quarter_cell_for
from forager_forecast.t8 import design
from forager_forecast.t8 import fit as tf
from forager_forecast.t8 import units as tu
from forager_forecast.t8 import weather as tw

START = date(2014, 9, 1)
DAYS = 4140
CELLS = [Cell(440 + i, -1240 + 4 * (i % 8)) for i in range(40)]
PER_YEAR = 160


def grids_arrays(rng):
    land = np.array([(c.lat_tenths, c.lon_tenths) for c in CELLS], dtype=np.int32)
    rain = sorted(
        {
            (q.lat_quarters, q.lon_quarters)
            for q in (quarter_cell_for(c.center_latitude, c.center_longitude) for c in CELLS)
        }
    )
    arrays = {"start": np.array(START.isoformat())}
    for v in ("temperature", "soil_temperature", "soil_moisture"):
        arrays[f"{v}_points"] = land
        arrays[f"{v}_values"] = rng.normal(size=(len(CELLS), DAYS))
    arrays["precipitation_points"] = np.array(rain, dtype=np.int32)
    arrays["precipitation_values"] = rng.gamma(1.0, 2.0, size=(len(rain), DAYS))
    return arrays


def counts_entries(rng):
    weeks = ef.frame_weeks()
    a = rng.uniform(0.5, 3.0, len(CELLS))
    entries = []
    for c in range(len(CELLS)):
        draws = rng.poisson(a[c] * 2.0, size=(len(weeks), 2))
        for w, d in zip(*np.nonzero(draws), strict=True):
            entries.append((c, int(w), int(d), float(draws[w, d])))
    return entries


def save_counts(path, entries):
    cell, week, day, count = (np.array(x) for x in zip(*entries, strict=True))
    np.savez(
        path,
        lat_tenths=np.array([c.lat_tenths for c in CELLS], dtype=np.int64),
        lon_tenths=np.array([c.lon_tenths for c in CELLS], dtype=np.int64),
        cell=cell.astype(np.int64),
        week=week.astype(np.int64),
        day=day.astype(np.int64),
        count=count.astype(np.float64),
    )


def build(folder):
    """Writes the files; returns their paths. Outcomes depend on W1 at the headline timing."""
    rng = np.random.default_rng(20261020)
    weather_npz = folder / "t1_pnw.npz"
    np.savez_compressed(weather_npz, **grids_arrays(rng))
    counts = folder / "t6-counts"
    counts.mkdir()
    sums = []
    for name, seed in (("all_fungi.npz", 1), ("all_lichen.npz", 2)):
        save_counts(counts / name, counts_entries(np.random.default_rng(seed)))
        sums.append(f"{hashlib.sha256((counts / name).read_bytes()).hexdigest()}  {name}")
    (counts / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    results = folder / "all_results.json"
    results.write_text(json.dumps({"chosen_per_fold": {str(y): "pull=10,smoothing=3"
                                                       for y in ef.YEARS}}))  # fmt: skip
    units = []
    for year in design.YEARS:
        first = 2 if year == 2015 else 1
        pairs = rng.choice(len(CELLS) * 52, size=PER_YEAR, replace=False)
        for k in sorted(pairs):
            cell, week = CELLS[k // 52], first + (k % 52) % (53 - first)
            units.append(tu.unit_id(cell, date.fromisocalendar(year, week, 1)))
    units = sorted(set(units))
    cells = [tu.parse_cell(u.split("@")[0]) for u in units]
    mondays = [date.fromisoformat(u.split("@")[1]) for u in units]
    grids = tw.read_grids(weather_npz)
    points = tw.unit_points(cells, grids)
    w = tw.measures_for_units(grids, points, mondays, design.HEADLINE_END_GAP)
    z = (w[:, 0] - w[:, 0].mean()) / w[:, 0].std()
    angle = np.array([2 * np.pi * (d.timetuple().tm_yday - 1) / 365.25 for d in mondays])
    eta = -2.3 + 0.8 * np.cos(angle - 4.9) + 1.3 * z
    y = (rng.random(len(units)) < 1 / (1 + np.exp(-eta))).astype(float)
    years = [d.isocalendar().year for d in mondays]
    units_npz = folder / "primary_t1_1000m_calendar.npz"
    np.savez_compressed(
        units_npz,
        unit=np.array(units),
        cell=np.array([c.id for c in cells]),
        year=np.array(years),
        y=y,
        p=np.full(len(units), y.mean()),
        land_point=np.array(points.land_kind),
    )
    lichen_npz = folder / "lichen_t1_1000m.npz"
    lichen_y = (rng.random(len(units)) < 0.15).astype(float)
    np.savez_compressed(lichen_npz, unit=np.array(units), lichen_y=lichen_y)
    return {
        "units_npz": units_npz,
        "lichen_npz": lichen_npz,
        "weather_npz": weather_npz,
        "counts_dir": counts,
        "track": "all",
        "t6_results": results,
    }, len(units)


@pytest.fixture(scope="module")
def files(tmp_path_factory):
    folder = tmp_path_factory.mktemp("t8fit")
    paths, n = build(folder)
    return folder, paths, n


@pytest.fixture
def ruled(monkeypatch, files):
    _folder, _paths, n = files
    monkeypatch.setattr(design, "RULED", {p: "test" for p in design.PENDING})
    monkeypatch.setitem(design.T1_LISTS, "t1_1000m", ("primary_t1_1000m_calendar", n))


@pytest.fixture(scope="module")
def prepared(files):
    _folder, paths, n = files
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(design, "RULED", {p: "test" for p in design.PENDING})
        mp.setitem(design.T1_LISTS, "t1_1000m", ("primary_t1_1000m_calendar", n))
        return tf.prepare("t1_1000m", **paths)


def test_prepare_lines_every_input_up_with_t1s_units(prepared, files):
    _folder, _paths, n = files
    assert prepared.is_headline and len(prepared.t1) == n
    assert sorted(prepared.headline.log_effort) == list(design.YEARS)
    assert prepared.headline.weather.shape == (n, 4)
    assert prepared.forecast.weather.shape == (n, 4)
    assert not np.array_equal(prepared.headline.weather, prepared.forecast.weather)
    assert prepared.effort_configs[2020] == "pull=10,smoothing=3"
    # Each fold's effort differs in its own held-out year, not only in level.
    assert not np.allclose(prepared.headline.log_effort[2015], prepared.headline.log_effort[2016])


def test_lichen_units_in_another_order_are_refused(files, ruled, tmp_path):
    _folder, paths, _n = files
    z = np.load(paths["lichen_npz"])
    path = tmp_path / "lichen.npz"
    np.savez(path, unit=z["unit"][::-1], lichen_y=z["lichen_y"][::-1])
    with pytest.raises(tf.InputsDiffer, match="T1's order"):
        tf.prepare("t1_1000m", **(paths | {"lichen_npz": path}))


def test_a_land_point_other_than_t1s_is_refused(files, ruled, tmp_path):
    _folder, paths, _n = files
    z = dict(np.load(paths["units_npz"]))
    z["land_point"] = z["land_point"].copy()
    z["land_point"][3] = "neighbour"
    path = tmp_path / "primary_t1_1000m_calendar.npz"
    np.savez(path, **z)
    with pytest.raises(tf.InputsDiffer, match="1 units' land point"):
        tf.prepare("t1_1000m", **(paths | {"units_npz": path}))


def test_a_unit_count_other_than_the_designs_is_refused(files, ruled, monkeypatch):
    _folder, paths, n = files
    monkeypatch.setitem(design.T1_LISTS, "t1_1000m", ("primary_t1_1000m_calendar", n + 1))
    with pytest.raises(tu.UnitsDiffer, match=f"expected {n + 1}"):
        tf.prepare("t1_1000m", **paths)


def test_the_fit_refuses_while_a_reading_is_open(files, monkeypatch):
    _folder, paths, _n = files
    monkeypatch.setattr(design, "RULED", {})
    with pytest.raises(design.NotRuled, match="fit"):
        tf.prepare("t1_1000m", **paths)


def test_the_bar_part_runs_end_to_end_and_only_it_carries_the_verdict(prepared, ruled, tmp_path):
    with pytest.raises(FileNotFoundError, match="bar part first"):
        tf.run_part("challenger", prepared, tmp_path, fitter=_stub, configs=_CONFIGS)
    out = tf.run_part("bar", prepared, tmp_path)
    assert out["bar"]["label"] == tf.VERDICT
    assert [c["name"] for c in out["bar"]["conditions"] if not c["passed"]] == []
    assert out["bar"]["conditions"][2]["figures"]["swaps_at_or_above"] == 0
    written = json.loads((tmp_path / "t1_1000m_bar.json").read_text())
    assert written["bar"]["passed"] is True
    assert len(written["bar"]["swap_briers"]) == design.N_SWAPS
    assert all(r["label"] == "no verdict" for r in written["per_year"])
    p = np.load(tmp_path / "t1_1000m_bar.npz")
    assert np.array_equal(p["unit"], prepared.t1.unit)
    challenger = tf.run_part("challenger", prepared, tmp_path, fitter=_stub, configs=_CONFIGS)
    assert challenger["challenger"]["label"] == "no verdict"
    # D136: the challenger's C3 is labelled slightly generous to true weather, in the output.
    c3 = next(c for c in challenger["challenger"]["conditions"] if c["name"] == "C3")
    assert c3["label"] == tf.CHALLENGER_C3_LABEL
    assert "slightly generous to true weather" in c3["label"]
    written = json.loads((tmp_path / "t1_1000m_challenger.json").read_text())
    assert next(c for c in written["challenger"]["conditions"] if c["name"] == "C3")["label"] == (
        tf.CHALLENGER_C3_LABEL
    )
    assert challenger["better_by_brier"]["better"] == "main"


def test_the_ecoregion_part_holds_out_each_block_with_no_verdict(prepared, ruled, tmp_path):
    blocks = np.where(prepared.headline.latitude > 46, "north", "south")
    out = tf.run_part("ecoregion", prepared, tmp_path, blocks=blocks,
                      block_effort=prepared.headline.log_effort[2015])  # fmt: skip
    assert out["ecoregion"]["label"] == "no verdict"
    assert [b["block"] for b in out["ecoregion"]["blocks"]] == ["north", "south"]


_CONFIGS = [{"id": "c00"}]


def _stub(_config, _train_x, train_y, test_x):
    return np.full(len(test_x), float(train_y.mean()))


def _counts_without_first_cell(folder):
    """T6's counts with CELLS[0] left out of the frame, as the 5,000 m list met on real data."""
    counts = folder / "t6-counts-short"
    counts.mkdir()
    sums = []
    for name, seed in (("all_fungi.npz", 1), ("all_lichen.npz", 2)):
        entries = [(c - 1, w, d, n) for c, w, d, n in counts_entries(np.random.default_rng(seed))
                   if c != 0]  # fmt: skip
        cell, week, day, count = (np.array(x) for x in zip(*entries, strict=True))
        np.savez(
            counts / name,
            lat_tenths=np.array([c.lat_tenths for c in CELLS[1:]], dtype=np.int64),
            lon_tenths=np.array([c.lon_tenths for c in CELLS[1:]], dtype=np.int64),
            cell=cell.astype(np.int64),
            week=week.astype(np.int64),
            day=day.astype(np.int64),
            count=count.astype(np.float64),
        )
        sums.append(f"{hashlib.sha256((counts / name).read_bytes()).hexdigest()}  {name}")
    (counts / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    return counts


def test_the_5000m_list_drops_units_outside_t6s_frame_and_records_them(
    files, ruled, tmp_path, monkeypatch
):
    # D137: for t1_5000m only, units in cells outside T6's frame are dropped, counted, and no
    # effort value is made up for them.
    _folder, paths, n = files
    monkeypatch.setitem(design.T1_LISTS, "t1_5000m", ("primary_t1_5000m_calendar", n))
    short = _counts_without_first_cell(tmp_path)
    z = np.load(paths["units_npz"])
    out_cell = z["cell"] == CELLS[0].id
    lichen = np.load(paths["lichen_npz"])["lichen_y"]
    assert out_cell.sum() > 0 and z["y"][out_cell].sum() > 0
    prep = tf.prepare("t1_5000m", **(paths | {"counts_dir": short}))
    assert prep.dropped == {
        "rule": "D137",
        "cells": 1,
        "units": int(out_cell.sum()),
        "positives": int(z["y"][out_cell].sum()),
        "lichen_positives": int(lichen[out_cell].sum()),
    }
    assert len(prep.t1) == n - int(out_cell.sum())
    assert CELLS[0].id not in set(prep.cells.tolist())
    assert np.array_equal(prep.t1.unit, z["unit"][~out_cell])
    assert np.array_equal(prep.lichen_y, lichen[~out_cell])
    blocks = np.where(prep.headline.latitude > 46, "north", "south")
    tf.run_part("ecoregion", prep, tmp_path, blocks=blocks,
                block_effort=prep.headline.log_effort[2015])  # fmt: skip
    written = json.loads((tmp_path / "t1_5000m_ecoregion.json").read_text())
    assert written["dropped_outside_t6_frame"] == prep.dropped
    assert np.array_equal(np.load(tmp_path / "t1_5000m_ecoregion.npz")["unit"], prep.t1.unit)


@pytest.mark.parametrize("name", ["t1_1000m", "t1_1000m_cc"])
def test_the_headline_and_cc_lists_still_refuse_a_cell_outside_t6s_frame(
    files, ruled, tmp_path, monkeypatch, name
):
    # D137 leaves the headline and cc paths unchanged: the refusal stays in force for them.
    _folder, paths, n = files
    monkeypatch.setitem(design.T1_LISTS, name, (design.T1_LISTS[name][0], n))
    short = _counts_without_first_cell(tmp_path)
    with pytest.raises(ef.NoEffortValue, match="1 unit cell"):
        tf.prepare(name, **(paths | {"counts_dir": short}))

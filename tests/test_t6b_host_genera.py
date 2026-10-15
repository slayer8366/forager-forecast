"""T6b host genera for the mycorrhizal map (docs/dispatch/2026-10-15-t6b-host-genera-build.md).

The owner's rulings (Forager RECORD -1033, provisional; the go in -1037): tier A and tier B genera
and an ectomycorrhizal-host total in one pass, as a T6b-only list with T5's list unchanged; Canada
flags what SCANFI cannot supply; old tiles kept, not deleted. And the verify report's two findings
(docs/audits/2026-10-15-t6b-host-genera-verify-report.md on t6b-host-genera-verify, section 4):
F1, a tree tile was counted done by its key and file hashes alone, so a tile built with the old
genus list would be skipped; F2, the plot table was rebuilt only when its rulings string changed.

Every test here goes through an entry point the run uses: ``build_plot_table``, ``tree_tile``,
or the runner's stages and ``main`` (scripts/t6b_run.py), on T6b's synthetic world in temporary
folders. Nothing here reads or writes the flash drive.
"""

import csv
import hashlib
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest
import rasterio
from pyproj import Transformer
from test_t5_layer import _write_vat
from test_t6b_layers import BIG, CANOPY, _scanfi_source, world  # noqa: F401
from test_t6b_us_half_runner import _small_tiles, runner  # noqa: F401

from forager_forecast.grid import CELL_SIZE_M, GEOGRAPHIC_CRS, GRID_CRS
from forager_forecast.t5_layer import FLAG_NOT_AVAILABLE, FLAG_SCANFI, FLAG_TREEMAP
from forager_forecast.t6b_layers import SCANFI_LAYERS
from forager_forecast.t6b_run import append_line, read_lines

# The band layout this dispatch builds, written out by hand rather than imported, so a change to
# the code's list cannot change what this test expects. T5's eight bands first, in T5's order,
# so the plot table's existing columns keep their meaning; then tier A, tier B, and the total.
T5_BANDS = ("Pseudotsuga", "Tsuga", "Picea", "Abies", "Pinus", "Quercus", "conifer", "broadleaf")
TIER_A = ("Larix", "Betula", "Populus", "Alnus", "Lithocarpus", "Chrysolepis", "Arbutus")
TIER_B = ("Fagus", "Carya", "Tilia", "Ostrya", "Carpinus")
EXPECTED_BANDS = (*T5_BANDS, *TIER_A, *TIER_B, "ecm_hosts")
EXPECTED_GENERA = (*T5_BANDS[:6], *TIER_A, *TIER_B)
EXPECTED_TREE_BANDS = ("total_cover_pct", "valid_fraction", "source",
                       *(f"share_{b}" for b in EXPECTED_BANDS))  # fmt: skip
OLD_TREE_BANDS = ("total_cover_pct", "valid_fraction", "source",
                  *(f"share_{b}" for b in T5_BANDS))  # fmt: skip

# Four plots on the same TreeMap raster as T6b's world, now holding every new genus. Plot 4 also
# holds western redcedar, a conifer that is not an ectomycorrhizal host, so the total must fall
# short of the plot's whole cover there. Genus strings are the tree table's own: tanoak is
# "Lithocarpus" in TreeMap 2023 (9,999 rows; "Notholithocarpus" has none, counted 2026-10-15).
HG_TREES = {
    1: [("202", "Pseudotsuga menziesii", 20.0, 60.0), ("073", "Larix occidentalis", 14.0, 20.0)],
    2: [
        ("263", "Tsuga heterophylla", 14.0, 40.0),
        ("351", "Alnus rubra", 12.0, 30.0),
        ("631", "Lithocarpus densiflorus", 10.0, 20.0),
    ],
    3: [("263", "Tsuga heterophylla", 3.0, 300.0)],  # canopy, no split
    4: [
        ("122", "Pinus ponderosa", 16.0, 50.0),
        ("746", "Populus tremuloides", 9.0, 30.0),
        ("375", "Betula papyrifera", 8.0, 20.0),
        ("361", "Arbutus menziesii", 10.0, 10.0),
        ("431", "Chrysolepis chrysophylla", 7.0, 10.0),
        ("407", "Carya ovata", 11.0, 25.0),
        ("531", "Fagus grandifolia", 12.0, 10.0),
        ("951", "Tilia americana", 10.0, 10.0),
        ("701", "Ostrya virginiana", 6.0, 10.0),
        ("391", "Carpinus caroliniana", 6.0, 10.0),
        ("242", "Thuja plicata", 15.0, 20.0),
    ],
}


def _write_hg_zip(path):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["TM_ID", "STATUSCD", "TPA_UNADJ", "SPCD", "SCIENTIFIC_NAME", "DIA"])
    for tm, rows in HG_TREES.items():
        for spcd, sci, dia, tpa in rows:
            w.writerow([tm, 1, tpa, int(spcd), sci, dia])
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Data/TreeMap2023_CONUS_Tree_Table.csv", "﻿" + buf.getvalue())


@pytest.fixture
def hg_table(tmp_path):
    from forager_forecast.t6b_layers import build_plot_table

    _write_hg_zip(tmp_path / "trees_hg.zip")
    _write_vat(tmp_path / "hg.vat.dbf", CANOPY)
    info = build_plot_table(tmp_path / "trees_hg.zip", tmp_path / "hg.vat.dbf",
                            tmp_path / "plots_hg.npz")  # fmt: skip
    return tmp_path / "plots_hg.npz", info


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --- The band layout -----------------------------------------------------------------------------


def test_the_plot_table_carries_every_new_genus_and_the_total_without_moving_t5s_columns(
    hg_table,
):
    """Stop condition of the dispatch: no existing column may change its meaning."""
    from forager_forecast.crown_cover import Tree, plot_cover

    path, info = hg_table
    with np.load(path) as z:
        assert "bands" in z.files, "the plot table does not record its band list"
        assert tuple(z["bands"].tolist()) == EXPECTED_BANDS
        table = z["table"]
    assert table.shape == (4, 2 + len(EXPECTED_BANDS))
    col = {b: 1 + k for k, b in enumerate(EXPECTED_BANDS)}
    for k, tm in enumerate((1, 2, 3, 4)):
        # T5's eight bands, the tree-list total and CANOPYPCT are where they were, with T5's own
        # values (T5's plot_cover, T5's list).
        t5 = plot_cover([Tree(int(s), sci.split()[0], dia, tpa, True)
                         for s, sci, dia, tpa in HG_TREES[tm]],
                        classify_unlisted_by_spcd=True)  # fmt: skip
        assert table[k, 0] == t5.total
        assert table[k, 1:9].tolist() == [t5.by_band[b] for b in T5_BANDS]
        assert table[k, -1] == CANOPY[tm]
        present = {sci.split()[0] for _, sci, dia, _ in HG_TREES[tm] if dia >= 5.0}
        for genus in (*TIER_A, *TIER_B):
            assert (table[k, col[genus]] > 0) == (genus in present), (tm, genus)
        genera_sum = sum(table[k, col[g]] for g in EXPECTED_GENERA)
        assert table[k, col["ecm_hosts"]] == pytest.approx(genera_sum, rel=1e-12, abs=1e-12)
    # Plot 1 is all host trees; plot 4 holds redcedar, which is in the conifer total only.
    assert table[0, col["ecm_hosts"]] == pytest.approx(table[0, 0])
    assert table[3, col["ecm_hosts"]] < table[3, 0] - 1.0
    assert table[3, col["conifer"]] + table[3, col["broadleaf"]] == pytest.approx(table[3, 0])
    assert info["band_layout"]


def _tile_with_hg(world, plots, out):  # noqa: F811
    from forager_forecast.t6b_layers import fetch_scanfi_super, tree_tile

    d = world["d"]
    super_dir = out / "scanfi_super"
    fetch_scanfi_super(BIG.window, super_dir, source_for=_scanfi_source(world))
    return tree_tile(BIG, d / "mask.tif", d / "treemap.tif", plots, super_dir, d / "nalcms.tif",
                     out)  # fmt: skip


def test_a_tree_tile_has_the_new_bands_canada_flags_them_not_available(world, hg_table, tmp_path):  # noqa: F811
    from forager_forecast.t6b_mask import SIDE_CA, cells_in_study, read_mask

    result = _tile_with_hg(world, hg_table[0], tmp_path)
    with rasterio.open(tmp_path / f"trees_{BIG.key}.tif") as ds:
        assert tuple(ds.descriptions) == EXPECTED_TREE_BANDS, "the tile lacks the new bands"
        assert ds.tags()["band_layout"] == result["band_layout"]
        v = {n: ds.read(k + 1) for k, n in enumerate(ds.descriptions)}
    with rasterio.open(tmp_path / f"trees_flags_{BIG.key}.tif") as ds:
        assert tuple(ds.descriptions) == tuple(f"flag_{b}" for b in EXPECTED_BANDS)
        f = {n: ds.read(k + 1) for k, n in enumerate(ds.descriptions)}
    study, side = cells_in_study(BIG.window, *read_mask(world["d"] / "mask.tif", BIG.window))
    ca = study & (side == SIDE_CA)
    us = study & ~ca
    assert ca.any() and us.any()
    for band in (*TIER_A, *TIER_B, "ecm_hosts"):
        # Canada: SCANFI folds these into broadleaf (or, for the total, mixes hosts and
        # non-hosts), so they are not available there (D85, RECORD -1033 item 2).
        assert (f[f"flag_{band}"][ca] == FLAG_NOT_AVAILABLE).all(), band
        assert np.isnan(v[f"share_{band}"][ca]).all(), band
    assert (f["flag_Pseudotsuga"][ca & np.isfinite(v["share_Pseudotsuga"])] == FLAG_SCANFI).all()
    assert np.isfinite(v["share_Pseudotsuga"][ca]).any()
    # US: each genus in the synthetic plots shows up, and the total is the sum of its genera.
    for band in ("Larix", "Alnus", "Lithocarpus", "Populus", "Betula", "Arbutus", "Chrysolepis",
                 "Carya", "Fagus", "Tilia", "Ostrya", "Carpinus"):  # fmt: skip
        has = us & np.isfinite(v[f"share_{band}"])
        assert (v[f"share_{band}"][has] > 0).any(), band
        assert (f[f"flag_{band}"][has] == FLAG_TREEMAP).all(), band
    total = v["share_ecm_hosts"]
    summed = sum(np.nan_to_num(v[f"share_{g}"]) for g in EXPECTED_GENERA)
    has = us & np.isfinite(total)
    assert has.sum() > 100
    np.testing.assert_allclose(total[has], summed[has], rtol=1e-5, atol=1e-6)
    assert (total[has] <= 1.0 + 1e-6).all()


def test_a_plot_table_of_another_band_layout_is_refused(tmp_path):
    from forager_forecast.t6b_layers import load_plot_table

    old = tmp_path / "old_plots.npz"
    np.savez(old, ids=np.array([1, 2, 3, 4]), table=np.zeros((4, 10)))
    with pytest.raises(ValueError, match="band"):
        load_plot_table(old)


# --- T5 stays as it is ---------------------------------------------------------------------------


def test_t5s_genus_list_and_its_cover_split_are_unchanged():
    """RECORD -1033 item 6: a T6b-only list. A guard: it passes before and after this change by
    design, and its revert check is an edit to T5's list."""
    from forager_forecast import crown_cover, t5_layer
    from forager_forecast.crown_cover import Tree, plot_cover

    assert crown_cover.HOST_GENERA == T5_BANDS[:6]
    assert crown_cover.BANDS == T5_BANDS
    assert t5_layer.BANDS == T5_BANDS
    listed = crown_cover.BROADLEAF_GENERA | {"Pinus"}
    c = plot_cover([Tree(int(s), sci.split()[0], dia, tpa, True)
                    for s, sci, dia, tpa in HG_TREES[4] if sci.split()[0] in listed])  # fmt: skip
    assert tuple(c.by_band) == T5_BANDS


# --- The runner: F1, the trees-only supersede, US halves, free space, the PNW box ----------------


def _old_layout_files(window, key, out_dir, names):
    """Files as the run wrote them before this change: eleven value bands, no layout tag."""
    from forager_forecast.t6b_layers import _write_tif

    v_name, f_name = names
    h, w = window.height, window.width
    sha_v = _write_tif(out_dir / v_name, window,
                       {b: np.full((h, w), 0.25) for b in OLD_TREE_BANDS}, "float32",
                       {"tile": key}, nodata=float("nan"))  # fmt: skip
    flags = {f"flag_{b}": np.ones((h, w)) for b in T5_BANDS}
    sha_f = _write_tif(out_dir / f_name, window, flags, "uint8", {"tile": key})
    return {v_name: sha_v, f_name: sha_f}


def _one_tile(runner, world, want):  # noqa: F811
    tiles = _small_tiles(world)
    t = next(t for t in tiles if want(t))
    runner.TREE_N = 4
    (runner.T6B / "tiles_trees.json").write_text(json.dumps([t]))
    from forager_forecast.t6b_layers import Tile

    return Tile(t["i"], t["j"], t["n"])


def _bystanders(runner):  # noqa: F811
    """A soil tile, a SCANFI layer tile and the manifest so far: what a trees supersede must
    leave exactly where and as they are."""
    soil = runner.TILES / "soil" / "soil_2048_0_0.tif"
    soil.parent.mkdir(parents=True, exist_ok=True)
    soil.write_bytes(b"soil tile, not a tree output")
    layer = runner.SCANFI_LAYER_TILES / "scanfi_broadleaf_4_0_0.npz"
    layer.parent.mkdir(parents=True, exist_ok=True)
    layer.write_bytes(b"scanfi layer tile, not a tree output")
    append_line(runner.MANIFEST, {"kind": "unit", "layer": "soil", "unit": "2048_0_0",
                                  "status": "ok", "files": {soil.name: _sha(soil)}})  # fmt: skip
    return {soil: _sha(soil), layer: _sha(layer)}, runner.MANIFEST.read_text()


def test_f1_a_tile_built_with_the_old_genus_list_is_rebuilt_not_counted_done(runner, world):  # noqa: F811
    t = _one_tile(runner, world, lambda t: not t["canada"])
    names = (f"trees_{t.key}.tif", f"trees_flags_{t.key}.tif")
    files = _old_layout_files(t.window, t.key, runner.TILES / "trees", names)
    append_line(runner.MANIFEST, {"kind": "unit", "layer": "trees", "unit": t.key,
                                  "status": "ok", "files": files})  # fmt: skip

    summary = runner.stage_trees(None, 1)
    assert summary["units_done_before"] == 0, "the old-layout tile was counted done (F1)"
    assert summary["units_ok"] == 1
    line = [e for e in read_lines(runner.MANIFEST) if e.get("kind") == "unit"][-1]
    assert line["unit"] == t.key and line["band_layout"]
    with rasterio.open(runner.TILES / "trees" / names[0]) as ds:
        assert tuple(ds.descriptions) == EXPECTED_TREE_BANDS
        assert ds.tags()["band_layout"] == line["band_layout"]
    # Done now under the current layout: a second section does not redo it.
    assert runner.stage_trees(None, 1)["units_done_before"] == 1


def test_the_trees_only_supersede_keeps_the_old_tile_and_leaves_soil_scanfi_and_manifest(
    runner,  # noqa: F811
    world,  # noqa: F811
):
    t = _one_tile(runner, world, lambda t: not t["canada"])
    names = (f"trees_{t.key}.tif", f"trees_flags_{t.key}.tif")
    files = _old_layout_files(t.window, t.key, runner.TILES / "trees", names)
    append_line(runner.MANIFEST, {"kind": "unit", "layer": "trees", "unit": t.key,
                                  "status": "ok", "files": files})  # fmt: skip
    bystanders, manifest_before = _bystanders(runner)

    runner.stage_trees(None, 1)
    kept = {p.name: _sha(p) for p in (runner.T6B / "superseded").rglob("trees_*.tif")}
    assert kept == files, "the old tile was not kept in a superseded folder"
    for name in names:
        moved = next((runner.T6B / "superseded").rglob(name))
        assert moved.parent.parent.name == "tiles" and moved.parent.name == "trees"
        assert moved.parents[2].name.endswith("trees")  # a dated, trees-only folder
    for path, sha in bystanders.items():
        assert path.exists() and _sha(path) == sha
    assert runner.MANIFEST.read_text().startswith(manifest_before)  # appended to, never moved
    lines = read_lines(runner.MANIFEST)
    moves = [e for e in lines if e.get("superseded")]
    assert moves and set(moves[0]["superseded"]) == set(names)
    assert not list((runner.T6B / "superseded").rglob("soil_*")) and not list(
        (runner.T6B / "superseded").rglob("scanfi_*")
    )


def test_an_old_layout_us_half_is_rebuilt_as_a_new_file_and_the_old_one_kept(runner, world):  # noqa: F811
    from forager_forecast.t6b_layers import us_half_names

    t = _one_tile(runner, world, lambda t: t["canada"] and t["us"])
    names = us_half_names(t.key)
    files = _old_layout_files(t.window, t.key, runner.TILES_US_HALF, names)
    append_line(runner.MANIFEST, {"kind": "unit", "layer": "trees-us-half",
                                  "unit": f"us-half:{t.key}", "status": "ok",
                                  "files": files})  # fmt: skip
    assert runner.stage_trees(None, 1)["units_total"] == 0  # still waits for SCANFI (D118)

    summary = runner.stage_trees_us_half(None, 1)
    assert summary["units_done_before"] == 0, "the old-layout US half was counted done (F1)"
    assert summary["units_ok"] == 1
    with rasterio.open(runner.TILES_US_HALF / names[0]) as ds:
        assert tuple(ds.descriptions) == EXPECTED_TREE_BANDS
    kept = {p.name: _sha(p) for p in (runner.T6B / "superseded").rglob("trees_*us_half_*.tif")}
    assert kept == files


def test_f2_the_plot_table_is_rebuilt_when_the_genus_list_changes(runner, world, tmp_path):  # noqa: F811
    d = world["d"]
    treemap = tmp_path / "treemap_zip"
    treemap.mkdir()
    (treemap / "RDS-2026-0038.zip").symlink_to(d / "trees.zip")
    (treemap / "TreeMap2023_CONUS.tif.vat.dbf").symlink_to(d / "treemap.tif.vat.dbf")
    runner.TREEMAP = treemap
    runner.PLOTS = runner.T6B / "plots.npz"
    # A table as the run built it: the old ten columns, under today's rulings string.
    np.savez(runner.PLOTS, ids=np.array([1, 2, 3, 4]), table=np.zeros((4, 10)))
    old_sha = _sha(runner.PLOTS)
    (runner.T6B / "plots.json").write_text(json.dumps({"rulings": runner.PLOT_TABLE_RULINGS}))

    runner.stage_plots()
    with np.load(runner.PLOTS) as z:
        assert z["table"].shape == (4, 2 + len(EXPECTED_BANDS)), "the old table was reused (F2)"
        assert tuple(z["bands"].tolist()) == EXPECTED_BANDS
    meta = json.loads((runner.T6B / "plots.json").read_text())
    assert meta["band_layout"] and tuple(meta["bands"]) == EXPECTED_BANDS
    kept = [p for p in (runner.T6B / "superseded").rglob("plots.npz")]
    assert [_sha(p) for p in kept] == [old_sha]
    new_sha = _sha(runner.PLOTS)
    runner.stage_plots()  # the same layout again: not rebuilt
    assert _sha(runner.PLOTS) == new_sha


@pytest.mark.parametrize("stage", ["trees", "trees-us-half"])
def test_a_tree_tile_is_not_started_without_free_space(runner, world, monkeypatch, stage):  # noqa: F811
    if stage == "trees":
        _one_tile(runner, world, lambda t: not t["canada"])
    else:
        _one_tile(runner, world, lambda t: t["canada"] and t["us"])
    low = shutil._ntuple_diskusage(10**9, 10**9, 1000)
    monkeypatch.setattr(shutil, "disk_usage", lambda p: low)
    summary = (runner.stage_trees(None, 1) if stage == "trees"
               else runner.stage_trees_us_half(None, 1))  # fmt: skip
    assert summary["units_ok"] == 0 and summary["units_failed"] == 0
    assert "free space" in summary["stopped"]
    assert not [e for e in read_lines(runner.MANIFEST) if e.get("kind") == "unit"]
    assert not list(runner.TILES.rglob("trees_*.tif"))


def _centre_lonlat(tile):
    x = tile.window.left + 2 * CELL_SIZE_M - CELL_SIZE_M / 2
    y = tile.window.top - 2 * CELL_SIZE_M + CELL_SIZE_M / 2
    lon, lat = Transformer.from_crs(GRID_CRS, GEOGRAPHIC_CRS, always_xy=True).transform(x, y)
    return float(lon), float(lat)


def test_the_box_option_runs_only_the_tiles_with_a_study_cell_in_the_box(
    runner,  # noqa: F811
    world,  # noqa: F811
    monkeypatch,
):
    from forager_forecast.t6b_layers import Tile

    tiles = _small_tiles(world)
    us_only = [t for t in tiles if not t["canada"]]
    assert len(us_only) >= 2
    runner.TREE_N = 4
    (runner.T6B / "tiles_trees.json").write_text(json.dumps(tiles))
    chosen = Tile(us_only[0]["i"], us_only[0]["j"], 4)
    lon, lat = _centre_lonlat(chosen)  # one cell centre of the chosen tile, nothing else
    box = f"{lat - 0.0003},{lat + 0.0003},{lon - 0.0003},{lon + 0.0003}"
    monkeypatch.setattr(runner, "DRIVE", runner.T6B)
    monkeypatch.setattr(runner, "commit_progress", lambda summaries, evidence: None)
    monkeypatch.setattr(sys, "argv", ["t6b_run.py", "--until", "23:59", "--stages", "trees",
                                      "--workers", "1", "--box", box])  # fmt: skip
    runner.main()
    done = [e["unit"] for e in read_lines(runner.MANIFEST)
            if e.get("kind") == "unit" and e.get("layer") == "trees"]  # fmt: skip
    assert done == [chosen.key]


def test_a_stale_whole_tile_is_moved_aside_without_its_current_us_half(runner, world):  # noqa: F811
    """A border tile whose US half is already current and whose whole tile is of the old layout:
    only the whole tile is superseded, and the new whole tile is filled from the US half (D119)."""
    from forager_forecast.t6b_layers import WHOLE_STATE, scanfi_layer_tile, us_half_names

    t = _one_tile(runner, world, lambda t: t["canada"] and t["us"])
    assert runner.stage_trees_us_half(None, 1)["units_ok"] == 1
    half = {n: _sha(runner.TILES_US_HALF / n) for n in us_half_names(t.key)}
    names = (f"trees_{t.key}.tif", f"trees_flags_{t.key}.tif")
    files = _old_layout_files(t.window, t.key, runner.TILES / "trees", names)
    append_line(runner.MANIFEST, {"kind": "unit", "layer": "trees", "unit": t.key,
                                  "status": "ok", "files": files})  # fmt: skip
    d = world["d"]
    for layer in SCANFI_LAYERS:
        scanfi_layer_tile(t, d / f"scanfi_full_{layer}.tif", layer, d / "mask.tif",
                          d / "nalcms.tif", runner.SCANFI_LAYER_TILES)  # fmt: skip

    assert runner.stage_trees(None, 1)["units_ok"] == 1
    line = [e for e in read_lines(runner.MANIFEST) if e.get("kind") == "unit"][-1]
    assert line["tile_state"] == WHOLE_STATE
    assert {n: _sha(runner.TILES_US_HALF / n) for n in half} == half  # left in place, unchanged
    kept = {p.name: _sha(p) for p in (runner.T6B / "superseded").rglob("trees_*.tif")}
    assert kept == files

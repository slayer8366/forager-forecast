"""D119 through the runner's real entry points (scripts/t6b_run.py), on T6b's synthetic world.

A tile with Canadian cells waits for SCANFI in the trees stage (D118); the trees-us-half stage
computes its US cells now and says so in the manifest; once the SCANFI layers are in, the trees
stage fills the Canadian cells from the US half without touching the US-half file.
"""

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from test_t6b_layers import BIG, N_BIG, world  # noqa: F401

from forager_forecast.t6b_layers import SCANFI_LAYERS, US_HALF_STATE, WHOLE_STATE
from forager_forecast.t6b_run import read_lines

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "t6b_run.py"


@pytest.fixture
def runner(world, tmp_path, monkeypatch):  # noqa: F811
    spec = importlib.util.spec_from_file_location("t6b_run_script", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    d = world["d"]
    t6b = tmp_path / "t6b"
    t6b.mkdir()
    treemap = tmp_path / "treemap"
    treemap.mkdir()
    (treemap / "TreeMap2023_CONUS.tif").symlink_to(d / "treemap.tif")
    with rasterio.open(d / "mask.tif") as ds:
        b = ds.bounds
    (t6b / "mask.json").write_text(json.dumps({"window": [int(b.left), int(b.bottom),
                                                          int(b.right), int(b.top)]}))  # fmt: skip
    tiles = t6b / "tiles"
    for name, value in {
        "T6B": t6b, "MASK": d / "mask.tif", "MASK_INFO": t6b / "mask.json",
        "PLOTS": d / "plots.npz", "TILES": tiles, "TILES_US_HALF": tiles / "trees_us_half",
        "MANIFEST": t6b / "manifest.jsonl", "PAUSE": t6b / "PAUSE", "TREEMAP": treemap,
        "NALCMS": d / "nalcms.tif", "SCANFI_LAYER_TILES": t6b / "scanfi_layers",
        "NATIVE_SCANFI": t6b / "native" / "scanfi", "TREE_N": N_BIG,
    }.items():  # fmt: skip
        monkeypatch.setattr(mod, name, value)
    return mod


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_the_us_half_runs_now_says_so_and_is_filled_later_without_change(runner, world):  # noqa: F811
    key = BIG.key
    listed = {t["key"]: t for t in runner.tile_list(N_BIG, "trees")}
    assert listed[key]["canada"]
    # The synthetic sources cover BIG only: the runner's cached tile list is cut to it.
    (runner.T6B / "tiles_trees.json").write_text(json.dumps([listed[key]]))

    trees = runner.stage_trees(None, 1)
    assert trees["units_total"] == 0  # the border tile waits for SCANFI (D118)

    half = runner.stage_trees_us_half(None, 1)
    assert half["units_ok"] == 1
    line = [e for e in read_lines(runner.MANIFEST) if e.get("kind") == "unit"][-1]
    assert line["unit"] == f"us-half:{key}" and line["layer"] == "trees-us-half"
    assert line["tile_state"] == US_HALF_STATE
    assert runner.us_half_done(key)
    files = {n: _sha(runner.TILES_US_HALF / n) for n in line["files"]}
    assert files == line["files"]
    assert not (runner.TILES / "trees" / f"trees_{key}.tif").exists()

    again = runner.stage_trees_us_half(None, 1)
    assert again["units_done_now"] == 0  # done once, not redone

    d = world["d"]
    from forager_forecast.t6b_layers import scanfi_layer_tile

    for layer in SCANFI_LAYERS:
        scanfi_layer_tile(BIG, d / f"scanfi_full_{layer}.tif", layer, d / "mask.tif",
                          d / "nalcms.tif", runner.SCANFI_LAYER_TILES)  # fmt: skip
    filled = runner.stage_trees(None, 1)
    assert filled["units_ok"] == 1
    line = [e for e in read_lines(runner.MANIFEST) if e.get("kind") == "unit"][-1]
    assert line["unit"] == key and line["tile_state"] == WHOLE_STATE
    v_name = f"trees_us_half_{key}.tif"
    assert line["us_cells_from"] == {v_name: files[v_name]}
    assert {n: _sha(runner.TILES_US_HALF / n) for n in files} == files

    with rasterio.open(runner.TILES / "trees" / f"trees_{key}.tif") as ds:
        whole = ds.read()
    assert np.isfinite(whole[0]).sum() > 100
    assert runner.stage_trees_us_half(None, 1)["units_total"] == 0  # a whole tile is not offered
    import shutil

    shutil.rmtree(runner.SCANFI_LAYER_TILES)  # even with its layer files gone
    assert runner.stage_trees_us_half(None, 1)["units_total"] == 0


def test_us_half_tiles_must_be_tiles_with_canadian_cells(runner):
    with pytest.raises(SystemExit, match="not tiles with Canadian cells"):
        runner.stage_trees_us_half(None, 1, {"16_0_0"})


# Review F1 (RECORD -786): a tile with Canadian cells only has no US half. It must never get a
# us-half line, and an "ok" line with no files must never count as a done US half, or the trees
# stage would try to fill a file that does not exist once SCANFI is in.


def _canada_only_small_tile(world):  # noqa: F811
    from forager_forecast.t6b_layers import Tile
    from forager_forecast.t6b_mask import SIDE_CA, SIDE_US, cells_in_study, read_mask

    n = 4
    for di in range(4):
        for dj in range(4):
            t = Tile(BIG.i * 4 + di, BIG.j * 4 + dj, n)
            study, side = cells_in_study(t.window, *read_mask(world["d"] / "mask.tif", t.window))
            if (side == SIDE_CA).any() and not (side == SIDE_US).any():
                return t
    raise AssertionError("no Canada-only small tile in the synthetic world")


def test_the_us_half_stage_offers_only_tiles_with_both_sides(runner, world):  # noqa: F811
    t = _canada_only_small_tile(world)
    runner.TREE_N = t.n
    (runner.T6B / "tiles_trees.json").write_text(
        json.dumps([{"key": t.key, "i": t.i, "j": t.j, "n": t.n, "canada": True}])
    )
    summary = runner.stage_trees_us_half(None, 1)
    assert summary["units_total"] == 0
    assert not [e for e in read_lines(runner.MANIFEST) if e.get("kind") == "unit"]


def test_an_ok_us_half_line_without_files_is_not_a_done_us_half(runner):
    from forager_forecast.t6b_run import append_line

    line = {"kind": "unit", "layer": "trees-us-half", "unit": "us-half:16_0_0", "status": "ok",
            "files": {}}  # fmt: skip
    append_line(runner.MANIFEST, line)
    assert not runner.us_half_done("16_0_0")


def test_a_canada_only_tile_goes_from_waiting_to_a_whole_tile(runner, world):  # noqa: F811
    from forager_forecast.t6b_layers import scanfi_layer_tile

    t = _canada_only_small_tile(world)
    runner.TREE_N = t.n
    (runner.T6B / "tiles_trees.json").write_text(
        json.dumps([{"key": t.key, "i": t.i, "j": t.j, "n": t.n, "canada": True}])
    )
    assert runner.stage_trees(None, 1)["units_total"] == 0  # waits for SCANFI
    runner.stage_trees_us_half(None, 1)
    d = world["d"]
    for layer in SCANFI_LAYERS:
        scanfi_layer_tile(t, d / f"scanfi_full_{layer}.tif", layer, d / "mask.tif",
                          d / "nalcms.tif", runner.SCANFI_LAYER_TILES)  # fmt: skip
    whole = runner.stage_trees(None, 1)
    assert whole["units_ok"] == 1
    line = [e for e in read_lines(runner.MANIFEST) if e.get("kind") == "unit"][-1]
    assert line["unit"] == t.key and "us_cells_from" not in line
    assert (runner.TILES / "trees" / f"trees_{t.key}.tif").exists()


# Forager RECORD -828: the PNW box's 8 Canadian tiles first. A tile filter for the scanfi-layers
# and trees stages. A filtered scanfi-layers run must not delete a whole layer file: the runner
# deletes a layer once every unit *in the list it was given* is done, and with a filtered list
# that is after the filtered tiles, leaving the rest of the continent to download it again.


def _small_tiles(world):  # noqa: F811
    from forager_forecast.t6b_layers import Tile
    from forager_forecast.t6b_mask import SIDE_CA, SIDE_US, cells_in_study, read_mask

    out = []
    for di in range(4):
        for dj in range(4):
            t = Tile(BIG.i * 4 + di, BIG.j * 4 + dj, 4)
            study, side = cells_in_study(t.window, *read_mask(world["d"] / "mask.tif", t.window))
            if study.any():
                out.append({"key": t.key, "i": t.i, "j": t.j, "n": t.n,
                            "canada": bool((side == SIDE_CA).any()),
                            "us": bool((side == SIDE_US).any())})  # fmt: skip
    return out


def _whole_layers_on_drive(runner, world, tmp_path):  # noqa: F811
    whole, requests = tmp_path / "scanfi_whole", tmp_path / "requests"
    whole.mkdir()
    requests.mkdir()
    for layer in SCANFI_LAYERS:
        (whole / f"{layer}.tif").symlink_to(world["d"] / f"scanfi_full_{layer}.tif")
        (requests / f"scanfi_whole_{layer}.request.json").write_text("{}\n")
    runner.SCANFI_WHOLE, runner.REQUESTS = whole, requests
    return whole


@pytest.mark.parametrize("filtered", [True, False])
def test_a_tile_filter_runs_only_those_tiles_and_keeps_the_whole_layers(
    runner,
    world,  # noqa: F811
    tmp_path,
    filtered,
):
    tiles = _small_tiles(world)
    canadian = [t for t in tiles if t["canada"]]
    us_only = [t for t in tiles if not t["canada"]]
    assert len(canadian) >= 2 and us_only
    chosen = canadian[0]["key"]
    runner.TREE_N = 4
    (runner.T6B / "tiles_trees.json").write_text(json.dumps(tiles))
    whole = _whole_layers_on_drive(runner, world, tmp_path)
    if not filtered:
        # Positive control for the trap: an unfiltered run given only this tile deletes the
        # whole layers once it is done, as the run does once every Canadian tile is done.
        (runner.T6B / "tiles_trees.json").write_text(
            json.dumps([t for t in tiles if t["key"] == chosen])
        )
        s = runner.stage_scanfi_layers(None, 1)
        assert s["units_ok"] == len(SCANFI_LAYERS)
        assert not any((whole / f"{layer}.tif").exists() for layer in SCANFI_LAYERS)
        return
    s = runner.stage_scanfi_layers(None, 1, only_tiles={chosen})
    assert s["units_total"] == len(SCANFI_LAYERS) and s["units_ok"] == len(SCANFI_LAYERS)
    lines = read_lines(runner.MANIFEST)
    assert {e["unit"].split(":")[1] for e in lines if e.get("kind") == "unit"} == {chosen}
    assert not [e for e in lines if e.get("kind") == "cleanup"]
    assert all((whole / f"{layer}.tif").exists() for layer in SCANFI_LAYERS)
    other = canadian[1]["key"]
    assert not list(runner.SCANFI_LAYER_TILES.glob(f"*_{other}.npz"))

    trees = runner.stage_trees(None, 1, only_tiles={chosen})
    assert trees["units_total"] == 1 and trees["units_ok"] == 1
    done = [e["unit"] for e in read_lines(runner.MANIFEST)
            if e.get("kind") == "unit" and e.get("layer") == "trees"]  # fmt: skip
    assert done == [chosen]  # the US-only tiles waiting in the list were not offered
    assert (runner.TILES / "trees" / f"trees_{chosen}.tif").exists()


def test_a_tile_filter_must_name_tiles_with_canadian_cells(runner, world):  # noqa: F811
    runner.TREE_N = 4
    (runner.T6B / "tiles_trees.json").write_text(json.dumps(_small_tiles(world)))
    with pytest.raises(SystemExit, match="not tiles with Canadian cells"):
        runner.stage_scanfi_layers(None, 1, only_tiles={"4_0_0"})

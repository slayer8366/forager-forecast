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

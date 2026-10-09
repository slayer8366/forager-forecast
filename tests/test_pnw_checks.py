"""Positive control for the PNW ten-cell check's independent host-tree recompute: on T6b's
synthetic world it must agree with the pipeline within the ten-cell rule's tolerances, so a
FAIL on real data cannot be the checker's own arithmetic. Then a negative control."""

import importlib.util
import math
from pathlib import Path

import numpy as np
import rasterio
from test_t6b_layers import BIG, _trees_by_layer, world  # noqa: F401

from forager_forecast.grid import CELL_SIZE_M

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "pnw_checks.py"


def _checks():
    spec = importlib.util.spec_from_file_location("pnw_checks_script", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_independent_tree_recompute_agrees_with_the_pipeline(world, tmp_path):  # noqa: F811
    mod = _checks()
    d = world["d"]
    _trees_by_layer(world, [BIG], tmp_path)
    with rasterio.open(tmp_path / f"trees_{BIG.key}.tif") as ds:
        names = list(ds.descriptions)
        v = {n: ds.read(k + 1) for k, n in enumerate(names)}
    us = np.argwhere((v["source"] == 1) & (v["valid_fraction"] > 0))
    rng = np.random.default_rng(20261009)
    picks = us[rng.choice(len(us), 12, replace=False)]
    with_share = 0
    for r, c in picks:
        col = BIG.window.left // CELL_SIZE_M + int(c)
        row = BIG.window.top // CELL_SIZE_M - 1 - int(r)
        ind = mod._tree_cell(col, row, d / "treemap.tif", d / "treemap.tif.vat.dbf",
                             d / "trees.zip", d / "nalcms.tif", d / "mask.tif")  # fmt: skip
        assert abs(ind["valid_fraction"] - v["valid_fraction"][r, c]) <= 0.001
        if ind["valid_fraction"] >= 0.5:
            assert abs(ind["total_cover_pct"] - v["total_cover_pct"][r, c]) <= 0.1
            for g in ("Pseudotsuga", "Tsuga", "Quercus", "Pinus", "Picea", "conifer", "broadleaf"):
                mv = float(v[f"share_{g}"][r, c])
                if math.isfinite(mv):
                    with_share += 1
                    assert ind["shares"][g] is not None, (g, mv, ind, r, c)
                    assert abs(ind["shares"][g] - mv) <= 0.001, (g, ind["shares"][g], mv)
    assert with_share > 10


def test_the_recompute_sees_a_changed_canopy(world, tmp_path):  # noqa: F811
    """Negative control: with every CANOPYPCT doubled the recompute no longer matches."""
    from test_t5_layer import _write_vat
    from test_t6b_layers import CANOPY

    mod = _checks()
    d = world["d"]
    _trees_by_layer(world, [BIG], tmp_path)
    _write_vat(tmp_path / "vat.dbf", {k: min(2 * c, 100.0) for k, c in CANOPY.items()})
    with rasterio.open(tmp_path / f"trees_{BIG.key}.tif") as ds:
        names = list(ds.descriptions)
        cover = ds.read(names.index("total_cover_pct") + 1)
        source = ds.read(names.index("source") + 1)
    r, c = np.argwhere(np.isfinite(cover) & (cover > 20) & (source == 1))[0]
    col = BIG.window.left // CELL_SIZE_M + int(c)
    row = BIG.window.top // CELL_SIZE_M - 1 - int(r)
    ind = mod._tree_cell(col, row, d / "treemap.tif", tmp_path / "vat.dbf", d / "trees.zip",
                         d / "nalcms.tif", d / "mask.tif")  # fmt: skip
    assert abs(ind["total_cover_pct"] - cover[r, c]) > 0.1

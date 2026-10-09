"""The PNW checks, as fixed in docs/audits/2026-10-09-pnw-monday/check-rules.md before any value
was read (Forager RECORD -772, -774). One check at a time, under the cap:

    systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0 \
        nice -n 10 .venv/bin/python scripts/pnw_checks.py CHECK [--out JSON]

CHECK: edges-trees, edges-soil, ten-cells, seam. Exits 1 if any comparison fails. Writes only
under forecast-data/pnw/checks/ and the --out file; never into t6b/.

``ten-cells`` is independent of the pipeline on purpose (ten-cell rule): it imports nothing from
forager_forecast except the published Bechtold 2004 tables and T5's genus lists
(crown_cover), parses the TreeMap attribute table and tree table itself, clips each native pixel
against the master cell's quad itself, and samples soil itself as scripts/t4_ten_cells.py does.
"""

import argparse
import csv
import io
import json
import math
import resource
import struct
import sys
import time
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

DRIVE = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data")
T6B = DRIVE / "t6b"
MASK = T6B / "mask.tif"
TILES = T6B / "tiles"
NALCMS = T6B / "sources" / "nalcms" / "NA_NALCMS_landcover_2020v2_30m.tif"
TREEMAP = DRIVE / "t5" / "treemap2023"
PLOTS = T6B / "plots.npz"
OUT = DRIVE / "pnw"
CHECKS = OUT / "checks"
REPO = Path(__file__).resolve().parent.parent
RULE_DIR = REPO / "docs" / "audits" / "2026-10-09-pnw-monday"
HALF = 32  # a 64 x 64 window around each point

TREE_CORNERS = [(-8192, 2048), (-8192, 3072), (-8192, 4096), (-7168, 1024), (-7168, 2048),
                (-7168, 3072), (-7168, 4096), (-7168, 5120), (-6144, 1024), (-6144, 2048),
                (-6144, 3072), (-6144, 4096), (-5120, 1024), (-5120, 2048), (-5120, 3072),
                (-5120, 4096)]  # fmt: skip
BORDER_CORNERS = [(-7936, 5120), (-7680, 4864), (-7680, 5120), (-7680, 5376), (-7424, 5120),
                  (-7168, 5120), (-6912, 5120), (-6656, 4864), (-6400, 4864), (-6144, 4864),
                  (-5888, 4864), (-5632, 4608), (-5376, 4608), (-5120, 4608), (-4864, 4608),
                  (-4608, 4608), (-4352, 4608)]  # fmt: skip
SOIL_POINTS = [(-8192, 2048), (-8192, 4096), (-6144, 2048), (-6144, 4096), (-7168, 2048),
               (-8192, 3072), (-7168, 4096), (-6144, 1024), (-5120, 2048), (-6144, 3072),
               (-5120, 4096)]  # fmt: skip


def peak_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)


# --- Tile edges (uses the pipeline's own entry points, by design: same code, other cut) ---------


@dataclass(frozen=True)
class EdgeTile:
    """A pseudo-tile: a 64 x 64 window centred on a point where tiles meet."""

    col: int
    row: int

    @property
    def key(self) -> str:
        return f"edge_{self.col}_{self.row}"

    @property
    def window(self):
        from forager_forecast.grid import CELL_SIZE_M, GridWindow

        s = CELL_SIZE_M
        return GridWindow((self.col - HALF) * s, (self.row - HALF) * s, (self.col + HALF) * s,
                          (self.row + HALF) * s)  # fmt: skip


def _stored(window, n, prefix_whole, prefix_half, band_count_names):
    from forager_forecast.pnw import assemble

    def file_for(key):
        p = TILES / ("trees" if prefix_whole.startswith("trees") else "soil")
        whole = p / f"{prefix_whole}_{key}.tif"
        if whole.exists():
            return whole
        if prefix_half:
            half = TILES / "trees_us_half" / f"{prefix_half}_{key}.tif"
            if half.exists():
                return half
        return None

    out, missing = {}, None
    for name in band_count_names:
        out[name], m = assemble(window, n, file_for, name)
        missing = m if missing is None else missing | m
    return out, missing


def _compare(recomputed: Path, stored: dict, missing) -> dict:
    with rasterio.open(recomputed) as ds:
        names = list(ds.descriptions)
        got = {n: ds.read(k + 1) for k, n in enumerate(names)}
    diffs = {}
    for n in names:
        a, b = got[n], stored[n]
        same = (a == b) | (np.isnan(a) & np.isnan(b)) if a.dtype.kind == "f" else a == b
        same = same | missing
        diffs[n] = int((~same).sum())
    return {"bands": names, "cells_differing": diffs, "cells_compared": int((~missing).sum())}


def edges_trees() -> dict:
    from forager_forecast.t6b_layers import tree_tile, tree_tile_us_half
    from forager_forecast.t6b_mask import SIDE_CA, SIDE_US, cells_in_study, read_mask

    scratch = CHECKS / "edges_trees"
    rows, ok = [], True
    for col, row in sorted(set(TREE_CORNERS) | set(BORDER_CORNERS)):
        t = EdgeTile(col, row)
        study, side = cells_in_study(t.window, *read_mask(MASK, t.window))
        has_ca, has_us = bool((side == SIDE_CA).any()), bool((side == SIDE_US).any())
        entry = {"point": [col, row], "study_cells": int(study.sum()), "canada": has_ca}
        if not study.any():
            entry["result"] = "no study cell"
            rows.append(entry)
            continue
        if has_ca and not has_us:
            entry["result"] = "Canadian cells only: pending on both sides, nothing to compare"
            rows.append(entry)
            continue
        t0 = time.time()
        if has_ca:
            from forager_forecast.t6b_layers import us_half_names

            tree_tile_us_half(t, MASK, TREEMAP / "TreeMap2023_CONUS.tif", PLOTS, NALCMS, scratch)
            v, f = (scratch / n for n in us_half_names(t.key))
            entry["entry_point"] = "tree_tile_us_half"
        else:
            tree_tile(t, MASK, TREEMAP / "TreeMap2023_CONUS.tif", PLOTS, None, NALCMS, scratch)
            v, f = scratch / f"trees_{t.key}.tif", scratch / f"trees_flags_{t.key}.tif"
            entry["entry_point"] = "tree_tile"
        entry["seconds"] = round(time.time() - t0, 1)
        with rasterio.open(v) as ds:
            vnames = list(ds.descriptions)
        with rasterio.open(f) as ds:
            fnames = list(ds.descriptions)
        sv, mv = _stored(t.window, 256, "trees", "trees_us_half", vnames)
        sf, mf = _stored(t.window, 256, "trees_flags", "trees_flags_us_half", fnames)
        entry["values"] = _compare(v, sv, mv)
        entry["flags"] = _compare(f, sf, mf)
        entry["tiles_missing_cells"] = int(mv.sum())
        bad = sum(entry["values"]["cells_differing"].values()) + sum(
            entry["flags"]["cells_differing"].values()
        )
        entry["result"] = "agree exactly" if bad == 0 else f"FAIL: {bad} band-cells differ"
        entry["finite_total_cover_cells"] = int(
            np.isfinite(sv["total_cover_pct"]).sum()
        )  # the sample has values
        ok = ok and bad == 0
        rows.append(entry)
        print(json.dumps({k: entry[k] for k in ("point", "result")}), flush=True)
    return {"check": "edges-trees", "ok": ok, "windows": rows, "peak_rss_mb": peak_mb()}


def edges_soil() -> dict:
    from forager_forecast.t6b_layers import soil_tile

    scratch = CHECKS / "edges_soil"
    rows, ok = [], True
    for col, row in SOIL_POINTS:
        t = EdgeTile(col, row)
        t0 = time.time()
        r = soil_tile(t, MASK, scratch / "native", scratch)
        entry = {"point": [col, row], "seconds": round(time.time() - t0, 1),
                 "cells_in_study": r.get("cells_in_study")}  # fmt: skip
        if "file" not in r:
            entry["result"] = r.get("skipped", "no file")
            rows.append(entry)
            continue
        with rasterio.open(scratch / r["file"]) as ds:
            names = list(ds.descriptions)
        stored, missing = _stored(t.window, 2048, "soil", None, names)
        entry["values"] = _compare(scratch / r["file"], stored, missing)
        entry["finite_mean_cells"] = int(np.isfinite(stored["ph_mean_0_30cm"]).sum())
        bad = sum(entry["values"]["cells_differing"].values())
        entry["result"] = "agree exactly" if bad == 0 else f"FAIL: {bad} band-cells differ"
        ok = ok and bad == 0
        rows.append(entry)
        print(json.dumps({k: entry[k] for k in ("point", "result")}), flush=True)
    return {"check": "edges-soil", "ok": ok, "windows": rows, "peak_rss_mb": peak_mb()}


# --- The ten cells: independent recompute -------------------------------------------------------

TO_GRID = Transformer.from_crs("EPSG:4269", "ESRI:102008", always_xy=True)
GRID_TO_LONLAT = Transformer.from_crs("ESRI:102008", "EPSG:4269", always_xy=True)
TO_IGH = Transformer.from_crs("EPSG:4326", "+proj=igh +datum=WGS84 +no_defs", always_xy=True)
DEPTHS = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}
SOIL_STATS = ("mean", "Q0.05", "Q0.95")
SAMPLES = 40
TOL = {"ph": 0.01, "soil_frac": 0.02, "cover": 0.1, "share": 0.001, "frac": 0.001}
BAND_W, BAND_E, BAND_S, BAND_N = -122.80, -95.15, 48.0, 50.0  # D115 item 1
HOSTS = ("Pseudotsuga", "Tsuga", "Picea", "Abies", "Pinus", "Quercus")


def _cell_of(lon, lat):
    x, y = TO_GRID.transform(lon, lat)
    return math.floor(x / 250.0), math.floor(y / 250.0)


def _master_at(path: Path, col: int, row: int) -> dict | None:
    with rasterio.open(path) as ds:
        t = ds.transform
        r = int(round((t.f - (row + 1) * 250.0) / 250.0))
        c = int(round((col * 250.0 - t.c) / 250.0))
        if not (0 <= r < ds.height and 0 <= c < ds.width):
            return None
        w = rasterio.windows.Window(c, r, 1, 1)
        return {n: float(ds.read(k + 1, window=w)[0, 0]) for k, n in enumerate(ds.descriptions)}


def _soil_cell(col, row):
    key = f"2048_{math.floor(col / 2048)}_{math.floor(row / 2048)}"
    native = T6B / "native" / "soil" / key
    offs = (np.arange(SAMPLES) + 0.5) / SAMPLES * 250.0
    sx, sy = np.meshgrid(col * 250.0 + offs, row * 250.0 + offs)
    lon, lat = GRID_TO_LONLAT.transform(sx.ravel(), sy.ravel())
    hx, hy = TO_IGH.transform(lon, lat)
    out = {}
    for stat in SOIL_STATS:
        acc = 0.0
        for depth, weight in DEPTHS.items():
            with rasterio.open(native / f"phh2o_{depth}_{stat}.tif") as ds:
                raw = ds.read(1)
                t, nod = ds.transform, ds.nodata
            pc = np.floor((np.asarray(hx) - t.c) / t.a).astype(int)
            pr = np.floor((np.asarray(hy) - t.f) / t.e).astype(int)
            if pc.min() < 0 or pr.min() < 0 or pc.max() >= raw.shape[1] or pr.max() >= raw.shape[0]:
                raise ValueError("cell reaches past the stored native window")
            v = raw[pr, pc]
            acc = acc + np.where(v == nod, np.nan, v / 10.0) * weight
        vals = acc / sum(DEPTHS.values())
        good = np.isfinite(vals)
        out[stat] = (float(vals[good].mean()) if good.any() else None, float(good.mean()))
    return key, out


def _dbf(path, want):
    with open(path, "rb") as f:
        n, hlen, rlen = struct.unpack("<IHH", f.read(12)[4:12])
        f.seek(32)
        fields = []
        while (d := f.read(32))[0] != 0x0D:
            fields.append((d[:11].rstrip(b"\0").decode(), d[16]))
        f.seek(hlen)
        out = {w: [] for w in want}
        for _ in range(n):
            r = f.read(rlen)
            p = 1
            for name, size in fields:
                if name in out:
                    out[name].append(r[p : p + size].decode().strip())
                p += size
    return out


def _clip(poly, x0, y0, x1, y1):
    """Sutherland-Hodgman: a polygon clipped to an axis-aligned rectangle."""

    def cut(pts, inside, inter):
        out = []
        for k in range(len(pts)):
            a, b = pts[k - 1], pts[k]
            if inside(b):
                if not inside(a):
                    out.append(inter(a, b))
                out.append(b)
            elif inside(a):
                out.append(inter(a, b))
        return out

    def ix(a, b, x):
        t = (x - a[0]) / (b[0] - a[0])
        return (x, a[1] + t * (b[1] - a[1]))

    def iy(a, b, y):
        t = (y - a[1]) / (b[1] - a[1])
        return (a[0] + t * (b[0] - a[0]), y)

    p = poly
    for inside, inter in (
        (lambda q: q[0] >= x0, lambda a, b: ix(a, b, x0)),
        (lambda q: q[0] <= x1, lambda a, b: ix(a, b, x1)),
        (lambda q: q[1] >= y0, lambda a, b: iy(a, b, y0)),
        (lambda q: q[1] <= y1, lambda a, b: iy(a, b, y1)),
    ):
        p = cut(p, inside, inter)
        if not p:
            return []
    return p


def _area(p):
    if len(p) < 3:
        return 0.0
    x = np.array([q[0] for q in p])
    y = np.array([q[1] for q in p])
    return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def _pixel_areas(col, row, ds):
    """{(r, c): area} of the cell's quad (densified, 8 points an edge) clipped to each pixel."""
    to_src = Transformer.from_crs("ESRI:102008", ds.crs, always_xy=True)
    edge = np.linspace(0, 250.0, 9)[:-1]
    x0, y0 = col * 250.0, row * 250.0
    gx = np.concatenate([x0 + edge, np.full(8, x0 + 250), x0 + 250 - edge, np.full(8, x0)])
    gy = np.concatenate([np.full(8, y0), y0 + edge, np.full(8, y0 + 250), y0 + 250 - edge])
    sx, sy = to_src.transform(gx, gy)
    poly = list(zip(np.asarray(sx).tolist(), np.asarray(sy).tolist(), strict=True))
    t = ds.transform
    cs = np.floor((np.asarray(sx) - t.c) / t.a).astype(int)
    rs = np.floor((np.asarray(sy) - t.f) / t.e).astype(int)
    out = {}
    for r in range(rs.min(), rs.max() + 1):
        for c in range(cs.min(), cs.max() + 1):
            px0, px1 = t.c + c * t.a, t.c + (c + 1) * t.a
            py1, py0 = t.f + r * t.e, t.f + (r + 1) * t.e
            a = _area(_clip(poly, px0, py0, px1, py1))
            if a > 0:
                out[(r, c)] = a
    return out, _area(poly)


def _surrogate(spcd, genus, eq3, nobs, table3_genus, woodland, conifer):
    if spcd in eq3:
        return spcd
    mates = [s for s, g in table3_genus.items() if g == genus and s not in woodland]
    if mates:
        return max(mates, key=lambda s: nobs[s])
    return 202 if conifer else 746  # D89(2): Douglas-fir or quaking aspen


def _plot_fractions(rows):
    """(genus and class fractions of crown area, total crown area) for one plot (D87 to D91,
    D116), from the tree table rows, with only the published tables imported."""
    from forager_forecast.crown_cover import (
        BECHTOLD_2004_DMAX,
        BECHTOLD_2004_EQ3,
        BECHTOLD_2004_N,
        BROADLEAF_GENERA,
        CONIFER_GENERA,
        TABLE_3_GENUS,
        WOODLAND,
    )

    pa = defaultdict(float)
    for r in rows:
        if r["STATUSCD"] != "1" or r["DIA"] in ("", "NA") or float(r["DIA"]) < 5.0:
            continue
        tpa = float(r["TPA_UNADJ"]) if r["TPA_UNADJ"] not in ("", "NA") else 0.0
        if not tpa > 0:
            continue
        spcd, genus, d = int(r["SPCD"]), r["SCIENTIFIC_NAME"].split()[0], float(r["DIA"])
        if genus in CONIFER_GENERA:
            conifer = True
        elif genus in BROADLEAF_GENERA:
            conifer = False
        else:
            conifer = spcd < 300  # D116
        s = _surrogate(spcd, genus, BECHTOLD_2004_EQ3, BECHTOLD_2004_N, TABLE_3_GENUS, WOODLAND,
                       conifer)  # fmt: skip
        b0, b1, b2 = BECHTOLD_2004_EQ3[s]
        dd = min(d, BECHTOLD_2004_DMAX[s])  # D91
        w = b0 + b1 * dd + b2 * dd * dd
        if w <= 0:
            continue
        a = tpa * math.pi * (w / 2) ** 2
        pa["_total"] += a
        if genus in HOSTS:
            pa[genus] += a
        pa["conifer" if conifer else "broadleaf"] += a
    tot = pa["_total"]
    return {k: (pa[k] / tot if tot > 0 else 0.0) for k in (*HOSTS, "conifer", "broadleaf")}, tot


def _tree_cell(col, row, treemap_tif=None, vat_path=None, tree_zip=None, nalcms=None,
               mask=None):  # fmt: skip
    """Total cover, valid fraction and shares of one US cell, recomputed independently."""
    treemap_tif = treemap_tif or TREEMAP / "TreeMap2023_CONUS.tif"
    vat_path = vat_path or TREEMAP / "TreeMap2023_CONUS.tif.vat.dbf"
    tree_zip = tree_zip or TREEMAP / "RDS-2026-0038.zip"
    nalcms, mask = nalcms or NALCMS, mask or MASK
    with rasterio.open(treemap_tif) as ds:
        areas, cell_area = _pixel_areas(col, row, ds)
        rs = [k[0] for k in areas]
        cs = [k[1] for k in areas]
        win = rasterio.windows.Window(min(cs), min(rs), max(cs) - min(cs) + 1,
                                      max(rs) - min(rs) + 1)  # fmt: skip
        plots = ds.read(1, window=win)
        nod, t, crs = ds.nodata, ds.transform, ds.crs
    to_ll = Transformer.from_crs(crs, "EPSG:4269", always_xy=True)
    with rasterio.open(nalcms) as nl, rasterio.open(mask) as mk:
        to_nl = Transformer.from_crs("EPSG:4326", nl.crs, always_xy=True)
        pix = []
        for (r, c), a in areas.items():
            x, y = t.c + (c + 0.5) * t.a, t.f + (r + 0.5) * t.e
            lon, lat = to_ll.transform(x, y)
            if BAND_W <= lon <= BAND_E and BAND_S <= lat <= BAND_N:
                side = "CA" if lat >= 49.0 else "US"
            else:
                gx, gy = TO_GRID.transform(lon, lat)
                mc, mr = math.floor(gx / 250.0), math.floor(gy / 250.0)
                mt = mk.transform
                cc = mc - int(round(mt.c / 250.0))
                rr = int(round(mt.f / 250.0)) - 1 - mr
                country = int(mk.read(1, window=rasterio.windows.Window(cc, rr, 1, 1))[0, 0])
                side = {1: "US", 2: "CA", 0: "either"}.get(country, "other")
            nx, ny = to_nl.transform(lon, lat)
            nc = math.floor((nx - nl.transform.c) / nl.transform.a)
            nr = math.floor((ny - nl.transform.f) / nl.transform.e)
            land = int(nl.read(1, window=rasterio.windows.Window(nc, nr, 1, 1))[0, 0])
            plot = int(plots[r - min(rs), c - min(cs)])
            pix.append({"a": a, "side": side, "water": land in (0, 18, 127), "plot": plot})
    vat = _dbf(vat_path, ("Value", "CANOPYPCT"))
    canopy = {int(float(v)): float(c) for v, c in zip(vat["Value"], vat["CANOPYPCT"], strict=True)
              if c}  # fmt: skip
    want = {p["plot"] for p in pix if p["plot"] != nod}
    trees = defaultdict(list)
    with zipfile.ZipFile(tree_zip) as z:
        with z.open("Data/TreeMap2023_CONUS_Tree_Table.csv") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                if int(r["TM_ID"]) in want:
                    trees[int(r["TM_ID"])].append(r)
    frac = {p: _plot_fractions(trees[p]) for p in want}
    valid_area = cover_num = share_den = 0.0
    share_num = defaultdict(float)
    for p in pix:
        if p["side"] not in ("US", "either") or p["water"]:
            continue
        valid_area += p["a"]
        if p["plot"] == nod:
            continue  # not forest: no crown (counts in the area, adds nothing)
        c = canopy[p["plot"]]
        cover_num += p["a"] * c
        g, tot = frac[p["plot"]]
        if tot > 0:
            share_den += p["a"] * c
            for k, v in g.items():
                share_num[k] += p["a"] * c * v
    vf = valid_area / cell_area
    cover = cover_num / valid_area if valid_area > 0 else None
    shares = {k: (share_num[k] / share_den if share_den > 0 else None)
              for k in (*HOSTS, "conifer", "broadleaf")}  # fmt: skip
    return {"valid_fraction": vf, "total_cover_pct": cover, "shares": shares,
            "native_pixels": len(pix), "plots": len(want)}  # fmt: skip


def ten_cells() -> dict:
    rule = json.loads((REPO / "docs/audits/2026-10-07-t6b-verify/ten_cells.json").read_text())
    from forager_forecast.pnw import PNW_BOX  # the box only, a constant

    out, ok = [], True
    for cell in rule["cells"]:
        if not PNW_BOX.contains(cell["lon"], cell["lat"]):
            continue
        col, row = _cell_of(cell["lon"], cell["lat"])
        assert (col, row) == (cell["col"], cell["row"]), cell
        entry = {"cell": cell["name"], "col": col, "row": row, "soil": {}, "trees": {}}
        key, src = _soil_cell(col, row)
        m = _master_at(TILES / "soil" / f"soil_{key}.tif", col, row)
        for stat, mb, fb in (("mean", "ph_mean_0_30cm", "valid_fraction_mean"),
                             ("Q0.05", "ph_q05_0_30cm_approximate", "valid_fraction_q05"),
                             ("Q0.95", "ph_q95_0_30cm_approximate",
                              "valid_fraction_q95")):  # fmt: skip
            sv, sf = src[stat]
            mv, mf = m[mb], m[fb]
            src_has = sv is not None and sf >= 0.5
            if not math.isfinite(mv) and not src_has:
                verdict = "both no data"
            elif (
                math.isfinite(mv)
                and src_has
                and abs(mv - sv) <= TOL["ph"]
                and abs(mf - sf) <= TOL["soil_frac"]
            ):
                verdict = "match"
            else:
                verdict = "FAIL"
            ok = ok and verdict != "FAIL"
            entry["soil"][stat] = {"source": sv, "source_fraction": sf, "master": mv,
                                   "master_fraction": mf, "verdict": verdict}  # fmt: skip
        # Host trees: the tile file the run wrote (whole, else the D119 US half).
        tkey = f"256_{math.floor(col / 256)}_{math.floor(row / 256)}"
        tpath = TILES / "trees" / f"trees_{tkey}.tif"
        fpath = TILES / "trees" / f"trees_flags_{tkey}.tif"
        if not tpath.exists():
            tpath = TILES / "trees_us_half" / f"trees_us_half_{tkey}.tif"
            fpath = TILES / "trees_us_half" / f"trees_flags_us_half_{tkey}.tif"
        entry["trees"]["tile_file"] = tpath.name
        if not tpath.exists():
            entry["trees"]["verdict"] = "FAIL: no tile file"
            ok = False
            out.append(entry)
            continue
        mt, mfl = _master_at(tpath, col, row), _master_at(fpath, col, row)
        ind = _tree_cell(col, row)
        checks = {}
        vf_ok = abs(mt["valid_fraction"] - ind["valid_fraction"]) <= TOL["frac"]
        checks["valid_fraction"] = [mt["valid_fraction"], ind["valid_fraction"], vf_ok]
        has = ind["valid_fraction"] >= 0.5 and ind["total_cover_pct"] is not None
        if has and math.isfinite(mt["total_cover_pct"]):
            c_ok = abs(mt["total_cover_pct"] - ind["total_cover_pct"]) <= TOL["cover"]
        else:
            c_ok = not has and not math.isfinite(mt["total_cover_pct"])
        checks["total_cover_pct"] = [mt["total_cover_pct"], ind["total_cover_pct"], c_ok]
        checks["source"] = [mt["source"], 1.0, mt["source"] == 1.0]
        defined = has and ind["total_cover_pct"] >= 10.0
        for g in (*HOSTS, "conifer", "broadleaf"):
            iv = ind["shares"][g] if defined else None
            mv = mt[f"share_{g}"]
            if iv is not None and math.isfinite(mv):
                s_ok = abs(mv - iv) <= TOL["share"]
            else:
                s_ok = iv is None and not math.isfinite(mv)
            flag = mfl[f"flag_{g}"]
            f_ok = flag == (1.0 if iv is not None else 0.0)
            checks[f"share_{g}"] = [mv, iv, s_ok]
            checks[f"flag_{g}"] = [flag, 1.0 if iv is not None else 0.0, f_ok]
        good = all(v[2] for v in checks.values())
        ok = ok and good
        entry["trees"].update({"checks": checks, "native_pixels": ind["native_pixels"],
                               "plots": ind["plots"],
                               "verdict": "match" if good else "FAIL"})  # fmt: skip
        out.append(entry)
    return {"check": "ten-cells", "ok": ok, "cells_checked": len(out), "cells_in_rule": 10,
            "cells": out, "tolerances": TOL, "peak_rss_mb": peak_mb()}  # fmt: skip


def seam() -> dict:
    from forager_forecast.seam import run_transects

    bands = ["total_cover_pct", "share_Pseudotsuga", "share_conifer", "share_broadleaf"]
    res = run_transects(OUT / "mosaic" / "trees_pnw.tif", bands)
    summary = {}
    for b, r in res.items():
        steps = r["border_steps"]
        summary[b] = {
            "verdict": "no verdict, Canadian side pending" if r["n_transects"] == 0
            else ("artifact" if r["artifact"] else "no step"),
            "transects_with_a_border_step": r["n_transects"],
            "within_us_median_abs": r["within_us_median_abs"],
            "within_us_p95_abs": r["within_us_p95_abs"],
            "within_ca_median_abs": r["within_ca_median_abs"],
            "border_steps": steps,
        }  # fmt: skip
    return {"check": "seam", "ok": None, "bands": summary, "peak_rss_mb": peak_mb()}


def seam_us_samples() -> dict:
    """What the seam check can show now: of the 25 x 80 US-side samples, how many have a value."""
    from forager_forecast.grid import cell_for_lonlat
    from forager_forecast.seam import sample_latitudes, transect_longitudes

    with rasterio.open(OUT / "mosaic" / "trees_pnw.tif") as ds:
        names = list(ds.descriptions)
        t = ds.transform
        out = {}
        for b in ("total_cover_pct", "valid_fraction", "source"):
            band = ds.read(names.index(b) + 1)
            vals = []
            for lon in transect_longitudes():
                _, south = sample_latitudes(lon)
                for lat in south:
                    c = cell_for_lonlat(lon, float(lat))
                    r = int(round(t.f / 250.0)) - 1 - c.row
                    cc = c.col - int(round(t.c / 250.0))
                    vals.append(float(band[r, cc]))
            vals = np.array(vals)
            out[b] = {"samples": len(vals), "finite": int(np.isfinite(vals).sum())}
            if b == "source":
                keys, counts = np.unique(vals, return_counts=True)
                out[b]["values"] = {str(k): int(v) for k, v in zip(keys, counts, strict=True)}
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("check", choices=["edges-trees", "edges-soil", "ten-cells", "seam"])
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    CHECKS.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if args.check == "edges-trees":
        result = edges_trees()
    elif args.check == "edges-soil":
        result = edges_soil()
    elif args.check == "ten-cells":
        result = ten_cells()
    else:
        result = seam()
        result["us_side_samples"] = seam_us_samples()
    result["seconds"] = round(time.time() - t0, 1)
    text = json.dumps(result, indent=1, default=str) + "\n"
    out = args.out or RULE_DIR / f"{args.check}.out.json"
    out.write_text(text)
    print(json.dumps({"check": result["check"], "ok": result["ok"], "out": str(out)}))
    sys.exit(1 if result["ok"] is False else 0)


if __name__ == "__main__":
    main()

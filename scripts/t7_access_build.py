"""T7 part B: build the 250 m distance-to-road-and-trail layer over the PNW box.

Usage (repository root, one stage at a time, under the dispatch's memory cap):
    systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0 nice -n 19 \\
        .venv/bin/python scripts/t7_access_build.py prepare|build|spot|coverage

- prepare: reads every fetched source (read-only, through /vsizip/), keeps the box padded by
  50 km, applies the owner's rulings (-1168: closed roads in, trails from federal sources only),
  reprojects to the grid CRS and writes one FlatGeobuf per source and band under work/, with the
  counts kept and dropped per source in prepare.json.
- build: the trails-not-published mask, then the distances block by block (256 x 256 cells),
  written to access_pnw.tif (three float32 bands) and trails_unpublished_pnw.tif (uint8), and the
  manifest naming every input's sha256.
- spot: ten cells re-measured from the raw sources by a separate path (no FlatGeobuf, no block
  search: every line within 60 km read from the source file and measured one by one).
- coverage: per level III block, from the T7 table's eligible cells (read-only).
"""

import datetime as dt
import hashlib
import json
import subprocess
import sys
import time
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pyogrio
import rasterio
import shapely
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.windows import Window

from forager_forecast.grid import CELL_SIZE_M, GEOGRAPHIC_CRS, GRID_CRS, GridWindow
from forager_forecast.pnw import PNW_BOX, pnw_window
from forager_forecast.t4_layer import box_mask
from forager_forecast.t7.access import (
    BAND_ROAD,
    BAND_TRAIL,
    FEDERAL_TRAIL_ORIGINATORS,
    OUTPUT_BANDS,
    PAD_M,
    TRAILS_UNPUBLISHED_FORESTS,
    block_distances,
    cell_centres,
    combine,
    keep_road_class,
    keep_trail,
)
from forager_forecast.t7.access_sources import ACCESS_ROOT, NTD_STATES, RAW_DIR, sha256

REPO = Path(__file__).resolve().parent.parent
WORK = ACCESS_ROOT / "work"
OUT = ACCESS_ROOT / "pnw-2026-10-17"
ACCESS_FILE = "access_pnw.tif"
UNPUBLISHED_FILE = "trails_unpublished_pnw.tif"
TILE_N = 256
START_RADIUS_M = 8000.0
MAX_RADIUS_M = 2_000_000.0
# The box padded by at least PAD_M on every side, in degrees for the read filter (50 km is under
# 0.45 degree of latitude, and under 0.71 degree of longitude at 49 N).
PAD_DEG_LAT, PAD_DEG_LON = 0.5, 0.75
READ_BBOX = (PNW_BOX.west - PAD_DEG_LON, PNW_BOX.south - PAD_DEG_LAT,
             PNW_BOX.east + PAD_DEG_LON, PNW_BOX.north + PAD_DEG_LAT)  # fmt: skip
FT = Path("/mnt/work/Zynergy/forecast-data/t7/fit")
# The cells computed: the box's study cells, read (read-only) from the 2026-10-17 T7 fit's
# applicability raster, every code but 0 ("outside the study area or box"). Ocean and other
# non-study cells are NaN: computing them (the first run, stopped after 20 blocks) spent most of
# its time widening the search over open sea.
DOMAIN = Path("/mnt/work/Zynergy/forecast-data/t7/pnw-2026-10-17/applicability_pnw.tif")
LABEL = (
    "Distance from each 250 m cell centre to the nearest road, trail, or either, in metres on the "
    "grid plane (ESRI:102008; up to about 6% from ground distance). A model input. Not a forecast."
)
ATTRIBUTION = (
    "Roads and trails: USGS National Transportation Dataset (acknowledgment of the U.S. "
    "Geological Survey); National Forest System Roads, National Forest System Trails and "
    "Administrative Forest Boundaries, USDA Forest Service, CC BY 4.0; BLM National GTLF Public "
    "Managed Trails, Bureau of Land Management, public domain."
)


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def gdb_path(name: str) -> str:
    zp = RAW_DIR / f"{name}.zip"
    gdb = sorted({n.split("/")[0] for n in zipfile.ZipFile(zp).namelist() if ".gdb" in n})[0]
    return f"/vsizip/{zp}/{gdb}"


def read(name: str, layer: str | None, columns: list[str], bbox=READ_BBOX):
    """(geometries in the grid CRS, {column: values}) of the features whose envelopes meet bbox."""
    meta, _, geom, fields = pyogrio.raw.read(
        gdb_path(name), layer=layer, columns=columns, bbox=bbox, force_2d=True
    )
    if meta["crs"] != "EPSG:4269":
        raise ValueError(f"{name}: CRS {meta['crs']}, expected EPSG:4269")
    cols = {str(c): v for c, v in zip(meta["fields"], fields, strict=True)}
    geoms = shapely.from_wkb(geom)
    t = Transformer.from_crs("EPSG:4269", GRID_CRS, always_xy=True)
    geoms = shapely.transform(geoms, lambda xy: np.column_stack(t.transform(xy[:, 0], xy[:, 1])))
    return geoms, cols


def write_fgb(path: Path, geoms) -> None:
    keep = ~shapely.is_missing(geoms) & ~shapely.is_empty(geoms)
    wkb = shapely.to_wkb(geoms[keep])
    pyogrio.raw.write(str(path), wkb, [], [], driver="FlatGeobuf", geometry_type="MultiLineString",
                      crs=GRID_CRS, promote_to_multi=True, SPATIAL_INDEX="YES")  # fmt: skip


def null_count(geoms) -> int:
    return int((shapely.is_missing(geoms) | shapely.is_empty(geoms)).sum())


def cmd_prepare() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    report: dict = {"started_utc": now(), "read_bbox_lonlat": READ_BBOX, "sources": {}}
    for state in NTD_STATES:
        name = f"ntd_{state.lower()}"
        g, c = read(name, "Trans_RoadSegment", ["tnmfrc", "source_originator"])
        keep = keep_road_class(c["tnmfrc"])
        write_fgb(WORK / f"roads_{name}.fgb", g[keep])
        g2, c2 = read(name, "Trans_TrailSegment", ["sourceoriginator"])
        keep2 = keep_trail(c2["sourceoriginator"])
        write_fgb(WORK / f"trails_{name}.fgb", g2[keep2])
        report["sources"][name] = {
            "roads_read": len(g), "roads_kept": int(keep.sum()),
            "roads_dropped_by_class": dict(Counter(int(x) for x in c["tnmfrc"][~keep]
                                                   if x is not None)),
            "roads_by_originator": dict(Counter(str(x) for x in c["source_originator"][keep])),
            "roads_no_geometry": null_count(g[keep]),
            "trails_read": len(g2), "trails_kept": int(keep2.sum()),
            "trails_dropped_by_originator": dict(Counter(str(x) for x in
                                                         c2["sourceoriginator"][~keep2])),
            "trails_kept_by_originator": dict(Counter(str(x) for x in
                                                      c2["sourceoriginator"][keep2])),
            "trails_no_geometry": null_count(g2[keep2]),
        }  # fmt: skip
        print(name, json.dumps(report["sources"][name]), flush=True)
        del g, c, g2, c2
    g, c = read("fs_roads", None, ["OPER_MAINT_LEVEL", "ADMIN_ORG"])
    write_fgb(WORK / "roads_fs_roads.fgb", g)
    report["sources"]["fs_roads"] = {
        "roads_read": len(g), "roads_kept": len(g), "roads_no_geometry": null_count(g),
        "by_maintenance_level": dict(Counter(str(x) for x in c["OPER_MAINT_LEVEL"])),
    }  # fmt: skip
    print("fs_roads", json.dumps(report["sources"]["fs_roads"]), flush=True)
    g, c = read("fs_trails", None, ["ADMIN_ORG"])
    write_fgb(WORK / "trails_fs_trails.fgb", g)
    org = np.array([str(x or "")[:4] for x in c["ADMIN_ORG"]])
    missing = shapely.is_missing(g) | shapely.is_empty(g)
    report["sources"]["fs_trails"] = {
        "trails_read": len(g), "trails_no_geometry": int(missing.sum()),
        "no_geometry_by_forest": dict(Counter(org[missing].tolist())),
        "with_geometry_by_forest": dict(Counter(org[~missing].tolist())),
    }  # fmt: skip
    print("fs_trails", json.dumps(report["sources"]["fs_trails"]), flush=True)
    g, _ = read("blm_trails", None, [])
    write_fgb(WORK / "trails_blm_trails.fgb", g)
    report["sources"]["blm_trails"] = {"trails_read": len(g), "trails_no_geometry": null_count(g)}
    print("blm_trails", json.dumps(report["sources"]["blm_trails"]), flush=True)
    report["finished_utc"] = now()
    (WORK / "prepare.json").write_text(json.dumps(report, indent=2) + "\n")


def band_files(band: str) -> list[Path]:
    return sorted(WORK.glob(f"{band}_*.fgb"))


def reader(files: list[Path]):
    def read_lines(bbox):
        parts = []
        for f in files:
            _, _, geom, _ = pyogrio.raw.read(str(f), bbox=bbox, read_geometry=True, columns=[])
            if len(geom):
                parts.append(shapely.from_wkb(geom))
        return np.concatenate(parts) if parts else np.array([], dtype=object)

    return read_lines


def unpublished_mask(window: GridWindow) -> tuple[np.ndarray, dict]:
    meta, _, geom, fields = pyogrio.raw.read(gdb_path("fs_admin_forests"),
                                             columns=["FORESTORGCODE", "FORESTNAME"])  # fmt: skip
    cols = {str(c): v for c, v in zip(meta["fields"], fields, strict=True)}
    codes = [str(x) for x in cols["FORESTORGCODE"]]
    t = Transformer.from_crs("EPSG:4269", GRID_CRS, always_xy=True)
    shapes, found = [], {}
    for i, code in enumerate(codes):
        if code in TRAILS_UNPUBLISHED_FORESTS:
            g = shapely.from_wkb(geom[i])
            g = shapely.transform(g, lambda xy: np.column_stack(t.transform(xy[:, 0], xy[:, 1])))
            shapes.append((shapely.geometry.mapping(g), 1))
            found[code] = str(cols["FORESTNAME"][i])
    if set(found) != set(TRAILS_UNPUBLISHED_FORESTS):
        raise ValueError(f"forests found {found}, expected {TRAILS_UNPUBLISHED_FORESTS}")
    transform = from_origin(window.left, window.top, CELL_SIZE_M, CELL_SIZE_M)
    mask = rasterize(shapes, out_shape=(window.height, window.width), transform=transform,
                     fill=0, dtype="uint8")  # fmt: skip
    return mask, found


def git_commit() -> str:
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()  # fmt: skip
    cmd = ["git", "-C", str(REPO), "status", "--porcelain", "--", "src", "scripts"]
    dirty = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return head + ("-dirty" if dirty.strip() else "")


def profile(window: GridWindow) -> dict:
    return {"driver": "GTiff", "width": window.width, "height": window.height, "crs": GRID_CRS,
            "transform": from_origin(window.left, window.top, CELL_SIZE_M, CELL_SIZE_M),
            "tiled": True, "blockxsize": TILE_N, "blockysize": TILE_N, "compress": "deflate",
            "BIGTIFF": "IF_SAFER"}  # fmt: skip


def cmd_build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    window = pnw_window()
    started = now()
    t0 = time.perf_counter()
    mask, found = unpublished_mask(window)
    with rasterio.open(DOMAIN) as ds:
        if (ds.width, ds.height) != (window.width, window.height) or ds.transform != from_origin(
            window.left, window.top, CELL_SIZE_M, CELL_SIZE_M
        ):
            raise ValueError(f"{DOMAIN} is not on the PNW window")
        inside_all = (ds.read(1) != 0) & box_mask(window, PNW_BOX)
    total_blocks = sum(
        inside_all[r:r + TILE_N, c:c + TILE_N].any()
        for r in range(0, window.height, TILE_N) for c in range(0, window.width, TILE_N)
    )  # fmt: skip
    print(f"{now()} domain cells {int(inside_all.sum())}, blocks {total_blocks}", flush=True)
    roads, trails = reader(band_files("roads")), reader(band_files("trails"))
    acc_part = OUT / f"{ACCESS_FILE}.partial"
    msk_part = OUT / f"{UNPUBLISHED_FILE}.partial"
    tags = {"label": LABEL, "attribution": ATTRIBUTION, "units": "metres (grid plane)",
            "bands": ", ".join(OUTPUT_BANDS), "dispatch": "2026-10-17-T7B",
            "record": "Forager RECORD -1163, -1168"}  # fmt: skip
    no_line = {BAND_ROAD: 0, BAND_TRAIL: 0}
    with rasterio.open(acc_part, "w", count=3, dtype="float32", nodata=float("nan"),
                       **profile(window)) as acc, \
         rasterio.open(msk_part, "w", count=1, dtype="uint8", nodata=None,
                       **profile(window)) as msk:  # fmt: skip
        for k, b in enumerate(OUTPUT_BANDS, start=1):
            acc.set_band_description(k, b)
        acc.update_tags(**tags)
        msk.set_band_description(1, "trails_unpublished")
        msk.update_tags(label="1: trail records published without lines (Forest Service); the "
                        "trail and combined bands are NaN here, never filled. 0: otherwise.",
                        forests=json.dumps(found))  # fmt: skip
        msk.write(mask, 1)
        n_blocks = 0
        for r0 in range(0, window.height, TILE_N):
            for c0 in range(0, window.width, TILE_N):
                h, w = min(TILE_N, window.height - r0), min(TILE_N, window.width - c0)
                bw = GridWindow(window.left + c0 * CELL_SIZE_M,
                                window.top - (r0 + h) * CELL_SIZE_M,
                                window.left + (c0 + w) * CELL_SIZE_M,
                                window.top - r0 * CELL_SIZE_M)  # fmt: skip
                inside = inside_all[r0 : r0 + h, c0 : c0 + w]
                if not inside.any():
                    continue
                d_road = block_distances(roads, bw, inside, START_RADIUS_M, MAX_RADIUS_M)
                d_trail = block_distances(trails, bw, inside, START_RADIUS_M, MAX_RADIUS_M)
                no_line[BAND_ROAD] += int((inside & np.isnan(d_road)).sum())
                no_line[BAND_TRAIL] += int((inside & np.isnan(d_trail)).sum())
                t_m, d_any = combine(d_road, d_trail, mask[r0 : r0 + h, c0 : c0 + w] == 1)
                win = Window(c0, r0, w, h)
                for k, arr in enumerate((d_road, t_m, d_any), start=1):
                    acc.write(arr.astype(np.float32), k, window=win)
                n_blocks += 1
                if n_blocks % 20 == 0:
                    print(f"{now()} blocks {n_blocks}/{total_blocks}", flush=True)
    acc_part.rename(OUT / ACCESS_FILE)
    msk_part.rename(OUT / UNPUBLISHED_FILE)
    prepare = json.loads((WORK / "prepare.json").read_text())
    inputs = {}
    for rec in sorted(RAW_DIR.glob("*.request.json")):
        if rec.name.startswith("blm_trails.first-run"):
            continue
        r = json.loads(rec.read_text())
        inputs[r["name"]] = {k: r[k] for k in ("url", "fetched_utc", "size_bytes", "sha256",
                                                 "check", "check_expected")}  # fmt: skip
        assert sha256(RAW_DIR / f"{r['name']}.zip") == r["sha256"], r["name"]
    manifest = {
        "dispatch": "docs/dispatch/2026-10-17-t7-part-b.md (origin/t7-strengthen-plan)",
        "record": "Forager RECORD -1163 (intent), -1168 (go, the owner's rulings)",
        "code_commit": git_commit(), "started_utc": started, "finished_utc": now(),
        "seconds": round(time.perf_counter() - t0, 1),
        "window": [window.left, window.bottom, window.right, window.top], "crs": GRID_CRS,
        "cell_size_m": CELL_SIZE_M, "box": vars(PNW_BOX), "pad_m": PAD_M,
        "read_bbox_lonlat": READ_BBOX, "start_radius_m": START_RADIUS_M,
        "max_radius_m": MAX_RADIUS_M, "bands": list(OUTPUT_BANDS),
        "rules": {
            "roads": "NTD road segments except classes 7 (ferry) and 8 (tunnel); every Forest "
                     "Service road incl. closed (maintenance level 1) (ruling 3)",
            "trails": "NTD trail segments whose source originator is one of "
                      f"{sorted(FEDERAL_TRAIL_ORIGINATORS)}; every Forest Service trail with a "
                      "line; every BLM managed trail (ruling 2)",
            "unpublished": f"cells by centre in {found}: trail and combined bands NaN (ruling 1)",
            "distance": "exact centre-to-nearest-line, grid-plane metres; scale 0.940 to 0.945 "
                        "along parallels, 1.058 to 1.063 along meridians over the box",
            "outside_box": "NaN",
            "domain": "cells of the box whose code in the domain raster is not 0; others NaN",
        },
        "cells_without_any_line_within_max_radius": no_line,
        "unpublished_cells_in_domain": int((mask.astype(bool) & inside_all).sum()),
        "domain": {"path": str(DOMAIN), "sha256": sha256(DOMAIN),
                   "cells": int(inside_all.sum())},
        "inputs": inputs, "prepare": prepare,
        "intermediates": {f.name: sha256(f) for f in sorted(WORK.glob("*.fgb"))},
        "outputs": {ACCESS_FILE: sha256(OUT / ACCESS_FILE),
                    UNPUBLISHED_FILE: sha256(OUT / UNPUBLISHED_FILE)},
        "label": LABEL, "attribution": ATTRIBUTION,
    }  # fmt: skip
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: manifest[k] for k in ("seconds", "cells_without_any_line_within_max_"
                                               "radius", "unpublished_cells_in_domain",
                                               "outputs")}), flush=True)  # fmt: skip


def raw_lines(band: str, bbox_lonlat):
    """Every line of ``band`` near a point straight from the raw sources, with its source."""
    out = []
    for state in NTD_STATES:
        name = f"ntd_{state.lower()}"
        if band == "roads":
            g, c = read(name, "Trans_RoadSegment", ["tnmfrc"], bbox=bbox_lonlat)
            k = keep_road_class(c["tnmfrc"])
        else:
            g, c = read(name, "Trans_TrailSegment", ["sourceoriginator"], bbox=bbox_lonlat)
            k = keep_trail(c["sourceoriginator"])
        out += [(x, name) for x in g[k]]
    extra = ["fs_roads"] if band == "roads" else ["fs_trails", "blm_trails"]
    for name in extra:
        g, _ = read(name, None, [], bbox=bbox_lonlat)
        out += [(x, name) for x in g]
    return [(x, n) for x, n in out if x is not None and not shapely.is_empty(x)]


SPOT_CELLS = (  # (label, lon, lat): chosen before the build, spread over blocks and settings
    ("Portland, OR, downtown", -122.6765, 45.5231),
    ("Eagle Cap Wilderness core (Wallowa-Whitman, masked)", -117.30, 45.17),
    ("Frank Church wilderness interior, ID", -115.10, 45.25),
    ("Olympic NP interior, WA", -123.60, 47.80),
    ("Bob Marshall Wilderness, MT", -113.20, 47.60),
    ("Mount Hood NF slope, OR", -121.80, 45.30),
    ("Salt Lake City, UT", -111.89, 40.76),
    ("Black Rock Desert, NV", -119.10, 40.90),
    ("Klamath Mountains, Trinity Alps, CA", -123.00, 41.00),
    ("Malheur NF, Strawberry Mountain, OR", -118.70, 44.30),
)


def cmd_spot() -> None:
    window = pnw_window()
    t = Transformer.from_crs(GEOGRAPHIC_CRS, GRID_CRS, always_xy=True)
    gx, gy = cell_centres(window)
    rows = []
    with rasterio.open(OUT / ACCESS_FILE) as ds, rasterio.open(OUT / UNPUBLISHED_FILE) as ms:
        for label, lon, lat in SPOT_CELLS:
            x, y = t.transform(lon, lat)
            r = int((window.top - y) // CELL_SIZE_M)
            c = int((x - window.left) // CELL_SIZE_M)
            cx, cy = float(gx[r, c]), float(gy[r, c])
            clon, clat = t.transform(cx, cy, direction="INVERSE")
            vals = ds.read(window=Window(c, r, 1, 1))[:, 0, 0].tolist()
            unpub = int(ms.read(1, window=Window(c, r, 1, 1))[0, 0])
            row = {"label": label, "cell_centre_lonlat": [round(clon, 5), round(clat, 5)],
                   "row": r, "col": c, "layer": dict(zip(OUTPUT_BANDS, vals, strict=True)),
                   "trails_unpublished": unpub}  # fmt: skip
            pt = shapely.points(cx, cy)
            for band, key in (("roads", BAND_ROAD), ("trails", BAND_TRAIL)):
                bbox = (clon - 0.8, clat - 0.55, clon + 0.8, clat + 0.55)  # about 60 km
                lines = raw_lines(band, bbox)
                if lines:
                    d = [float(shapely.distance(pt, g)) for g, _ in lines]
                    i = int(np.argmin(d))
                    row[f"check_{key}"] = round(d[i], 2)
                    row[f"check_{key}_source"] = lines[i][1]
                    row[f"check_{key}_lines_read"] = len(lines)
                else:
                    row[f"check_{key}"] = None
            rows.append(row)
            print(json.dumps(row), flush=True)
    (OUT / "spot_check.json").write_text(json.dumps(rows, indent=2) + "\n")


def cmd_coverage() -> None:
    window = pnw_window()
    meta = json.loads((FT / "table_meta.json").read_text())
    level3 = {e["code"]: e for e in meta["level3_table"]}
    tab = np.load(FT / "table.npz")
    cell_id, l3 = tab["cell_id"], tab["level3"]
    col = (cell_id & 0xFFFF).astype(np.int64) - (1 << 15)
    row = (cell_id >> 16).astype(np.int64) - (1 << 15)
    c = col - window.left // CELL_SIZE_M
    r = window.top // CELL_SIZE_M - 1 - row
    if c.min() < 0 or r.min() < 0 or c.max() >= window.width or r.max() >= window.height:
        raise ValueError("a T7 cell lies outside the PNW window")
    with rasterio.open(OUT / ACCESS_FILE) as ds, rasterio.open(OUT / UNPUBLISHED_FILE) as ms:
        bands = ds.read()
        unpub = ms.read(1)
    road, trail, both = bands[0][r, c], bands[1][r, c], bands[2][r, c]
    un = unpub[r, c] == 1
    out = []
    for code in sorted(set(l3.tolist())):
        sel = l3 == code
        e = level3.get(int(code), {"level3": "none", "name": "no level III"})
        n = int(sel.sum())
        out.append({
            "level3": e["level3"], "name": e["name"], "cells": n,
            "road_values": int(np.isfinite(road[sel]).sum()),
            "trail_values": int(np.isfinite(trail[sel]).sum()),
            "trails_unpublished": int(un[sel].sum()),
            "road_median_m": float(np.nanmedian(road[sel])) if n else None,
            "road_p90_m": float(np.nanpercentile(road[sel], 90)) if n else None,
            "trail_median_m": float(np.nanmedian(trail[sel])) if np.isfinite(trail[sel]).any()
            else None,
            "any_median_m": float(np.nanmedian(both[sel])) if np.isfinite(both[sel]).any()
            else None,
        })  # fmt: skip
    total = {"cells": int(len(l3)), "road_values": int(np.isfinite(road).sum()),
             "trail_values": int(np.isfinite(trail).sum()), "trails_unpublished": int(un.sum()),
             "table": str(FT / "table.npz"),
             "table_cells_are": "T7's table cells, eligible under P4 (codes 1 and 2)",
             "table_meta_sha256": hashlib.sha256((FT / "table_meta.json").read_bytes()).hexdigest()
             }  # fmt: skip
    (OUT / "coverage_by_block.json").write_text(json.dumps({"total": total, "blocks": out},
                                                           indent=2) + "\n")  # fmt: skip
    print(json.dumps(total))
    for o in out:
        print(json.dumps(o))


if __name__ == "__main__":
    {"prepare": cmd_prepare, "build": cmd_build, "spot": cmd_spot, "coverage": cmd_coverage}[
        sys.argv[1]
    ]()

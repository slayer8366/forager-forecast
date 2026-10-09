"""The Pacific Northwest render for the owner's meeting (Forager RECORD -772 to -777).

Reads finished T6b tiles from the flash drive and writes, under forecast-data/pnw/ (never into
t6b/): the PNW mosaics, labelled SVG images, one zoom-9 PMTiles archive per layer, and the
boundary lines for the browsable map. One heavy step at a time, under the cap:

    systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0 \
        nice -n 10 .venv/bin/python scripts/pnw_build.py STAGE

STAGE is one of: mosaic, images, pmtiles, lines. Each writes a JSON summary beside its outputs and
prints it.
"""

import argparse
import json
import resource
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin

from forager_forecast.grid import CELL_SIZE_M, GEOGRAPHIC_CRS, GRID_CRS, GridWindow
from forager_forecast.pnw import (
    DATA_LICENCE,
    LABEL,
    MISSING_RGBA,
    PENDING_RGBA,
    PNW_BOX,
    SOURCES,
    LegendEntry,
    assemble,
    in_box,
    paint,
    png_bytes,
    pnw_window,
    ramp,
    svg_image,
    tile_states,
    tree_file_for,
)
from forager_forecast.t5_layer import read_dbf_columns
from forager_forecast.t6b_layers import FLAG_PENDING
from forager_forecast.t6b_mask import (
    _CEC_LONLAT,
    CEC_LAEA,
    cells_in_study,
    read_mask,
    read_shapefile,
)
from forager_forecast.tiles import (
    encode_percent_byte,
    encode_ph_byte,
    master_to_mercator_nearest,
    mercator_window_for,
    write_archive,
)

DRIVE = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data")
T6B = DRIVE / "t6b"
MASK = T6B / "mask.tif"
TILES = T6B / "tiles"
TREES = TILES / "trees"
US_HALF = TILES / "trees_us_half"
SOIL = TILES / "soil"
POLITICAL = (
    T6B / "sources" / "politicalboundaries_shapefile" / "NA_PoliticalDivisions" / "data"
    / "boundaries_p_2021_v3.shp"
)  # fmt: skip
OUT = DRIVE / "pnw"
MOSAIC = OUT / "mosaic"
SOIL_N, TREE_N = 2048, 256
MIN_FREE = 1_000_000_000  # dispatch: stop if under 1 GB

TREE_BANDS = ("total_cover_pct", "valid_fraction", "source", "share_Pseudotsuga", "share_Tsuga",
              "share_conifer", "share_broadleaf")  # fmt: skip
# What is shown, and why (report): Douglas-fir is the best-supported host layer (both sides,
# no step at the seam after T5 Amendment 3, D90) and the main chanterelle host here; hemlock is
# a host T5 sources and is US-only (D85), which is all the box holds; total cover gives context.
LAYERS = {
    "soil-ph": {"band": "ph_mean_0_30cm", "mosaic": "soil", "title": "Soil pH, 0 to 30 cm",
                "unit": "pH", "range": (4.5, 8.0), "kind": "ph",
                "subtitle": "SoilGrids 2.0 mean, thickness-weighted 0 to 30 cm (D80), 250 m grid"},
    "tree-cover": {"band": "total_cover_pct", "mosaic": "trees",
                   "title": "Tree canopy cover", "unit": "% cover", "range": (0.0, 100.0),
                   "kind": "percent", "scale": 1.0,
                   "subtitle": "TreeMap 2023 live canopy cover (D88), 250 m grid"},
    "douglas-fir": {"band": "share_Pseudotsuga", "mosaic": "trees",
                    "title": "Douglas-fir share of tree canopy", "unit": "% of canopy",
                    "range": (0.0, 100.0), "kind": "percent", "scale": 100.0,
                    "subtitle": "Pseudotsuga share of canopy cover where cover is 10% or more "
                                "(D87, D89), 250 m grid"},
    "hemlock": {"band": "share_Tsuga", "mosaic": "trees",
                "title": "Hemlock share of tree canopy", "unit": "% of canopy",
                "range": (0.0, 100.0), "kind": "percent", "scale": 100.0,
                "subtitle": "Tsuga share of canopy cover where cover is 10% or more "
                            "(D87, D89), 250 m grid"},
}  # fmt: skip
PLACES = [("Seattle", -122.332, 47.606), ("Portland", -122.679, 45.515),
          ("Spokane", -117.426, 47.659), ("Boise", -116.202, 43.615),
          ("Eugene", -123.087, 44.052), ("Bend", -121.315, 44.058),
          ("Redding", -122.392, 40.587), ("Missoula", -113.994, 46.872),
          ("Medford", -122.875, 42.327), ("Yakima", -120.505, 46.602)]  # fmt: skip


def log(summary: dict) -> None:
    summary["peak_rss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    summary["free_bytes_after"] = shutil.disk_usage(DRIVE).free
    summary["at"] = datetime.now(UTC).isoformat(timespec="seconds")
    print(json.dumps(summary, indent=1))


def check_free() -> int:
    free = shutil.disk_usage(DRIVE).free
    if free < MIN_FREE:
        sys.exit(f"stop: {free} bytes free on the drive, under 1 GB")
    return free


def write_band_tif(path: Path, window: GridWindow, bands: dict[str, np.ndarray], tags: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    dtype = "float32"
    with rasterio.open(
        partial, "w", driver="GTiff", width=window.width, height=window.height,
        count=len(bands), dtype=dtype, crs=GRID_CRS, nodata=float("nan"), compress="deflate",
        tiled=True, transform=from_origin(window.left, window.top, CELL_SIZE_M, CELL_SIZE_M),
        BIGTIFF="IF_SAFER",
    ) as dst:  # fmt: skip
        for k, (name, data) in enumerate(bands.items(), start=1):
            dst.write(data.astype(dtype), k)
            dst.set_band_description(k, name)
        dst.update_tags(**tags)
    partial.rename(path)


def stage_mosaic() -> dict:
    free_before = check_free()
    t0 = time.time()
    window = pnw_window()
    country, eco = read_mask(MASK, window)
    study, side = cells_in_study(window, country, eco)
    del country, eco
    box = in_box(window)
    pnw_study = study & box
    tags = {"label": LABEL, "box": "40 to 49 N, 111 to 125 W (cell centre)",
            "licence": DATA_LICENCE, "dispatch": "Forager RECORD -772"}  # fmt: skip

    def tree_file(key):
        return tree_file_for(TREES, US_HALF, key)[0]

    states = tile_states(window, TREE_N, lambda k: tree_file_for(TREES, US_HALF, k)[1])
    bands, missing = {}, None
    for b in TREE_BANDS:
        bands[b], m = assemble(window, TREE_N, tree_file, b)
        missing = m if missing is None else missing
    bands["missing"] = (missing & pnw_study).astype("float32")
    bands["side"] = side.astype("float32")
    bands["pnw_study"] = pnw_study.astype("float32")
    pending = bands["source"] == FLAG_PENDING
    counts_trees = {
        "tile_states_over_window": states,
        "pnw_study_cells": int(pnw_study.sum()),
        "pnw_study_cells_us": int((pnw_study & (side == 1)).sum()),
        "pnw_study_cells_canada": int((pnw_study & (side == 2)).sum()),
        "cells_in_tiles_not_computed_yet": int((missing & pnw_study).sum()),
        "cells_pending_canada": int((pending & pnw_study).sum()),
        "cells_with_total_cover": int((np.isfinite(bands["total_cover_pct"]) & box).sum()),
        **{f"cells_with_{b}": int((np.isfinite(bands[b]) & box).sum())
           for b in TREE_BANDS if b.startswith("share")},
    }  # fmt: skip
    write_band_tif(MOSAIC / "trees_pnw.tif", window, bands, tags)
    del bands
    soil, soil_missing = assemble(window, SOIL_N, lambda k: _soil_file(k), "ph_mean_0_30cm")
    frac, _ = assemble(window, SOIL_N, lambda k: _soil_file(k), "valid_fraction_mean")
    write_band_tif(MOSAIC / "soil_pnw.tif", window, {"ph_mean_0_30cm": soil,
                   "valid_fraction_mean": frac}, tags)  # fmt: skip
    counts_soil = {
        "pnw_study_cells": int(pnw_study.sum()),
        "cells_with_mean": int((np.isfinite(soil) & box).sum()),
        "cells_in_tiles_not_computed_yet": int((soil_missing & pnw_study).sum()),
    }
    summary = {"stage": "mosaic", "seconds": round(time.time() - t0, 1),
               "window": [window.left, window.bottom, window.right, window.top],
               "free_bytes_before": free_before, "trees": counts_trees, "soil": counts_soil,
               "files": {p.name: p.stat().st_size for p in MOSAIC.glob("*.tif")}}  # fmt: skip
    (OUT / "mosaic.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def _soil_file(key: str):
    p = SOIL / f"soil_{key}.tif"
    return p if p.exists() else None


def _read(name: str, bands: list[str]) -> tuple[dict, GridWindow]:
    with rasterio.open(MOSAIC / name) as ds:
        names = list(ds.descriptions)
        t = ds.transform
        left, top = int(round(t.c)), int(round(t.f))
        window = GridWindow(left, top - ds.height * CELL_SIZE_M, left + ds.width * CELL_SIZE_M,
                            top)  # fmt: skip
        return {b: ds.read(names.index(b) + 1) for b in bands}, window


def boundary_lines(window: GridWindow | None = None) -> list[np.ndarray]:
    """US and Canadian state and province outlines from the CEC file, as (lon, lat) arrays,
    cut to the box with a 0.5 degree margin, a point kept about every 1 km."""
    cols = read_dbf_columns(POLITICAL.with_suffix(".dbf"), ("COUNTRY",))
    inverse = Transformer.from_crs(CEC_LAEA, _CEC_LONLAT, always_xy=True)
    m = 0.5
    out = []
    for rings, country in zip(read_shapefile(POLITICAL), cols["COUNTRY"], strict=True):
        if country not in ("USA", "CAN"):
            continue
        for ring in rings:
            keep = [0]
            for k in range(1, len(ring)):
                if np.hypot(*(ring[k] - ring[keep[-1]])) >= 1000.0 or k == len(ring) - 1:
                    keep.append(k)
            lon, lat = inverse.transform(ring[keep, 0], ring[keep, 1])
            lon, lat = np.asarray(lon), np.asarray(lat)
            inside = ((lon >= PNW_BOX.west - m) & (lon <= PNW_BOX.east + m)
                      & (lat >= PNW_BOX.south - m) & (lat <= PNW_BOX.north + m))  # fmt: skip
            run = []
            for k in range(len(lon)):
                if inside[k]:
                    run.append((float(lon[k]), float(lat[k])))
                elif run:
                    if len(run) > 1:
                        out.append(np.array(run))
                    run = []
            if len(run) > 1:
                out.append(np.array(run))
    return out


STRIDE = 4  # one image pixel per 4 x 4 cells (1 km)


def stage_images() -> dict:
    check_free()
    t0 = time.time()
    trees, window = _read("trees_pnw.tif", ["total_cover_pct", "share_Pseudotsuga",
                                            "share_Tsuga", "source", "missing"])  # fmt: skip
    soil, _ = _read("soil_pnw.tif", ["ph_mean_0_30cm"])
    rows = np.arange(STRIDE // 2, window.height, STRIDE)
    cols = np.arange(STRIDE // 2, window.width, STRIDE)
    box = in_box(window)[np.ix_(rows, cols)]
    to_lonlat = Transformer.from_crs(GEOGRAPHIC_CRS, GRID_CRS, always_xy=True)

    def pix(lon, lat):
        x, y = to_lonlat.transform(lon, lat)
        return ((np.asarray(x) - window.left) / CELL_SIZE_M - STRIDE // 2) / STRIDE + 0.5, (
            (window.top - np.asarray(y)) / CELL_SIZE_M - STRIDE // 2
        ) / STRIDE + 0.5

    lines = []
    for line in boundary_lines():
        x, y = pix(line[:, 0], line[:, 1])
        lines.append(list(zip(x.tolist(), y.tolist(), strict=True)))
    places = [(n, *(float(v) for v in pix(lon, lat))) for n, lon, lat in PLACES]
    pending = (trees["source"] == FLAG_PENDING)[np.ix_(rows, cols)] & box
    missing = (trees["missing"] > 0)[np.ix_(rows, cols)] & box
    written = {}
    for name, spec in LAYERS.items():
        src = soil if spec["mosaic"] == "soil" else trees
        v = src[spec["band"]][np.ix_(rows, cols)].astype("float64") * spec.get("scale", 1.0)
        v[~box] = np.nan
        rgba = ramp(v, *spec["range"])
        extra = []
        if spec["mosaic"] == "trees":
            rgba = paint(rgba, pending, PENDING_RGBA)
            rgba = paint(rgba, missing, MISSING_RGBA)
            extra.append(LegendEntry(PENDING_RGBA, "Canada: not computed yet, waits for the "
                                     "Canadian tree data (SCANFI)"))  # fmt: skip
            if missing.any():
                extra.append(LegendEntry(MISSING_RGBA, "Not computed yet: a border tile held "
                                         "back by a coastline question"))  # fmt: skip
            if spec["band"].startswith("share"):
                extra.append(LegendEntry((0, 0, 0, 0), "Blank where canopy cover is under 10%"))
        svg = svg_image(png_bytes(rgba), len(cols), len(rows), spec["title"],
                        spec["subtitle"] + "; box 40 to 49 N, 111 to 125 W",
                        (*spec["range"], spec["unit"]), extra, SOURCES[spec["mosaic"]], lines,
                        places)  # fmt: skip
        path = OUT / "images" / f"pnw-{name}.svg"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg)
        written[path.name] = path.stat().st_size
    summary = {"stage": "images", "seconds": round(time.time() - t0, 1), "files": written,
               "image_pixels": [len(cols), len(rows)], "cells_per_pixel": STRIDE * STRIDE,
               "pending_pixels": int(pending.sum()),
               "missing_pixels": int(missing.sum())}  # fmt: skip
    (OUT / "images.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


PMTILES_PENDING = 255  # grey byte of a pending Canadian cell in a tree archive (alpha 255)
PMTILES_MISSING = 254  # grey byte of a US cell whose tile is not computed yet (alpha 255)


def stage_pmtiles(only: str | None) -> dict:
    t0 = time.time()
    out = {}
    for name, spec in LAYERS.items():
        if only and name != only:
            continue
        check_free()
        bands = ([spec["band"], "source", "missing"] if spec["mosaic"] == "trees"
                 else [spec["band"]])  # fmt: skip
        src, window = _read(f"{spec['mosaic']}_pnw.tif", bands)
        values = src[spec["band"]].astype("float64") * spec.get("scale", 1.0)
        box = in_box(window)
        values[~box] = np.nan
        merc = mercator_window_for(window)
        m = master_to_mercator_nearest(values, window, merc)
        del values
        if spec["kind"] == "ph":
            grey, alpha = encode_ph_byte(m)
            encoding = "grey = floor(pH * 10 + 0.5); alpha 0 = no data"
        else:
            grey, alpha = encode_percent_byte(m)
            encoding = (f"grey = floor(percent * 2 + 0.5), 0 to 200; grey {PMTILES_PENDING} with "
                        "alpha 255 = Canada, pending SCANFI; grey "
                        f"{PMTILES_MISSING} with alpha 255 = tile not computed yet; "
                        "alpha 0 = no data")  # fmt: skip
            pend = (src["source"] == FLAG_PENDING) & box
            p = master_to_mercator_nearest(pend.astype("float64"), window, merc)
            grey[p == 1] = PMTILES_PENDING
            alpha[p == 1] = 255
            miss = (src["missing"] > 0) & box
            q = master_to_mercator_nearest(miss.astype("float64"), window, merc)
            grey[q == 1] = PMTILES_MISSING
            alpha[q == 1] = 255
        del m
        meta = {"name": f"pnw-{name}", "description": f"{spec['title']}. {LABEL}",
                "attribution": " | ".join(SOURCES[spec["mosaic"]]), "licence": DATA_LICENCE,
                "label": LABEL, "encoding": encoding, "unit": spec["unit"],
                "dispatch": "Forager RECORD -772"}  # fmt: skip
        arch = OUT / "pmtiles"
        arch.mkdir(parents=True, exist_ok=True)
        header, _ = write_archive(grey, alpha, merc, arch / f"pnw-{name}.mbtiles",
                                  arch / f"pnw-{name}.pmtiles", meta)  # fmt: skip
        (arch / f"pnw-{name}.mbtiles").unlink()
        out[name] = {"bytes": (arch / f"pnw-{name}.pmtiles").stat().st_size,
                     "min_zoom": header.get("min_zoom"),
                     "max_zoom": header.get("max_zoom")}  # fmt: skip
    summary = {"stage": "pmtiles", "seconds": round(time.time() - t0, 1), "archives": out}
    (OUT / f"pmtiles{'-' + only if only else ''}.json").write_text(
        json.dumps(summary, indent=1) + "\n"
    )
    return summary


def stage_lines() -> dict:
    lines = boundary_lines()
    gj = {"type": "FeatureCollection", "attribution": SOURCES["soil"][1], "features": [
        {"type": "Feature", "properties": {},
         "geometry": {"type": "LineString",
                      "coordinates": [[round(x, 4), round(y, 4)] for x, y in line]}}
        for line in lines]}  # fmt: skip
    path = OUT / "lines.geojson"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(gj, separators=(",", ":")))
    return {"stage": "lines", "lines": len(lines), "bytes": path.stat().st_size}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=["mosaic", "images", "pmtiles", "lines"])
    p.add_argument("--layer", default=None, choices=list(LAYERS))
    args = p.parse_args()
    if not DRIVE.is_dir():
        sys.exit("flash drive not mounted")
    OUT.mkdir(parents=True, exist_ok=True)
    if args.stage == "mosaic":
        log(stage_mosaic())
    elif args.stage == "images":
        log(stage_images())
    elif args.stage == "pmtiles":
        log(stage_pmtiles(args.layer))
    else:
        log(stage_lines())


if __name__ == "__main__":
    main()

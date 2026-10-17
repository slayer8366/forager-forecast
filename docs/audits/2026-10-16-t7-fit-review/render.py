"""Q5: render the two output rasters to PNG for review (never published).

Images, under this folder:
  habitat_overview.png   1.25 km pixels (every 5th cell), score as its percentile among shaded cells,
                         dark purple (low) to yellow (high); codes 2 to 6 in flat colours.
  applicability_overview.png  the codes alone, 1.25 km pixels (code 1 green).
  searched_overlay.png   the habitat overview with shaded cells OUTSIDE T6's effort frame drawn
                         in a separate (blue-green) ramp, so forest no one searched stands out.
  crop_*.png             full-resolution (250 m) crops at named places.
Legend: code 0 white, 2 red, 3 pale blue, 4 light grey, 5 tan, 6 mid blue.
Also writes render.json with simple stripe and seam measures."""

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.io import MemoryFile

sys.path.insert(0, str(Path(__file__).parent))
import common as c  # noqa: E402

HERE = Path(__file__).parent
OUTD = Path("/mnt/work/Zynergy/forecast-data/t7/pnw-2026-10-17")
with rasterio.open(OUTD / "relative_habitat_pnw.tif") as d:
    score = d.read(1)
    tr = d.transform
with rasterio.open(OUTD / "applicability_pnw.tif") as d:
    code = d.read(1)
H, W = score.shape
fin = np.isfinite(score)
srt = np.sort(score[fin])
pct = np.full(score.shape, np.nan, np.float32)
pct[fin] = np.searchsorted(srt, score[fin]) / len(srt)

STOPS = np.array([[48, 18, 59], [64, 67, 135], [41, 120, 142], [34, 168, 132], [122, 209, 81],
                  [253, 231, 37]], float)
STOPS2 = np.array([[8, 29, 88], [37, 52, 148], [65, 182, 196], [199, 233, 180]], float)
FLAT = {0: (255, 255, 255), 2: (220, 30, 30), 3: (200, 225, 245), 4: (215, 215, 215),
        5: (210, 180, 140), 6: (110, 150, 210)}


def ramp(p, stops):
    p = np.clip(p, 0, 1) * (len(stops) - 1)
    i = np.minimum(np.floor(p).astype(int), len(stops) - 2)
    f = (p - i)[..., None]
    return (stops[i] * (1 - f) + stops[i + 1] * f).astype(np.uint8)


def rgb(pct_, code_, alt=None):
    out = np.zeros(code_.shape + (3,), np.uint8)
    for k, col in FLAT.items():
        out[code_ == k] = col
    ok = np.isfinite(pct_)
    out[ok] = ramp(pct_[ok], STOPS)
    if alt is not None:
        m = ok & alt
        out[m] = ramp(pct_[m], STOPS2)
    return out


def write_png(path, arr):
    h, w, _ = arr.shape
    with MemoryFile() as mf:
        with mf.open(driver="PNG", width=w, height=h, count=3, dtype="uint8", ZLEVEL=9) as ds:
            for b in range(3):
                ds.write(arr[..., b], b + 1)
        path.write_bytes(mf.read())


s = 5
write_png(HERE / "habitat_overview.png", rgb(pct[::s, ::s], code[::s, ::s]))
codes_only = np.zeros(code[::s, ::s].shape + (3,), np.uint8)
for k, col in {**FLAT, 1: (40, 140, 60)}.items():
    codes_only[code[::s, ::s] == k] = col
write_png(HERE / "applicability_overview.png", codes_only)

# frame overlay: weather cell of each 1 km sample pixel centre, in T6's frame or not
rows = np.arange(0, H, s)
cols = np.arange(0, W, s)
xs = tr.c + (cols + 0.5) * 250
ys = tr.f - (rows + 0.5) * 250
gx, gy = np.meshgrid(xs, ys)
lon, lat = Transformer.from_crs("ESRI:102008", "EPSG:4269", always_xy=True).transform(gx, gy)
k = c.key(np.floor(lat * 10 + 0.5).astype(int), np.floor(lon * 10 + 0.5).astype(int))
frame = np.isin(k, c.frame_keys("all"))
write_png(HERE / "searched_overlay.png", rgb(pct[::s, ::s], code[::s, ::s], alt=~frame))

sub = pct[::s, ::s]
shaded = np.isfinite(sub)
info = {"shape": [H, W], "shaded_cells": int(fin.sum()),
        "shaded_1km_samples": int(shaded.sum()),
        "shaded_1km_samples_outside_frame": int((shaded & ~frame).sum()),
        "mean_pct_in_frame": float(np.nanmean(np.where(frame, sub, np.nan))),
        "mean_pct_outside_frame": float(np.nanmean(np.where(~frame, sub, np.nan)))}

# seams: mean absolute difference of the percentile across each tile edge (every 256 cells,
# tiles aligned to the master lattice) against the same measure one cell away from an edge
col0 = int(round(tr.c / 250))
row_top = int(round(tr.f / 250))


def edge_jumps(a, axis):
    d = np.abs(np.diff(a, axis=axis))
    n = a.shape[axis]
    idx = np.arange(n - 1)
    if axis == 1:
        world = col0 + idx + 1  # column index of the right-hand cell
    else:
        world = row_top - 1 - idx  # row of the upper cell; edge below it
        world = world  # lattice row of upper cell; edge when (world) % 256 == 0
    at_edge = (world % 256) == 0
    near = ((world - 1) % 256) == 0
    take = (lambda m: d[:, m]) if axis == 1 else (lambda m: d[m, :])
    return float(np.nanmean(take(at_edge))), float(np.nanmean(take(near)))


info["seam_cols_edge_vs_offset"] = edge_jumps(pct, 1)
info["seam_rows_edge_vs_offset"] = edge_jumps(pct, 0)

# stripes: correlation of column means / row means of the percentile with a period-2..8 pattern
cm = np.nanmean(pct, axis=0)
rm = np.nanmean(pct, axis=1)
info["column_mean_lag1_absdiff"] = float(np.nanmean(np.abs(np.diff(cm))))
info["row_mean_lag1_absdiff"] = float(np.nanmean(np.abs(np.diff(rm))))

to_g = Transformer.from_crs("EPSG:4269", "ESRI:102008", always_xy=True)
CROPS = {"puget_border": (-122.6, 48.6), "mt_hood": (-121.7, 45.4), "coast_range_or": (-123.6, 44.6),
         "idaho_batholith": (-115.5, 44.5), "klamath": (-123.3, 42.0)}
for name, (lo, la) in CROPS.items():
    x, y = to_g.transform(lo, la)
    cc_ = int((x - tr.c) / 250)
    rr_ = int((tr.f - y) / 250)
    r0, c0 = max(0, rr_ - 300), max(0, cc_ - 300)
    write_png(HERE / f"crop_{name}.png", rgb(pct[r0:r0 + 600, c0:c0 + 600],
                                             code[r0:r0 + 600, c0:c0 + 600]))
# by-latitude band means of the percentile (north-south pattern), 1 degree bands
bands = {}
for la in range(40, 49):
    m = (lat >= la) & (lat < la + 1) & shaded
    bands[f"{la}-{la + 1}N"] = float(sub[m].mean()) if m.any() else None
info["mean_pct_by_lat_band"] = bands
lbands = {}
for lo in range(-125, -111):
    m = (lon >= lo) & (lon < lo + 1) & shaded
    lbands[f"{lo}..{lo + 1}E"] = float(sub[m].mean()) if m.any() else None
info["mean_pct_by_lon_band"] = lbands
(HERE / "render.json").write_text(json.dumps(info, indent=1) + "\n")
print(json.dumps(info, indent=1))

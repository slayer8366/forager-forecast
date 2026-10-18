"""Q6: render the new habitat raster + applicability codes, the judged 2026-10-16 raster, and the rank
difference to PNG (own PNG writer; no plotting library in the environment). Scores are drawn as
percentile ranks among shaded cells of the same map. Output stays in this folder (a reviewer's evidence
folder), never published."""
import zlib, struct, json, sys
import numpy as np, rasterio
from scipy.stats import rankdata, spearmanr

NEW = "/mnt/work/Zynergy/forecast-data/t7/refit/outputs/"
OLD = "/mnt/work/Zynergy/forecast-data/t7/pnw-2026-10-17/"

def png(path, rgb):
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[i].tobytes() for i in range(h))
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))

STOPS = np.array([[68, 1, 84], [59, 82, 139], [33, 145, 140], [94, 201, 98], [253, 231, 37]], float)
def ramp(t):
    t = np.clip(t, 0, 1) * (len(STOPS) - 1); i = np.minimum(t.astype(int), len(STOPS) - 2); f = (t - i)[..., None]
    return (STOPS[i] * (1 - f) + STOPS[i + 1] * f).astype(np.uint8)

def ranks(a):
    m = np.isfinite(a); r = np.full(a.shape, np.nan)
    r[m] = (rankdata(a[m]) - 1) / (m.sum() - 1)
    return r

new = rasterio.open(NEW + "relative_habitat_pnw.tif").read(1); newc = rasterio.open(NEW + "applicability_pnw.tif").read(1)
old = rasterio.open(OLD + "relative_habitat_pnw.tif").read(1); oldc = rasterio.open(OLD + "applicability_pnw.tif").read(1)
print(new.shape, old.shape, "finite new/old", int(np.isfinite(new).sum()), int(np.isfinite(old).sum()))
both = np.isfinite(new) & np.isfinite(old)
print("rank corr over both-shaded", spearmanr(new[both], old[both]).statistic)
rn, ro = ranks(new), ranks(old)
CODE_COL = {0: (255, 255, 255), 2: (200, 120, 120), 3: (170, 170, 170), 4: (225, 225, 205), 5: (205, 215, 225), 6: (150, 190, 230)}
def paint(r, codes):
    img = np.zeros(r.shape + (3,), np.uint8); img[:] = 255
    for c, col in CODE_COL.items(): img[codes == c] = col
    fin = np.isfinite(r); img[fin] = ramp(r[fin]); return img
S = 5  # every 5th cell: keeps each PNG under the repository 1 MB file limit (an earlier run at 3 was viewed first)
def down(img):  # take every S-th cell (nearest), keeps colours exact
    return img[::S, ::S]
png("map_new_rank.png", down(paint(rn, newc)))
png("map_old_rank.png", down(paint(ro, oldc)))
diff = np.full(new.shape, np.nan); diff[both] = rn[both] - ro[both]
d = np.zeros(new.shape + (3,), np.uint8); d[:] = 255
for c, col in CODE_COL.items(): d[newc == c] = col
t = np.clip((diff[both] + 0.5) / 1.0, 0, 1)  # -0.5..+0.5 rank shift
red = np.stack([np.where(t > .5, 255, 255 * 2 * t), np.where(t > .5, 255 * 2 * (1 - t), 255 * 2 * t), np.where(t > .5, 255 * 2 * (1 - t), 255)], -1)
d[both] = red.astype(np.uint8)
png("map_rank_shift_red_up_blue_down.png", down(d))
json.dump({"codes_new": {int(k): int(v) for k, v in zip(*np.unique(newc, return_counts=True))},
           "codes_old": {int(k): int(v) for k, v in zip(*np.unique(oldc, return_counts=True))},
           "shape": list(new.shape), "downsample": S,
           "rank_shift_percentiles": {str(p): float(np.percentile(diff[both], p)) for p in (1, 5, 25, 50, 75, 95, 99)},
           "abs_shift_gt_0.25_share": float((np.abs(diff[both]) > .25).mean())}, open("06_results.json", "w"), indent=1)
print(open("06_results.json").read())

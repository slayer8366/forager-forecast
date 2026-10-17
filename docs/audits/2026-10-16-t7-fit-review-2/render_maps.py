"""Review 2, question 5: the two output rasters rendered to PNG with my own writer, plus a third
image of where the map and the effort surface disagree. Pixels are 5 x 5 cells (1.25 km) so each
file stays under the repository's 1 MiB guard. Written, then looked at and described in words.

Project code used: ``cell_lonlat`` (grid geometry) through ``weather_cells_for_window`` for the
frame outline. Everything else is here.
"""

import csv
import json
import struct
import sys
import zlib
from pathlib import Path

import numpy as np
import rasterio

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))
from forager_forecast.pnw import pnw_window  # noqa: E402
from forager_forecast.t7.keying import weather_cells_for_window  # noqa: E402

OUTS = Path("/mnt/work/Zynergy/forecast-data/t7/pnw-2026-10-17")
WORK = Path("/mnt/work/Zynergy/forecast-data/t7/fit")
ROWS = Path("/mnt/work/Zynergy/forecast-data/t7-review-2")
T6 = Path.home() / "Zynergy/forager-forecast-t6/data/t6/all/cell_level.csv"
STEP = 5


def png(path: Path, rgb: np.ndarray) -> None:
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[i].tobytes() for i in range(h))
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def pack(lat_t, lon_t):
    return (np.asarray(lat_t, dtype=np.int64) + 1000) * 10_000 + (np.asarray(lon_t, dtype=np.int64) + 2000)


def main():
    with rasterio.open(OUTS / "relative_habitat_pnw.tif") as ds:
        score = ds.read(1)
    with rasterio.open(OUTS / "applicability_pnw.tif") as ds:
        code = ds.read(1)
    window = pnw_window()
    lat_t, lon_t = weather_cells_for_window(window)
    with open(T6, newline="") as f:
        keys = np.array(sorted(pack([int(r["lat_tenths"]) for r in csv.DictReader(f)], [0])), dtype=np.int64)
    with open(T6, newline="") as f:
        rows = list(csv.DictReader(f))
    keys = np.array(sorted(set(pack([int(r["lat_tenths"]) for r in rows], [int(r["lon_tenths"]) for r in rows]).tolist())))
    frame = np.isin(pack(lat_t, lon_t), keys)
    summary = {"shape": list(score.shape), "code_counts": {int(k): int(v) for k, v in zip(*np.unique(code, return_counts=True))},
               "finite_scores": int(np.isfinite(score).sum()),
               "finite_scores_equal_code1": bool(np.array_equal(np.isfinite(score), code == 1))}
    ok = np.isfinite(score)
    summary["score_quantiles"] = np.quantile(score[ok], [0, .05, .25, .5, .75, .95, 1]).tolist()
    s = score[::STEP, ::STEP]; c = code[::STEP, ::STEP]; fr = frame[::STEP, ::STEP]
    h, w = s.shape
    # 1. the habitat map: five equal-count classes of the shaded cells, codes 2 to 6 in greys
    rgb = np.full((h, w, 3), 255, np.uint8)
    greys = {0: 255, 2: 150, 3: 225, 4: 236, 5: 205, 6: 245}
    for k, g in greys.items():
        rgb[c == k] = g
    okk = np.isfinite(s)
    edges = np.quantile(score[ok], [0.2, 0.4, 0.6, 0.8])
    cls = np.digitize(s, edges)
    greens = [(237, 248, 233), (186, 228, 179), (116, 196, 118), (49, 163, 84), (0, 109, 44)]
    for k, col in enumerate(greens):
        rgb[okk & (cls == k)] = col
    edge = np.zeros_like(fr)
    edge[1:, :] |= fr[1:, :] != fr[:-1, :]; edge[:, 1:] |= fr[:, 1:] != fr[:, :-1]
    rgb[edge] = (120, 60, 160)
    png(HERE / "map_relative_habitat.png", rgb)
    summary["class_edges"] = edges.tolist()
    # 2. the applicability codes, one colour each
    pal = {0: (255, 255, 255), 1: (60, 140, 60), 2: (220, 40, 40), 3: (255, 230, 120), 4: (225, 225, 225),
           5: (120, 120, 220), 6: (170, 215, 255)}
    rgb2 = np.zeros((h, w, 3), np.uint8)
    for k, col in pal.items():
        rgb2[c == k] = col
    rgb2[edge] = (120, 60, 160)
    png(HERE / "map_applicability.png", rgb2)
    # 3. map rank against effort rank, inside the frame: blue = map ranks higher than effort,
    #    brown = effort ranks higher; out-of-frame shaded cells in green by map rank
    tab = np.load(WORK / "table.npz")
    cell_id = tab["cell_id"]
    le = np.load(ROWS / "log_effort_all.npy")
    sc = np.load(ROWS / "score_refit.npy")
    ids = cell_id.astype(np.int64)
    col = (ids & 0xFFFF) - (1 << 15); row = (ids >> 16) - (1 << 15)
    rr = window.top // 250 - 1 - row; cc = col - window.left // 250
    insd = code[rr, cc] == 1
    from scipy.stats import rankdata
    fin = np.isfinite(le) & insd
    d = np.full(len(ids), np.nan)
    d[fin] = rankdata(sc[fin]) / fin.sum() - rankdata(le[fin]) / fin.sum()
    img = np.full(code.shape, np.nan, np.float32)
    img[rr[fin], cc[fin]] = d[fin]
    dd = img[::STEP, ::STEP]
    rgb3 = np.full((h, w, 3), 255, np.uint8)
    for k, g in greys.items():
        rgb3[c == k] = g
    oof = okk & ~np.isfinite(dd)
    for k, col_ in enumerate(greens):
        rgb3[oof & (cls == k)] = col_
    fd = np.isfinite(dd)
    v = np.clip(dd[fd] / 0.5, -1, 1)
    r_ = np.where(v > 0, 255 * (1 - v), 255).astype(np.uint8); g_ = (255 * (1 - np.abs(v))).astype(np.uint8)
    b_ = np.where(v < 0, 255 * (1 + v), 255).astype(np.uint8)
    # blue for map > effort, brown/orange for effort > map
    rgb3[fd] = np.column_stack([np.where(v > 0, 255 * (1 - v), 255), np.where(v > 0, 255 * (1 - v), 255 * (1 + v) * 0.6 + 100 * (-v)), np.where(v > 0, 255, 255 * (1 + v))]).astype(np.uint8)
    rgb3[edge] = (120, 60, 160)
    png(HERE / "map_rank_minus_effort_rank.png", rgb3)
    summary["rank_diff_quantiles_in_frame"] = np.nanquantile(d, [0, .05, .25, .5, .75, .95, 1]).tolist()
    for p in ("map_relative_habitat.png", "map_applicability.png", "map_rank_minus_effort_rank.png"):
        summary[p] = (HERE / p).stat().st_size
    (HERE / "render_maps.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()

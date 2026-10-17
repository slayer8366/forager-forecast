"""Review 2, step 1: rebuild the fit's training rows with my own code and compare to the report.

Reads (read only): the fit's work dir table (cell ids, weather keys, level III codes, tile codes),
V9's presence files, T6's stored surface. Writes only to OUT (my own folder on /mnt/work) and
prints a JSON summary to stdout.

Project code used, and why: ``EffortSurface.read`` and ``static_effort`` (the T6 surface's own
reader: the value of log effort is T6's, not under review here); ``frame_weeks``. Everything else
(eligibility, genus units and weights, the background draw, the key packing, tile code lookup)
is written here from the rules as read.
"""

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from forager_forecast.cells import Cell  # noqa: E402
from forager_forecast.effort import EffortSurface  # noqa: E402
from forager_forecast.t7.keying import static_effort  # noqa: E402

WORK = Path("/mnt/work/Zynergy/forecast-data/t7/fit")
V9 = Path("/mnt/work/Zynergy/forecast-data/t7/v9")
T6 = Path.home() / "Zynergy/forager-forecast-t6/data/t6"
OUT = Path("/mnt/work/Zynergy/forecast-data/t7-review-2")
SEED = 20260918
N_BACKGROUND = 500_000
MIN_ALONE = 30
POOLED = "(pooled)"
TILE = 256


def pack(lat_t, lon_t):
    # the table's key encoding (keying.py:30-39), reproduced so the join works
    return (np.asarray(lat_t, dtype=np.int64) + 1000) * 10_000 + (np.asarray(lon_t, dtype=np.int64) + 2000)


def tile_code(cell_ids, codes):
    ids = np.asarray(cell_ids, dtype=np.int64)
    col = (ids & 0xFFFF) - (1 << 15)
    row = (ids >> 16) - (1 << 15)
    out = np.zeros(len(ids), dtype=np.uint8)
    for k in range(len(ids)):
        i, j = col[k] // TILE, row[k] // TILE
        key = f"{TILE}_{i}_{j}"
        if key not in codes:
            continue
        out[k] = codes[key][(j + 1) * TILE - 1 - row[k], col[k] - i * TILE]
    return out


def log_effort_by_key(track: str, keys: np.ndarray) -> dict[int, float]:
    lat = keys // 10_000 - 1000
    lon = keys % 10_000 - 2000
    cells = [Cell(int(a), int(b)) for a, b in zip(lat, lon)]
    eff = static_effort(EffortSurface.read(T6 / track), cells)
    return {int(pack(c.lat_tenths, c.lon_tenths)): eff.log(c) for c in eff.total}


def build(name: str, presence_file: Path, track: str, smoke_tenth: bool = False) -> dict:
    tab = np.load(WORK / "table.npz")
    cell_id, wkey, level3 = tab["cell_id"], tab["wkey"], tab["level3"]
    codes = dict(np.load(WORK / "codes.npz"))
    assert np.all(np.diff(cell_id.astype(np.int64)) > 0), "table cell ids not sorted unique"
    keys = np.unique(wkey)
    eff_all = log_effort_by_key("all", keys)
    eff = eff_all if track == "all" else log_effort_by_key(track, keys)

    with open(presence_file, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    p_cell = np.array([int(r["cell_id"]) for r in rows], dtype=np.int64)
    pos = np.clip(np.searchsorted(cell_id, p_cell), 0, len(cell_id) - 1)
    eligible = cell_id[pos] == p_cell
    p_code = tile_code(p_cell, codes)
    assert np.array_equal(eligible, p_code == 1), "eligibility and tile code disagree"
    cell_key = wkey[pos]
    in_frame_p = np.array([int(k) in eff for k in cell_key])
    entering = eligible & in_frame_p
    own_key = pack([int(r["lat_tenths"]) for r in rows], [int(r["lon_tenths"]) for r in rows])
    summary = {
        "run": name, "presence_file": str(presence_file), "track": track,
        "thinned_in_file": len(rows),
        "by_code": {str(k): int(v) for k, v in sorted(Counter(p_code.tolist()).items())},
        "eligible_but_outside_frame": int((eligible & ~in_frame_p).sum()),
        "entering": int(entering.sum()),
        "entering_record_key_differs_from_cell_key": int((entering & (own_key != cell_key)).sum()),
    }
    kept = [r for r, k in zip(rows, entering) if k]
    per_genus = Counter(r["genus"] for r in kept)
    unit_of = {g: (g if n >= MIN_ALONE else POOLED) for g, n in per_genus.items()}
    per_unit = Counter()
    for g, n in per_genus.items():
        per_unit[unit_of[g]] += n
    pw = np.array([1.0 / per_unit[unit_of[r["genus"]]] for r in kept])
    summary["genera_alone"] = sum(1 for u in per_unit if u != POOLED)
    summary["pooled_presences"] = int(per_unit.get(POOLED, 0))
    summary["units"] = len(per_unit)
    summary["presence_total_weight"] = float(pw.sum())

    frame_keys = np.fromiter(eff_all.keys(), dtype=np.int64)
    in_frame = np.isin(wkey, frame_keys)
    summary["background_pool"] = int(in_frame.sum())
    pool = np.unique(cell_id[in_frame].astype(np.uint32))
    picks = np.random.default_rng(SEED).choice(len(pool), size=N_BACKGROUND, replace=False)
    bcells = np.sort(pool[picks])
    summary["background_sha256"] = hashlib.sha256(bcells.astype("<u4").tobytes()).hexdigest()
    bi = np.searchsorted(cell_id, bcells)
    assert np.array_equal(cell_id[bi], bcells)
    b_has = np.array([int(k) in eff for k in wkey[bi]])
    summary["background_dropped_no_track_effort"] = int((~b_has).sum())
    bi = bi[b_has]
    if smoke_tenth:
        bi = bi[::10]
    bw = np.full(len(bi), pw.sum() / len(bi))
    pi = pos[entering]
    idx = np.concatenate([pi, bi])
    y = np.concatenate([np.ones(len(pi)), np.zeros(len(bi))])
    w = np.concatenate([pw, bw])
    blocks = level3[idx].astype(np.int64)
    clusters = wkey[idx].astype(np.int64)
    year = np.concatenate([np.array([int(r["year"]) for r in kept]), np.zeros(len(bi), np.int64)])
    genus = np.array([r["genus"] for r in kept] + [""] * len(bi))
    le = np.array([eff[int(k)] for k in wkey[idx]])
    summary["n_background"] = int(len(bi))
    summary["n_rows"] = int(len(idx))
    summary["held_effort_median_log_effort"] = float(np.median(np.array(list(eff.values()))))
    summary["effort_cells_with_eligible"] = len(eff)
    summary["blocks_in_fit"] = sorted(int(b) for b in np.unique(blocks))
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(OUT / f"rows_{name}.npz", idx=idx, y=y, w=w, blocks=blocks, clusters=clusters,
             year=year, genus=genus, log_effort=le, pi=pi, bi=bi)
    return summary


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "main"
    files = {
        "main": (V9 / "presences_main.csv", "all"),
        "side": (V9 / "presences_side.csv", "all"),
        "licence": (V9 / "presences_licence_track.csv", "cc"),
        "comparison": (V9 / "presences_comparison.csv", "all"),
    }
    path, track = files[which]
    print(json.dumps(build(which, path, track), indent=1))

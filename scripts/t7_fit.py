"""T7 P3 to P10: the full PNW fit, under D133 to D141 and D144 (Forager RECORD -1062, -1081).

Usage:
  python scripts/t7_fit.py table   <work dir> [--access]
  python scripts/t7_fit.py timing  <work dir> <evidence dir> --access-monotone {-1,0,1}
  python scripts/t7_fit.py fit     <work dir> <evidence dir> --access-monotone {-1,0,1}
                                   --out <new folder> [--threads N] [--smoke]
  python scripts/t7_fit.py figures <work dir> <evidence dir>

The re-fit (dispatch 2026-10-17-T7R, Forager RECORD -1182, -1183): ``table --access`` stores the
access bands beside the features; ``timing`` and ``fit`` put the road band (``dist_road_m``) in
every model beside effort, in effort's interaction group, with the monotone direction passed on the
command line (an open ruling, never defaulted); ``fit`` runs the trails side check and the
saprotroph group's runs among the side runs, evaluates P10b (D145) with conditions 1 to 3 and
reports P10 (D140) beside it with no verdict, and writes the map to ``--out``, which may not be
inside the judged run's folders. ``fit`` at the commit before the re-fit (5c1a9df) is the judged
run's code.

``table`` reads every tree tile of the PNW box with its flags, soil tile, the T6b mask and the
level III file (all read only, on the flash drive), through ``t7/predictors.read_tile`` (P4 as
ruled), and stores the eligible cells (cell id, the 18 features, weather cell, level III code)
and each tile's code array in the work dir, with every input file's sha256 checked against the
T6b manifest's line for it.

``timing`` assembles the training table (presences from V9's thinned main run, P3's background)
and times ONE outer fold of the base model, the inner tuning included, then projects the run.

``fit`` runs the ladder (P7, D138), the comparisons A and B, the bootstrap, the forested-block
figures, the side runs, the area of applicability (P8), the map pass and the outputs (P9) to the
work dir, and writes the block report and every figure to the evidence dir. Beside every pooled
AUC it reports base minus B, the within-weather-cell AUCs and the block-clustered intervals (T7
part A, Forager RECORD -1156).

``figures`` recomputes those beside-figures from a finished fit's cache, and never fits.

Never writes to the flash drive or to the repository except the evidence dir.
"""

from __future__ import annotations

import csv
import hashlib
import json
import resource
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import rasterio

from forager_forecast.cells import Cell
from forager_forecast.effort import EffortSurface
from forager_forecast.grid import CELL_SIZE_M, GridWindow, cell_from_id
from forager_forecast.pnw import PNW_BOX, pnw_window
from forager_forecast.t4_layer import box_mask
from forager_forecast.t6b_layers import tiles_over, us_half_names
from forager_forecast.t6b_mask import SIDE_US, cells_in_study, read_mask
from forager_forecast.t7 import background as bg
from forager_forecast.t7 import folds as fd
from forager_forecast.t7 import metrics as mt
from forager_forecast.t7 import model as md
from forager_forecast.t7.aoa import fit_aoa
from forager_forecast.t7.ecoregions import burn_level3, read_level3
from forager_forecast.t7.keying import pack, static_effort
from forager_forecast.t7.predictors import (
    ACCESS_BANDS,
    ACCESS_MAIN_BANDS,
    BASE_BANDS,
    CANDIDATE_BANDS,
    CODE_IN,
    CODE_LEGEND,
    CODE_OUT_OF_AOA,
    FEATURES,
    LEFT_OUT_BANDS,
    SHARE_FLOOR,
    read_tile,
)
from forager_forecast.t7.presences import POOLED, genus_weights

REPO = Path(__file__).resolve().parent.parent
T6B = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b")
MASK = T6B / "mask.tif"
TREES, US_HALF, SOIL = T6B / "tiles/trees", T6B / "tiles/trees_us_half", T6B / "tiles/soil"
MANIFEST = T6B / "manifest.jsonl"
LEVEL3 = (
    T6B / "sources/terr_ecoregions_v2_level_iii_shapefile/NA_TerrEcoregions_III/data"
    / "NA_Terrestrial_Ecoregions_v2_level3.shp"
)  # fmt: skip
T6 = Path.home() / "Zynergy/forager-forecast-t6/data/t6"
T6_SHA = REPO / "docs/audits/2026-10-06-t6-fit/stored_surface_sha256.txt"
V9 = Path("/mnt/work/Zynergy/forecast-data/t7/v9")
V9C = Path("/mnt/work/Zynergy/forecast-data/t7/v9c")
# T7 part B's access layer (D149), as its manifest records it (outputs, access_pnw.tif)
ACCESS = Path("/mnt/work/Zynergy/forecast-data/access/pnw-2026-10-17/access_pnw.tif")
ACCESS_SHA256 = "7748fe0b5018a823ef0e41c64b0a8a0f3675951026461c8a39a0f5aa9682d38a"
GRID_FILE = REPO / "docs/audits/2026-10-15-t7-build/tuning_grid.json"
GRID_SHA256 = "7412d90677ef24031005d64797ba6482a94cddec12c1c0288b4183f9c86a45cd"
SEED = 20260918
TILE_N = 256
SIDE_RUNS = (
    ("M2 side run", V9 / "presences_side.csv", "all"),
    ("licence track", V9 / "presences_licence_track.csv", "cc"),
    ("comparison group", V9 / "presences_comparison.csv", "all"),
)


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


class Log:
    def __init__(self, path: Path) -> None:
        self.path = path

    def __call__(self, msg: str) -> None:
        line = f"{now()} {msg}"
        print(line, flush=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=1, ensure_ascii=False, default=str) + "\n",
                    encoding="utf-8")  # fmt: skip


# --- the re-fit's pieces (dispatch 2026-10-17-T7R) -----------------------------------------------

JUDGED = (
    Path("/mnt/work/Zynergy/forecast-data/t7/fit"),
    Path("/mnt/work/Zynergy/forecast-data/t7/pnw-2026-10-17"),
    V9,
    V9C,
)
CONDITION_4_PENDING = "pending: data exist, scoring not yet ruled"


def access_attribution() -> str:
    """The access layer's credit line, as part B's manifest writes it (D148)."""
    return json.loads((ACCESS.parent / "manifest.json").read_text(encoding="utf-8"))["attribution"]


def check_out_dir(path: Path) -> Path:
    """The map's output folder, named by the caller (``--out``). Refuses the judged run's folders
    and anything inside them, and a folder that already holds files: the run never overwrites.
    (The script used to name it ``pnw-<UTC date>``, which on 2026-10-17 is the judged run's.)"""
    path = Path(path)
    resolved = path.resolve()
    for judged in JUDGED:
        j = judged.resolve()
        if resolved == j or j in resolved.parents:
            raise SystemExit(f"{path}: inside the judged run's folder {judged}; never written")
    if path.exists() and any(path.iterdir()):
        raise SystemExit(f"{path}: not empty; the map is written once, into a new folder")
    return path


def map_columns(f, names, full_features, held_effort, held_access):
    """The map pass's model inputs for table rows ``f`` (columns ``names``): the habitat bands as
    read, the cover columns derived, effort and access each held at one value for every cell."""
    con, brd = md.cover_columns(f[:, names.index("share_conifer")],
                                f[:, names.index("share_broadleaf")],
                                f[:, names.index("total_cover_pct")])  # fmt: skip
    cols = {**{n: f[:, k] for k, n in enumerate(names)}, md.EFFORT: np.full(len(f), held_effort),
            md.ACCESS: np.full(len(f), held_access), md.CONIFER_COVER: con,
            md.BROADLEAF_COVER: brd}  # fmt: skip
    return np.column_stack([cols[c] for c in full_features])


def area_of_applicability(data, full_features, gains):
    """P8 on the habitat bands only: effort and access are held for the map, so neither is a
    predictor of the area of applicability (``md.habitat_features``). ``gains``: the final full
    model's gain per feature of ``full_features``."""
    habitat = md.habitat_features(list(full_features))
    hab_gain = np.array([gains[list(full_features).index(f)] for f in habitat])
    return fit_aoa(data.cols(habitat), hab_gain, data.blocks), habitat


def shared_forested_blocks(forested, blocks_a, y_a, blocks_b, y_b, minimum=30):
    """Forested blocks (D139) where both groups have at least ``minimum`` presences (-1173: the
    13 shared forested blocks of the host-specific contrast)."""
    out = []
    for b in sorted(forested):
        na = int(((np.asarray(blocks_a) == b) & (np.asarray(y_a) == 1)).sum())
        nb = int(((np.asarray(blocks_b) == b) & (np.asarray(y_b) == 1)).sum())
        if na >= minimum and nb >= minimum:
            out.append(int(b))
    return out


def p10b_figures(condition_1, condition_2, condition_3, condition_4_status, p10_passes,
                 condition_4=None):  # fmt: skip
    """P10b (D145) as the fit report carries it: the verdict, each condition's figure, and P10
    (D140) beside it with no verdict. Condition 4 is computed only once its scoring is ruled;
    while its data exist and its scoring is not ruled (``CONDITION_4_PENDING``), the verdict is
    never "pass", since D145 requires condition 4 wherever usable data exist."""
    v = mt.p10b(block_clustered_full_minus_b=condition_1, within_cell_full_minus_a=condition_2,
                host_specific_contrast=condition_3, independent_data=None)  # fmt: skip
    verdict = v.verdict
    if condition_4_status == CONDITION_4_PENDING and verdict == "pass":
        verdict = "incomplete: conditions 1 to 3 pass; condition 4 not yet evaluated"
    return {
        "verdict": verdict,
        "conditions": {
            "1_block_clustered_full_minus_B": dd(condition_1),
            "2_within_cell_full_minus_A_block_resampled": dd(condition_2),
            "3_host_specific_contrast": None if condition_3 is None else dd(condition_3),
            "4_independent_data": {"status": condition_4_status},
        },
        "p10_d140": {"passes": bool(p10_passes), "reading": "no verdict"},
    }


# --- table ----------------------------------------------------------------------------------------


def manifest_lines() -> dict:
    lines = {}
    with open(MANIFEST, encoding="utf-8") as f:
        for raw in f:
            d = json.loads(raw)
            if d.get("kind") == "unit":
                lines[(d.get("layer"), d.get("unit"))] = d
    return lines


def tile_files(key: str):
    whole = TREES / f"trees_{key}.tif"
    if whole.exists():
        return whole, TREES / f"trees_flags_{key}.tif", ("trees", key)
    a, b = us_half_names(key)
    if (US_HALF / a).exists():
        return US_HALF / a, US_HALF / b, ("trees-us-half", f"us-half:{key}")
    return None, None, None


def cmd_table(work: Path, access_path: Path | None = None) -> None:
    """``access_path``: T7 part B's access raster (D149). When given, every access band
    (``ACCESS_BANDS``: roads, trails, the nearer of the two) is read through ``read_tile``'s access
    path for each eligible cell and stored as ``access`` (float32, NaN kept, never filled), with
    the file's sha256 checked against ``ACCESS_SHA256`` and the NaN count per band in the meta."""
    work.mkdir(parents=True, exist_ok=True)
    log = Log(work / "table.log")
    if access_path is not None:
        digest = sha256_file(access_path)
        if digest != ACCESS_SHA256:
            raise SystemExit(f"{access_path}: sha256 {digest} is not the recorded {ACCESS_SHA256}")
    t0 = time.monotonic()
    lines = manifest_lines()
    table, polygons = read_level3(LEVEL3)
    window = pnw_window()

    inputs = {"mask": {"path": str(MASK), "sha256": sha256_file(MASK)},
              "level3": {"path": str(LEVEL3), "sha256": sha256_file(LEVEL3)},
              "tiles": {}}  # fmt: skip
    if access_path is not None:
        inputs["access"] = {"path": str(access_path), "sha256": ACCESS_SHA256}
    access_bands = ACCESS_BANDS if access_path is not None else ()
    parts = defaultdict(list)
    codes = {}
    attribution_tree, attribution_soil = set(), set()
    canadian_read = False
    block_study = Counter()  # level III code -> study cells in the box, both sides (D139)
    block_shares = Counter()  # ... of which with every share band defined
    block_study_us = Counter()
    block_shares_us = Counter()
    hash_mismatch = []
    for tile in tiles_over(window, TILE_N):
        tw = tile.window
        study, side = cells_in_study(tw, *read_mask(MASK, tw))
        inbox = study & box_mask(tw, PNW_BOX)
        if not inbox.any():
            continue
        tree, flags, line_key = tile_files(tile.key)
        if tree is None:
            raise SystemExit(f"tile {tile.key}: box study cells but no tree file")
        soil_tiles = tiles_over(tw, 2048)
        if len(soil_tiles) != 1:
            raise SystemExit(f"tile {tile.key}: {len(soil_tiles)} soil tiles")
        soil = SOIL / f"soil_{soil_tiles[0].key}.tif"
        rec = {}
        for path, key in ((tree, line_key), (flags, line_key), (soil, ("soil", soil_tiles[0].key))):
            digest = sha256_file(path)
            want = lines.get(key, {}).get("files", {}).get(path.name)
            rec[path.name] = digest
            if want != digest:
                hash_mismatch.append([path.name, digest, want])
        inputs["tiles"][tile.key] = rec
        cells = read_tile(tile, tree, flags, soil, MASK, PNW_BOX, polygons,
                          access_path=access_path, access_bands=access_bands)  # fmt: skip
        attribution_tree.add(cells.tree_attribution)
        attribution_soil.add(cells.soil_attribution)
        canadian_read |= cells.canadian_values_read
        codes[tile.key] = cells.code
        parts["cell_id"].append(cells.cell_id)
        parts["features"].append(cells.features.astype(np.float32))
        parts["wkey"].append(pack(cells.lat_tenths, cells.lon_tenths))
        parts["level3"].append(cells.level3.astype(np.uint16))
        if access_bands:
            parts["access"].append(cells.access.astype(np.float32))
        # D139's forested share: study cells in the box with every share defined, per block
        l3 = burn_level3(polygons, tw)
        with rasterio.open(tree) as ds:
            names = list(ds.descriptions)
            conifer = ds.read(names.index("share_conifer") + 1)
        has = np.isfinite(conifer)
        for code in np.unique(l3[inbox]):
            sel = inbox & (l3 == code)
            block_study[int(code)] += int(sel.sum())
            block_shares[int(code)] += int((sel & has).sum())
            block_study_us[int(code)] += int((sel & (side == SIDE_US)).sum())
            block_shares_us[int(code)] += int((sel & has & (side == SIDE_US)).sum())
        log(f"tile {tile.key}: {len(cells.cell_id)} eligible, {round(time.monotonic() - t0)} s")
    if hash_mismatch:
        write_json(work / "hash_mismatch.json", hash_mismatch)
        raise SystemExit(f"{len(hash_mismatch)} input files differ from the T6b manifest")
    cell_id = np.concatenate(parts["cell_id"])
    order = np.argsort(cell_id, kind="stable")
    arrays = {
        "cell_id": cell_id[order],
        "features": np.concatenate(parts["features"])[order],
        "wkey": np.concatenate(parts["wkey"])[order],
        "level3": np.concatenate(parts["level3"])[order],
    }
    if access_bands:
        arrays["access"] = np.concatenate(parts["access"])[order]
    np.savez(work / "table.npz", **arrays)
    np.savez_compressed(work / "codes.npz", **{k: v for k, v in codes.items()})
    meta = {
        "features": list(FEATURES),
        "inputs": inputs,
        "attribution_tree": sorted(attribution_tree),
        "attribution_soil": sorted(attribution_soil),
        "canadian_values_read": canadian_read,
        "level3_table": [vars(e) for e in table],
        "block_study_cells": dict(block_study),
        "block_share_cells": dict(block_shares),
        "block_study_cells_us": dict(block_study_us),
        "block_share_cells_us": dict(block_shares_us),
        "eligible_cells": int(len(cell_id)),
        "access_bands": list(access_bands),
        "access_nan_cells": {b: int(np.isnan(arrays["access"][:, k]).sum())
                             for k, b in enumerate(access_bands)},
        "code_counts": {str(k): int(v) for k, v in sum(
            (Counter({int(a): int(b) for a, b in zip(*np.unique(c, return_counts=True),
                                                       strict=True)}) for c in codes.values()),
            Counter()).items()},
        "seconds": round(time.monotonic() - t0, 1),
        "peak_rss_mb": round(peak_rss_mb(), 1),
        "written_utc": now(),
    }  # fmt: skip
    write_json(work / "table_meta.json", meta)
    log(f"table done: {len(cell_id)} eligible cells, {meta['seconds']} s")


# --- training data --------------------------------------------------------------------------------


def check_t6() -> dict:
    want = {}
    for line in T6_SHA.read_text().splitlines():
        digest, name = line.split()
        want[name] = digest
    for name, digest in want.items():
        path = T6.parent.parent / name
        if sha256_file(path) != digest:
            raise SystemExit(f"{path} is not the stored T6 surface")
    return want


def load_presences(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def tile_code_of(cell_ids: np.ndarray, codes) -> np.ndarray:
    out = np.zeros(len(cell_ids), dtype=np.uint8)
    for k, c in enumerate(cell_ids):
        cell = cell_from_id(int(c))
        i, j = cell.col // TILE_N, cell.row // TILE_N
        key = f"{TILE_N}_{i}_{j}"
        if key not in codes:
            out[k] = 0
            continue
        r = (j + 1) * TILE_N - 1 - cell.row
        q = cell.col - i * TILE_N
        out[k] = codes[key][r, q]
    return out


class Data:
    """The training table: presences and background with their features, weights and groups."""

    def __init__(self, work: Path, presence_file: Path, track: str = "all", log=print,
                 access_band: str | None = None) -> None:  # fmt: skip
        tab = np.load(work / "table.npz")
        self.meta = json.loads((work / "table_meta.json").read_text(encoding="utf-8"))
        codes = dict(np.load(work / "codes.npz"))
        cell_id, feats, wkey, level3 = tab["cell_id"], tab["features"], tab["wkey"], tab["level3"]
        weather = [Cell(int(a), int(b)) for a, b in zip(*_unpack(np.unique(wkey)), strict=True)]
        frame_all = _log_effort(EffortSurface.read(T6 / "all"), weather)
        log_eff = frame_all if track == "all" else _log_effort(EffortSurface.read(T6 / track),
                                                               weather)  # fmt: skip
        self.track = track
        self.log_effort_values = np.array(list(log_eff.values()))
        self.held_effort = md.held_effort(self.log_effort_values)
        self.effort_cells_with_eligible = len(log_eff)

        # presences
        rows = load_presences(presence_file)
        p_cell = np.array([int(r["cell_id"]) for r in rows], dtype=np.int64)
        p_wkey = pack([int(r["lat_tenths"]) for r in rows], [int(r["lon_tenths"]) for r in rows])
        p_code = tile_code_of(p_cell, codes)
        pos = np.searchsorted(cell_id, p_cell)
        pos = np.clip(pos, 0, len(cell_id) - 1)
        eligible = cell_id[pos] == p_cell
        if not np.array_equal(eligible, p_code == CODE_IN):
            raise SystemExit("presence eligibility disagrees between the table and the codes")
        # effort is keyed by the 250 m cell centre's weather cell, as for background; a record's
        # own coordinates can sit in the neighbouring weather cell (counted below)
        cell_wkey = wkey[pos]
        has_eff = eligible & np.array([int(k) in log_eff for k in cell_wkey])
        self.presence_outcomes = {
            "thinned presences in the file": len(rows),
            "by cell code": {str(k): int(v) for k, v in Counter(p_code.tolist()).items()},
            "eligible but weather cell outside the effort frame": int((eligible & ~has_eff).sum()),
            "entering the fit": int((eligible & has_eff).sum()),
            "eligible, record's weather cell differs from its 250 m cell centre's": int(
                (eligible & (p_wkey != cell_wkey)).sum()
            ),
        }
        keep = eligible & has_eff
        self.presences = [r for r, k in zip(rows, keep, strict=True) if k]
        from forager_forecast.t7.presences import Presence  # noqa: PLC0415

        objs = [Presence(int(r["gbif_id"]), r["genus"], int(r["cell_id"]), int(r["lat_tenths"]),
                         int(r["lon_tenths"]), int(r["year"]), float(r["uncertainty_m"]),
                         r["license"]) for r in self.presences]  # fmt: skip
        self.genus_weights = genus_weights(objs, 30)
        pw = self.genus_weights.weights
        pi = pos[keep]

        # background (D133): eligible cells in T6's (all-licence) effort frame, drawn once; the
        # same draw for every run and track (P3 point 5); a track whose surface has no value for a
        # drawn cell drops it, counted
        in_frame = np.isin(wkey, np.fromiter(frame_all.keys(), dtype=np.int64))
        self.background_pool = int(in_frame.sum())
        bcells = bg.draw_background(cell_id[in_frame])
        self.background_sha256 = bg.cell_list_sha256(bcells)
        bi = np.searchsorted(cell_id, bcells)
        b_has = np.array([int(k) in log_eff for k in wkey[bi]])
        self.background_dropped_no_track_effort = int((~b_has).sum())
        bi = bi[b_has]
        # the access band (dispatch 2026-10-17-T7R): read for every row from the table's access
        # columns; its held value and quartiles are over the background draw as drawn (before the
        # trial run's thinning), so a trial holds the value the full run would
        self.access_band = access_band
        acc = None
        if access_band is not None:
            bands = self.meta.get("access_bands", [])
            if access_band not in bands:
                raise SystemExit(f"the table has no access band {access_band!r} (it has {bands})")
            acc = tab["access"][:, bands.index(access_band)].astype(np.float64)
            on_background = acc[bi]
            finite = np.isfinite(on_background)
            self.access_background_nan = int((~finite).sum())
            self.held_access = md.held_access(on_background) if finite.all() else None
            self.access_quartiles = [float(q) for q in
                                     np.quantile(on_background[finite], [0.25, 0.75])]  # fmt: skip
        if SMOKE:
            bi = bi[::10]
        bw = bg.background_weights(len(bi), float(pw.sum()))

        idx = np.concatenate([pi, bi])
        self.y = np.concatenate([np.ones(len(pi)), np.zeros(len(bi))])
        self.w = np.concatenate([pw, bw])
        self.blocks = level3[idx].astype(np.int64)
        self.clusters = wkey[idx]
        self.year = np.concatenate([np.array([int(r["year"]) for r in self.presences]),
                                    np.zeros(len(bi), dtype=np.int64)])  # fmt: skip
        f = feats[idx].astype(np.float64)
        le = np.array([log_eff[int(k)] for k in wkey[idx]])
        names = list(FEATURES)
        conifer, broadleaf = md.cover_columns(f[:, names.index("share_conifer")],
                                              f[:, names.index("share_broadleaf")],
                                              f[:, names.index("total_cover_pct")])  # fmt: skip
        self.columns = [*names, md.EFFORT, md.CONIFER_COVER, md.BROADLEAF_COVER]
        self.x = np.column_stack([f, le, conifer, broadleaf])
        if acc is not None:
            a = acc[idx]
            self.access_nan_rows = int(np.isnan(a).sum())
            if access_band in ACCESS_MAIN_BANDS and self.access_nan_rows:
                raise SystemExit(f"{self.access_nan_rows} rows have no {access_band}")
            self.columns.append(md.ACCESS)
            self.x = np.column_stack([self.x, a])
        self.n_presences, self.n_background = len(pi), len(bi)
        log(f"data: {len(pi)} presences, {len(bi)} background, pool {self.background_pool}")

    def cols(self, features: list[str]) -> np.ndarray:
        return self.x[:, [self.columns.index(c) for c in features]]


def _log_effort(surface: EffortSurface, weather: list) -> dict[int, float]:
    eff = static_effort(surface, weather)
    return {int(pack(c.lat_tenths, c.lon_tenths)): eff.log(c) for c in eff.total}


def _unpack(keys):
    from forager_forecast.t7.keying import unpack  # noqa: PLC0415

    return unpack(keys)


def configs() -> list[dict]:
    if sha256_file(GRID_FILE) != GRID_SHA256:
        raise SystemExit("the committed tuning grid is not the recorded one")
    out = fd.tuning_configurations()
    committed = json.loads(GRID_FILE.read_text(encoding="utf-8"))["configurations"]
    if out != committed:
        raise SystemExit("tuning_configurations() differs from the committed grid")
    return out[:2] if SMOKE else out


# --- timing ---------------------------------------------------------------------------------------


def cmd_timing(work: Path, evidence: Path, threads: int) -> None:
    evidence.mkdir(parents=True, exist_ok=True)
    log = Log(work / "timing.log")
    if ACCESS_MONOTONE is None:
        raise SystemExit("timing needs --access-monotone (-1, 0 or 1): the direction is a ruling")
    data = Data(work, V9 / "presences_main.csv", log=log, access_band=MAIN_ACCESS)
    features = [*BASE_BANDS, md.EFFORT, md.ACCESS]
    x = data.cols(features)
    folds = fd.leave_one_block_out_folds(data.blocks)
    for f in folds:
        fd.assert_no_leakage(f, data.blocks)
    sizes = sorted(((len(f.test), f.block) for f in folds), reverse=True)
    fold = next(f for f in folds if f.block == sizes[len(sizes) // 2][1])  # a median-size block
    fit = md.fitter_for(features, threads, ACCESS_MONOTONE)
    t = time.monotonic()
    per_config = {}

    def timed_fitter(config, *args):
        s = time.monotonic()
        out = fit(config, *args)
        per_config.setdefault(config["id"], []).append(round(time.monotonic() - s, 2))
        return out

    tr, te = fold.train, fold.test
    best, scores = fd.inner_choice(configs(), x[tr], data.y[tr], data.w[tr], data.blocks[tr],
                                   timed_fitter)  # fmt: skip
    s = time.monotonic()
    fit(best, x[tr], data.y[tr], data.w[tr], x[te])
    final = round(time.monotonic() - s, 1)
    fold_seconds = round(time.monotonic() - t, 1)
    n_folds = len(folds)
    tuned_models = 4  # A, B, base, full (full may equal base; counted to be safe)
    side_runs = len(REFIT_SIDE_RUNS)
    # add-ones, side runs (full, A, B each), final models
    untuned_fits = 8 * n_folds + side_runs * 3 * n_folds + 3 * 81
    mean_fit = float(np.mean([v for vs in per_config.values() for v in vs]))
    projection = tuned_models * n_folds * fold_seconds + untuned_fits * mean_fit
    out = {
        "access_band": MAIN_ACCESS, "access_monotone": ACCESS_MONOTONE, "side_runs": side_runs,
        "fold_block": fold.block, "train_points": int(len(tr)), "test_points": int(len(te)),
        "features": features, "threads": threads, "inner_fits": sum(len(v) for v in
                                                                    per_config.values()),
        "seconds_per_config": per_config, "chosen": best["id"], "final_fit_seconds": final,
        "outer_fold_seconds": fold_seconds, "outer_folds": n_folds,
        "fold_sizes": [[b, n] for n, b in sizes], "mean_fit_seconds": round(mean_fit, 2),
        "projection_hours_fits": round(projection / 3600, 2),
        "projection_note": "4 tuned models x folds x this fold's time, plus untuned fits x the "
                           "mean fit time; excludes the bootstrap, the area of applicability and "
                           "the map pass, timed separately",
        "presences": data.n_presences, "background": data.n_background,
        "presence_outcomes": data.presence_outcomes, "peak_rss_mb": round(peak_rss_mb(), 1),
        "written_utc": now(),
    }  # fmt: skip
    # the other heavy steps, timed once each (not a result: gains are uniform here)
    s = time.monotonic()
    mt.clustered_auc_difference(data.x[:, 0], data.x[:, 1], data.y, data.w, data.clusters)
    out["bootstrap_one_difference_seconds"] = round(time.monotonic() - s, 1)
    habitat = list(BASE_BANDS)
    s = time.monotonic()
    aoa = fit_aoa(data.cols(habitat), np.ones(len(habitat)), data.blocks)
    out["aoa_fit_seconds"] = round(time.monotonic() - s, 1)
    tab = np.load(work / "table.npz")
    sample = tab["features"][:: max(1, len(tab["features"]) // 100_000)].astype(np.float64)
    sample = sample[:, [list(FEATURES).index(c) for c in habitat]]
    s = time.monotonic()
    aoa.inside(sample)
    per = (time.monotonic() - s) / len(sample)
    out["aoa_query_seconds_per_cell"] = per
    out["aoa_query_projection_hours_all_eligible"] = round(per * len(tab["cell_id"]) / 3600, 2)
    out["eligible_cells"] = int(len(tab["cell_id"]))
    write_json(evidence / "timing.json", out)
    log(f"timing: one outer fold {fold_seconds} s; projection {out['projection_hours_fits']} h")


# --- fit ------------------------------------------------------------------------------------------


CACHE: Path | None = None  # set by cmd_fit: held-out predictions saved per model, reused on rerun
SMOKE = False  # --smoke: 2 configurations, a tenth of the background, 50 resamples, own folders
# --access-monotone: the access band's monotone direction (-1, 0 or 1), an open ruling; required by
# ``fit`` and ``timing``, which refuse to run without it rather than default it
ACCESS_MONOTONE: int | None = None
MAIN_ACCESS = ACCESS_MAIN_BANDS[0]  # dist_road_m (D150 ruling 1)
TRAILS_CHECK_ACCESS = "dist_any_m"  # the trails side check (-1168), in place of the road band
REFIT_SIDE_RUNS = (
    # (name, presences, effort track, access band); configurations reused (P7 point 9)
    ("M2 side run", V9 / "presences_side.csv", "all", MAIN_ACCESS),
    ("licence track", V9 / "presences_licence_track.csv", "cc", MAIN_ACCESS),
    ("comparison group", V9 / "presences_comparison.csv", "all", MAIN_ACCESS),
    ("saprotroph main", V9C / "presences_saprotroph_main.csv", "all", MAIN_ACCESS),
    ("saprotroph side", V9C / "presences_saprotroph_side.csv", "all", MAIN_ACCESS),
    ("trails side check", V9 / "presences_main.csv", "all", TRAILS_CHECK_ACCESS),
)
SAPROTROPH_MAIN = "saprotroph main"  # condition 3's group (D146, D155)


def lobo(data: Data, features: list[str], threads: int, log, chosen=None, key=None):
    """Held-out predictions over every block, cached under ``key`` in CACHE."""
    if CACHE is not None and key is not None:
        pp, cp = CACHE / f"lobo_{key}.npy", CACHE / f"lobo_{key}.json"
        if pp.exists() and cp.exists():
            meta = json.loads(cp.read_text())
            if (meta["features"] == features and meta["n"] == len(data.y)
                    and meta.get("access_monotone") == ACCESS_MONOTONE
                    and meta.get("access_band") == getattr(data, "access_band", None)):  # fmt: skip
                log(f"{key}: reused from cache")
                return np.load(pp), {int(k): v for k, v in meta["chosen"].items()}
        preds, ch = _lobo(data, features, threads, log, chosen)
        np.save(pp, preds)
        cp.write_text(json.dumps({"features": features, "n": len(data.y), "chosen": ch,
                                  "access_monotone": ACCESS_MONOTONE,
                                  "access_band": getattr(data, "access_band", None)}))  # fmt: skip
        return preds, ch
    return _lobo(data, features, threads, log, chosen)


def _lobo(data: Data, features: list[str], threads: int, log, chosen=None):
    """Held-out predictions over every block. ``chosen``: block -> config to reuse (no tuning)."""
    x = data.cols(features)
    fit = md.fitter_for(features, threads, ACCESS_MONOTONE)
    cfgs = {c["id"]: c for c in configs()}
    if chosen is None:
        preds, results = fd.leave_one_block_out(list(cfgs.values()), x, data.y, data.w,
                                                data.blocks, fit, log=log)  # fmt: skip
        return preds, {r.block: r.chosen for r in results}
    folds = fd.leave_one_block_out_folds(data.blocks)
    for f in folds:
        fd.assert_no_leakage(f, data.blocks)
    preds = np.full(len(data.y), np.nan)
    for f in folds:
        preds[f.test] = fit(cfgs[chosen[f.block]], x[f.train], data.y[f.train], data.w[f.train],
                            x[f.test])  # fmt: skip
    if np.isnan(preds).any():
        raise RuntimeError("a point has no held-out prediction")
    return preds, dict(chosen)


def diff(data: Data, a, b, select=None, clusters=None) -> mt.Difference:
    s = np.ones(len(data.y), bool) if select is None else select
    c = data.clusters if clusters is None else clusters
    return mt.clustered_auc_difference(a[s], b[s], data.y[s], data.w[s], c[s],
                                       resamples=50 if SMOKE else mt.RESAMPLES)  # fmt: skip


def dd(d: mt.Difference) -> dict:
    return {"point": d.point, "low": d.low, "high": d.high, "resamples": d.resamples,
            "interval_wholly_above_zero": d.excludes_zero_above}  # fmt: skip


# --- figures reported beside every fit (T7 part A, Forager RECORD -1156, -1157) -------------------

A_KEY, B_KEY = "A: effort only", "B: forest only"


def within_cell_figures(y, w, clusters, preds: dict, resamples: int) -> dict:
    """The weighted AUC of each model over (presence, background) pairs inside one weather cell,
    where effort is one value and only habitat can rank, with intervals over weather-cell
    resamples; and full minus A and full minus B on those pairs (P10b condition 2 is full minus
    A). Review 2's figure, with intervals (Forager RECORD -1156 item 1)."""
    names = {"A": A_KEY, "B": B_KEY, "base": "base", "full": "full"}
    out: dict = {"clusters": "weather cell", "auc": {}}
    for short, key in names.items():
        if key not in preds:
            continue
        m = mt.within_cluster_auc(preds[key], y, w, clusters, resamples)
        out["auc"][short] = {"point": m.point, "low": m.low, "high": m.high,
                             "resamples": m.resamples}  # fmt: skip
        out["pair_mass_share"] = m.pair_mass_share
    for short in ("A", "B"):
        out[f"full_minus_{short}"] = dd(
            mt.within_cluster_auc_difference(
                preds["full"], preds[names[short]], y, w, clusters, resamples
            )  # fmt: skip
        )
    return out


def within_cell_block_clustered_figures(y, w, clusters, blocks, preds: dict,
                                        resamples: int) -> dict:  # fmt: skip
    """P10b condition 2 as amended (Forager RECORD -1164, -1167): full minus A (and full minus B)
    over pairs inside one weather cell, every such pair kept, with the interval from condition 1's
    resampling by level III block (rows weighted by their block's draw count)."""
    out: dict = {
        "pairs": "inside one weather cell",
        "resampled": "level III block, rows weighted by their block's draw count",
    }
    for short, key in (("A", A_KEY), ("B", B_KEY)):
        out[f"full_minus_{short}"] = dd(
            mt.within_cluster_auc_difference_rows_resampled(
                preds["full"], preds[key], y, w, clusters, blocks, resamples
            )  # fmt: skip
        )
    return out


def block_clustered_figures(y, w, blocks, preds: dict, forested_sel, resamples: int) -> dict:
    """Full minus A and full minus B with intervals clustered by level III block, over all blocks
    and over the forested blocks, printed beside the weather-cell ones (P7 point 6)."""
    f = forested_sel
    return {
        "all": {s: dd(mt.clustered_auc_difference(preds["full"], preds[k], y, w, blocks,
                                                  resamples))
                for s, k in (("A", A_KEY), ("B", B_KEY))},
        "forested": {s: dd(mt.clustered_auc_difference(preds["full"][f], preds[k][f], y[f], w[f],
                                                       blocks[f], resamples))
                     for s, k in (("A", A_KEY), ("B", B_KEY))},
    }  # fmt: skip


def base_minus_b_figures(y, w, clusters, blocks, preds: dict, resamples: int) -> dict:
    """Base minus B, the habitat model with no band selection against forest cover alone, with
    its weather-cell and its block-clustered interval (both reviews: the lead over B rests on the
    bands selected on the same held-out blocks)."""
    base, b = preds["base"], preds[B_KEY]
    return {
        "weather_cell": dd(mt.clustered_auc_difference(base, b, y, w, clusters, resamples)),
        "block_clustered": dd(mt.clustered_auc_difference(base, b, y, w, blocks, resamples)),
    }


def cached_predictions(cache: Path, key: str, n: int) -> np.ndarray:
    """A model's held-out predictions as ``lobo`` saved them. Never fits: a missing entry, or one
    for a different row count, stops the run."""
    pp, cp = cache / f"lobo_{key}.npy", cache / f"lobo_{key}.json"
    if not (pp.exists() and cp.exists()):
        raise SystemExit(f"{key}: not in the cache {cache}; this command never fits")
    saved = json.loads(cp.read_text())["n"]
    p = np.load(pp)
    if saved != n or len(p) != n:
        raise SystemExit(f"{key}: the cache holds {saved} rows ({len(p)} saved), the table {n}")
    return p


def forested_selection(data: Data):
    """D139's forested blocks in the box, the blocks in the fit, the forested ones among them, and
    the rows in those."""
    study = {int(k): v for k, v in data.meta["block_study_cells"].items()}
    shares = {int(k): v for k, v in data.meta["block_share_cells"].items()}
    forested_all = fd.forested_blocks(study, shares)
    in_fit = set(np.unique(data.blocks).tolist())
    forested = forested_all & in_fit
    return forested_all, in_fit, forested, np.isin(data.blocks, sorted(forested))


def _iv(d: dict) -> str:
    return f"{d['point']:+.5f} [{d['low']:+.5f}, {d['high']:+.5f}]"


def log_reported_beside(log, by_block_cluster: dict, within_cell: dict, base_minus_b: dict) -> None:
    for scope in ("all", "forested"):
        for k in ("A", "B"):
            iv = _iv(by_block_cluster[scope][k])
            log(f"full minus {k}, {scope} blocks, block-clustered: {iv}")
    log(f"base minus B: weather cell {_iv(base_minus_b['weather_cell'])}, "
        f"block-clustered {_iv(base_minus_b['block_clustered'])}")  # fmt: skip
    aucs = ", ".join(f"{k} {v['point']:.4f} [{v['low']:.4f}, {v['high']:.4f}]"
                     for k, v in within_cell["auc"].items())  # fmt: skip
    log(f"within one weather cell (pair weight share {within_cell['pair_mass_share']:.5%}): "
        f"{aucs}; full minus A {_iv(within_cell['full_minus_A'])}, "
        f"full minus B {_iv(within_cell['full_minus_B'])}")  # fmt: skip


def auc(data: Data, p, select=None) -> float | None:
    s = np.ones(len(data.y), bool) if select is None else select
    try:
        return mt.weighted_auc(p[s], data.y[s], data.w[s])
    except ValueError:
        return None


def checkpoint(work: Path, name: str, value) -> None:
    np.save(work / f"pred_{name}.npy", value)


def as_difference(d: dict) -> mt.Difference:
    return mt.Difference(d["point"], d["low"], d["high"], d["resamples"])


def cmd_fit(work: Path, evidence: Path, threads: int, out_dir: Path) -> None:
    """The re-fit (dispatch 2026-10-17-T7R): the ladder with the access band beside effort in
    every model, the side runs (the trails side check and the saprotroph group's two runs among
    them), condition 3's contrast and P10b with P10 beside it, the area of applicability on the
    habitat bands only, and the map with effort and access held. Needs a table built with
    ``--access`` and a ruled ``--access-monotone``."""
    global CACHE
    if ACCESS_MONOTONE is None:
        raise SystemExit("fit needs --access-monotone (-1, 0 or 1): the direction is a ruling")
    out_dir = check_out_dir(out_dir)
    CACHE = work / ("cache_smoke" if SMOKE else "cache")
    CACHE.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    log = Log(work / "fit.log")
    t0 = time.monotonic()
    t6_hashes = check_t6()
    data = Data(work, V9 / "presences_main.csv", log=log, access_band=MAIN_ACCESS)
    meta = data.meta
    level3 = {e["code"]: e for e in meta["level3_table"]}
    log(f"access: {MAIN_ACCESS}, monotone {ACCESS_MONOTONE}, held {data.held_access:.1f} m, "
        f"quartiles {data.access_quartiles}")  # fmt: skip
    study = {int(k): v for k, v in meta["block_study_cells"].items()}
    shares = {int(k): v for k, v in meta["block_share_cells"].items()}
    forested_all, in_fit, forested, forested_sel = forested_selection(data)
    resamples = 50 if SMOKE else mt.RESAMPLES
    log(f"forested blocks: {len(forested_all)} in the box, {len(forested)} in the fit")

    ladder = md.ladder_with_access(list(BASE_BANDS) + [md.EFFORT], list(CANDIDATE_BANDS))
    preds: dict[str, np.ndarray] = {}
    chosen: dict[str, dict] = {}
    for name in ("A: effort only", "B: forest only", "base"):
        s = time.monotonic()
        preds[name], chosen[name] = lobo(data, ladder[name], threads, log, key=name[0:4])
        checkpoint(work, name.split(":")[0].replace(" ", "_"), preds[name])
        within = mt.within_cluster_auc(preds[name], data.y, data.w, data.clusters, resamples)
        log(
            f"{name}: {round(time.monotonic() - s)} s, pooled AUC {auc(data, preds[name]):.4f}, "
            f"within-weather-cell AUC {within.point:.4f} [{within.low:.4f}, {within.high:.4f}]"
        )
    add_one = {}
    for c in CANDIDATE_BANDS:
        key = f"base + {c}"
        preds[key], _ = lobo(data, ladder[key], threads, log, chosen=chosen["base"], key=c)
        add_one[c] = diff(data, preds[key], preds["base"])
        log(f"{key}: difference {add_one[c].point:+.4f} [{add_one[c].low:+.4f}, "
            f"{add_one[c].high:+.4f}]")  # fmt: skip
    kept = [c for c in CANDIDATE_BANDS if add_one[c].excludes_zero_above]
    full_features = [*BASE_BANDS, *kept, md.EFFORT, md.ACCESS]
    if kept:
        s = time.monotonic()
        preds["full"], chosen["full"] = lobo(data, full_features, threads, log, key="full")
        log(f"full (base + {kept}): {round(time.monotonic() - s)} s")
    else:
        preds["full"], chosen["full"] = preds["base"], chosen["base"]
    checkpoint(work, "full", preds["full"])

    full, a, b = preds["full"], preds["A: effort only"], preds["B: forest only"]
    pooled = {"A": diff(data, full, a), "B": diff(data, full, b)}
    forest = {"A": diff(data, full, a, forested_sel), "B": diff(data, full, b, forested_sel)}
    verdict = mt.p10_passes(pooled, forest)
    by_block_cluster = block_clustered_figures(data.y, data.w, data.blocks, preds, forested_sel,
                                               resamples)  # fmt: skip
    within_cell = within_cell_figures(data.y, data.w, data.clusters, preds, resamples)
    within_cell_by_block = within_cell_block_clustered_figures(
        data.y, data.w, data.clusters, data.blocks, preds, resamples
    )
    base_minus_b = base_minus_b_figures(data.y, data.w, data.clusters, data.blocks, preds,
                                        resamples)  # fmt: skip
    log(f"P10 (D140, reported beside, no verdict): {'pass' if verdict else 'fail'}")
    log_reported_beside(log, by_block_cluster, within_cell, base_minus_b)

    # per block and level I
    informative = fd.informative_blocks(data.blocks, data.y)
    blocks_report = []
    for blk in sorted(in_fit):
        sel = data.blocks == blk
        e = level3[int(blk)]
        blocks_report.append({
            "code": int(blk), "level3": e["level3"], "name": e["name"], "level1": e["level1"],
            "presences": int((data.y[sel] == 1).sum()), "background": int((data.y[sel] == 0).sum()),
            "informative": int(blk) in informative, "forested": int(blk) in forested,
            "forested_share": round(shares.get(int(blk), 0) / study[int(blk)], 4),
            "chosen": {k: v.get(int(blk)) for k, v in chosen.items()},
            "auc": {k: (auc(data, preds[k], sel) if int(blk) in informative else None)
                    for k in ("full", "A: effort only", "B: forest only")},
        })  # fmt: skip
    level1 = {}
    for l1 in sorted({level3[int(b)]["level1"] for b in in_fit}):
        sel = np.isin(data.blocks, [b for b in in_fit if level3[int(b)]["level1"] == l1])
        level1[l1] = {k: auc(data, preds[k], sel) for k in ("full", "A: effort only",
                                                             "B: forest only")}  # fmt: skip
        level1[l1]["presences"] = int((data.y[sel] == 1).sum())
    by_year = {}
    bgsel = data.y == 0
    for yr in sorted(set(data.year[data.y == 1].tolist())):
        sel = bgsel | ((data.y == 1) & (data.year == yr))
        by_year[int(yr)] = {k: auc(data, preds[k], sel) for k in ("full", "A: effort only",
                                                                   "B: forest only")}  # fmt: skip
        by_year[int(yr)]["presences"] = int(((data.y == 1) & (data.year == yr)).sum())

    # final models on all blocks: the configuration chosen by inner grouped 4-fold on all blocks
    cfgs = configs()
    s = time.monotonic()
    xf = data.cols(full_features)
    best_full, _ = fd.inner_choice(cfgs, xf, data.y, data.w, data.blocks,
                                   md.fitter_for(full_features, threads,
                                                 ACCESS_MONOTONE))  # fmt: skip
    booster = md.train(best_full, full_features, xf, data.y, data.w, threads, ACCESS_MONOTONE)
    log(f"final full model: {best_full['id']}, {round(time.monotonic() - s)} s")
    gains = booster.feature_importance("gain")
    s = time.monotonic()
    aoa, habitat = area_of_applicability(data, full_features, gains)
    log(f"area of applicability: threshold {aoa.threshold:.4f}, {round(time.monotonic() - s)} s")

    # side runs, reusing each fold's chosen configurations (P7 point 9)
    side = {}
    sap = None
    for name, path, track, band in REFIT_SIDE_RUNS:
        s = time.monotonic()
        sd = Data(work, path, track=track, log=log, access_band=band)
        sp = {}
        for k, feats in (
            ("full", full_features),
            ("A: effort only", ladder["A: effort only"]),
            ("B: forest only", ladder["B: forest only"]),
        ):
            ch = chosen[k]
            missing = set(np.unique(sd.blocks).tolist()) - set(ch)
            if missing:
                raise SystemExit(f"{name}: blocks {missing} have no chosen configuration")
            sp[k], _ = lobo(sd, feats, threads, log, chosen=ch, key=f"{name}-{k[:4]}")
        sf = np.isin(sd.blocks, sorted(forested))
        side[name] = {
            "presences": sd.n_presences, "background": sd.n_background,
            "presence_outcomes": sd.presence_outcomes,
            "held_effort": sd.held_effort,
            "auc": {k: auc(sd, v) for k, v in sp.items()},
            "full_minus_A": dd(diff(sd, sp["full"], sp["A: effort only"])),
            "full_minus_B": dd(diff(sd, sp["full"], sp["B: forest only"])),
            "forested_full_minus_A": dd(diff(sd, sp["full"], sp["A: effort only"], sf)),
            "forested_full_minus_B": dd(diff(sd, sp["full"], sp["B: forest only"], sf)),
            "block_clustered": block_clustered_figures(sd.y, sd.w, sd.blocks, sp, sf, resamples),
            "within_weather_cell": within_cell_figures(sd.y, sd.w, sd.clusters, sp, resamples),
            "within_weather_cell_block_clustered": within_cell_block_clustered_figures(
                sd.y, sd.w, sd.clusters, sd.blocks, sp, resamples),
            "access_band": band, "access_nan_rows": sd.access_nan_rows,
            "seconds": round(time.monotonic() - s),
        }  # fmt: skip
        if name == "comparison group":
            comp_booster = md.train(best_full, full_features, sd.cols(full_features), sd.y,
                                    sd.w, threads, ACCESS_MONOTONE)  # fmt: skip
        if name == SAPROTROPH_MAIN:
            sap = mt.GroupScores(sp["full"], sp["A: effort only"], sd.y, sd.w, sd.blocks)
            side[name]["genus_units"] = {
                "alone": sum(1 for u in sd.genus_weights.presences_per_unit if u != POOLED),
                "pooled_presences": sd.genus_weights.presences_per_unit.get(POOLED, 0)}  # fmt: skip
        log(f"{name}: {side[name]['auc']}")
        del sd

    # P10b condition 3: the host-specific contrast, one block resampling for both groups
    myc = mt.GroupScores(preds["full"], preds["A: effort only"], data.y, data.w, data.blocks)
    shared = shared_forested_blocks(forested, data.blocks, data.y, sap.blocks, sap.y)
    contrast = mt.host_specific_contrast(myc, sap, resamples)

    def _subset(g, keep):
        k = np.isin(g.blocks, keep)
        return mt.GroupScores(g.full[k], g.a[k], g.y[k], g.w[k], g.blocks[k])

    contrast_shared = mt.host_specific_contrast(_subset(myc, shared), _subset(sap, shared),
                                                resamples)  # fmt: skip

    def _gain(g):
        return auc(SimpleNamespace(y=g.y, w=g.w), g.full) - auc(SimpleNamespace(y=g.y, w=g.w), g.a)

    condition_3 = {
        "gain_mycorrhizal_full_minus_A": _gain(myc), "gain_saprotroph_full_minus_A": _gain(sap),
        "contrast_all_blocks": dd(contrast),
        "resampled": "level III blocks, one draw per resample applied to both groups",
        "shared_forested_blocks": shared,
        "contrast_shared_forested_blocks_no_verdict": dd(contrast_shared),
    }  # fmt: skip
    p10b = p10b_figures(as_difference(by_block_cluster["all"]["B"]),
                        as_difference(within_cell_by_block["full_minus_A"]), contrast,
                        CONDITION_4_PENDING, verdict)  # fmt: skip
    log(f"condition 3: contrast {_iv(dd(contrast))}; over {len(shared)} shared forested "
        f"blocks {_iv(dd(contrast_shared))}")  # fmt: skip
    log(f"P10b: {p10b['verdict']}")

    # the map pass
    from forager_forecast.t7.outputs import HabitatWriter, attribution  # noqa: PLC0415

    window = pnw_window()
    tab = np.load(work / "table.npz")
    codes = dict(np.load(work / "codes.npz"))
    cell_id, feats = tab["cell_id"], tab["features"]
    names = list(FEATURES)
    held = data.held_effort
    scores_all = np.empty(len(cell_id), dtype=np.float32)
    comp_all = np.empty(len(cell_id), dtype=np.float32)
    inside_all = np.empty(len(cell_id), dtype=bool)
    chunk = 500_000
    s = time.monotonic()
    held_access = data.held_access
    hold = {md.EFFORT: held, md.ACCESS: held_access}
    for i0 in range(0, len(cell_id), chunk):
        f = feats[i0 : i0 + chunk].astype(np.float64)
        xm = map_columns(f, names, full_features, held, held_access)
        scores_all[i0 : i0 + chunk] = md.predict_held(booster, full_features, xm, hold)
        comp_all[i0 : i0 + chunk] = md.predict_held(comp_booster, full_features, xm, hold)
        inside_all[i0 : i0 + chunk] = aoa.inside(f[:, [names.index(c) for c in habitat]])
        log(f"map pass {i0 + len(f)} of {len(cell_id)}, {round(time.monotonic() - s)} s")
    np.save(work / "scores_all.npy", scores_all)
    np.save(work / "inside_all.npy", inside_all)
    shaded = inside_all
    from scipy.stats import spearmanr  # noqa: PLC0415

    rho = float(spearmanr(scores_all[shaded], comp_all[shaded]).statistic)

    # ranking unchanged at two effort levels (P6), on a sample
    rng = np.random.default_rng(SEED)
    pick = rng.choice(len(cell_id), size=min(200_000, len(cell_id)), replace=False)
    f = feats[pick].astype(np.float64)
    xm = map_columns(f, names, full_features, held, held_access)
    # P6: the 25th and 75th percentiles of the distribution the held value is the median of; for
    # effort with access held, and for access (over the background draw) with effort held
    q25, q75 = np.quantile(data.log_effort_values, [0.25, 0.75])
    r25 = md.predict_held(booster, full_features, xm, {md.EFFORT: q25, md.ACCESS: held_access})
    r75 = md.predict_held(booster, full_features, xm, {md.EFFORT: q75, md.ACCESS: held_access})
    ranking_same = bool(np.array_equal(np.argsort(r25, kind="stable"),
                                       np.argsort(r75, kind="stable")))  # fmt: skip
    shift = r75 - r25
    a25, a75 = data.access_quartiles
    s25 = md.predict_held(booster, full_features, xm, {md.EFFORT: held, md.ACCESS: a25})
    s75 = md.predict_held(booster, full_features, xm, {md.EFFORT: held, md.ACCESS: a75})
    access_ranking_same = bool(np.array_equal(np.argsort(s25, kind="stable"),
                                              np.argsort(s75, kind="stable")))  # fmt: skip
    access_shift = s75 - s25
    log(f"P6: ranking same at effort quartiles {ranking_same}, at access quartiles "
        f"{access_ranking_same}")  # fmt: skip

    # writers
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True,
                            text=True, check=True).stdout.strip()  # fmt: skip
    attrib = attribution(
        set(meta["attribution_tree"]),
        set(meta["attribution_soil"]),
        meta["canadian_values_read"],
        [
            "Põlme, S. et al. 2020. FungalTraits. Fungal Diversity 105: 1-16. "
            "doi 10.1007/s13225-020-00466-2 (Table S1, with the corresponding "
            "author's consent)",
            "GBIF.org (6 October 2026) GBIF Occurrence Download https://doi.org/10.15468/dl.8jxmeb",
            "Commission for Environmental Cooperation (CEC). 2021. North American "
            "Environmental Atlas - Terrestrial Ecoregions: Level III. Ed. 2.0",
            access_attribution(),
        ],
    )
    writer = HabitatWriter(out_dir, window, {"label": "relative habitat, PNW pilot, not shown",
                                             "code_commit": commit,
                                             "attribution": " | ".join(attrib)})  # fmt: skip
    from forager_forecast.t6b_layers import Tile  # noqa: PLC0415

    code_counts = Counter()
    for key, code in codes.items():
        n, i, j = (int(v) for v in key.split("_"))
        tile = Tile(i, j, n)
        tw = tile.window
        code = code.copy()
        score = np.full(code.shape, np.nan, dtype=np.float32)
        lo = np.searchsorted(cell_id, _tile_id_range(tw)[0])
        hi = np.searchsorted(cell_id, _tile_id_range(tw)[1], side="right")
        ids = cell_id[lo:hi]
        rr, cc = _rows_cols(ids, tw)
        ok = (rr >= 0) & (rr < TILE_N) & (cc >= 0) & (cc < TILE_N)
        idx = np.arange(lo, hi)[ok]
        rr, cc = rr[ok], cc[ok]
        if not (code[rr, cc] == CODE_IN).all():
            raise SystemExit(f"tile {key}: table cells are not all code 1")
        ins = inside_all[idx]
        score[rr[ins], cc[ins]] = scores_all[idx][ins]
        code[rr[~ins], cc[~ins]] = CODE_OUT_OF_AOA
        # clip to the box window
        left, right = max(tw.left, window.left), min(tw.right, window.right)
        bottom, top = max(tw.bottom, window.bottom), min(tw.top, window.top)
        r0, c0 = (tw.top - top) // CELL_SIZE_M, (left - tw.left) // CELL_SIZE_M
        r1, c1 = (tw.top - bottom) // CELL_SIZE_M, (right - tw.left) // CELL_SIZE_M
        sub = GridWindow(left, bottom, right, top)
        writer.write(sub, score[r0:r1, c0:c1], code[r0:r1, c0:c1])
        u, n_ = np.unique(code[r0:r1, c0:c1], return_counts=True)
        for a_, b_ in zip(u.tolist(), n_.tolist(), strict=True):
            code_counts[int(a_)] += int(b_)
    digests = writer.close()
    log(f"rasters written: {digests}")

    # AOA counts by side (US only in the fit), block and frame
    wkey_all, l3_all = tab["wkey"], tab["level3"]
    frame_keys = np.array(sorted(_frame_keys(T6 / "all")), dtype=np.int64)
    in_frame_all = np.isin(wkey_all, frame_keys)
    aoa_counts = {
        "eligible": int(len(cell_id)), "inside": int(inside_all.sum()),
        "outside": int((~inside_all).sum()),
        "inside_in_frame": int((inside_all & in_frame_all).sum()),
        "inside_outside_frame": int((inside_all & ~in_frame_all).sum()),
        "outside_in_frame": int((~inside_all & in_frame_all).sum()),
        "outside_outside_frame": int((~inside_all & ~in_frame_all).sum()),
        "by_block": {f"{level3[int(b)]['level3']} {level3[int(b)]['name']}":
                     {"inside": int((inside_all & (l3_all == b)).sum()),
                      "outside": int((~inside_all & (l3_all == b)).sum())}
                     for b in np.unique(l3_all)},
    }  # fmt: skip

    # mask map image
    png = out_dir / "mask_map.png"
    png_sha = mask_map(out_dir, window, png)

    report = {
        "written_utc": now(), "code_commit": commit, "threads": threads,
        "presences": data.n_presences, "background": data.n_background,
        "background_pool": data.background_pool, "background_sha256": data.background_sha256,
        "presence_outcomes": data.presence_outcomes,
        "genus_units": {"alone": sum(1 for u in data.genus_weights.presences_per_unit
                                     if u != POOLED),
                        "pooled_presences": data.genus_weights.presences_per_unit.get(POOLED, 0)},
        "held_effort": held, "effort_quartiles": [float(q25), float(q75)],
        "ranking_same_at_quartiles": ranking_same,
        "score_shift_at_quartiles": [float(shift.min()), float(shift.max())],
        "access": {"band": MAIN_ACCESS, "monotone": ACCESS_MONOTONE, "held": held_access,
                   "held_rule": "median over the background draw",
                   "quartiles_over_background": data.access_quartiles,
                   "ranking_same_at_quartiles": access_ranking_same,
                   "score_shift_at_quartiles": [float(access_shift.min()),
                                                float(access_shift.max())],
                   "in_interaction_group_with": md.EFFORT,
                   "excluded_from_area_of_applicability": True},
        "model_features": {**ladder, "full": full_features},
        "smoke": SMOKE, "resamples": resamples,
        "blocks_in_fit": len(in_fit), "forested_blocks_in_box": len(forested_all),
        "forested_blocks_in_fit": sorted(int(b) for b in forested),
        "informative_blocks": sorted(int(b) for b in informative),
        "pooled_auc": {k: auc(data, v) for k, v in preds.items()},
        "forested_auc": {k: auc(data, v, forested_sel) for k, v in preds.items()},
        "add_one": {c: dd(d) for c, d in add_one.items()}, "kept_candidates": kept,
        "full_features": full_features,
        "p10b": p10b, "condition_3": condition_3,
        "p10_no_verdict": {"all_blocks": {k: dd(v) for k, v in pooled.items()},
                           "forested_blocks": {k: dd(v) for k, v in forest.items()},
                           "passes": verdict},
        "block_clustered_intervals_no_verdict": by_block_cluster,
        "base_minus_B_no_verdict": base_minus_b,
        "within_weather_cell_no_verdict": within_cell,
        "within_weather_cell_block_clustered_no_verdict": within_cell_by_block,
        "by_block": blocks_report, "level1": level1, "by_year": by_year,
        "side_runs": side, "comparison_rank_correlation_over_shaded": rho,
        "final_model_configuration": best_full,
        "aoa": {"threshold": aoa.threshold, "mean_distance": aoa.mean_distance,
                "mean_distance_exact": aoa.mean_distance_exact,
                "weights": dict(zip(habitat, aoa.weights.tolist(), strict=True)),
                "train_di_quantiles": np.quantile(aoa.train_di, [0, .25, .5, .75, 1]).tolist(),
                "counts": aoa_counts},
        "code_counts_in_box_window": dict(sorted(code_counts.items())),
        "outputs": {**digests, "mask_map.png": png_sha},
        "seconds": round(time.monotonic() - t0), "peak_rss_mb": round(peak_rss_mb(), 1),
    }  # fmt: skip
    write_json(evidence / "fit_report.json", report)
    write_block_csv(evidence / "block_report.csv", blocks_report)
    write_json(out_dir / "block_report.json", report)
    write_block_csv(out_dir / "block_report.csv", blocks_report)
    from forager_forecast.t7.outputs import write_manifest  # noqa: PLC0415

    manifest = {
        "inputs": {"t6b": meta["inputs"], "t6_surface": t6_hashes,
                   "d26_zip_sha256": json.loads((V9 / "counts.json").read_text())["zip_sha256"],
                   "presence_files": json.loads((V9 / "counts.json").read_text())[
                       "presence_files_outside_repo"]},
        "code_commit": commit, "seed": SEED,
        "membership": {"list_sha256": json.loads((V9 / "counts.json").read_text())[
            "membership_list_sha256"], "export_sha256": json.loads(
            (V9 / "counts.json").read_text())["export_sha256"]},
        "background": {"n": data.n_background, "sha256": data.background_sha256,
                       "pool": data.background_pool},
        "tuning_grid_sha256": GRID_SHA256, "chosen_configurations": chosen,
        "final_model_configuration": best_full,
        "share_floor": SHARE_FLOOR, "held_effort": held,
        "aoa": {"threshold": aoa.threshold, "mean_distance": aoa.mean_distance,
                "excluded": [md.EFFORT, md.ACCESS]},
        "access": {"input": meta["inputs"].get("access"), "band": MAIN_ACCESS,
                   "monotone": ACCESS_MONOTONE, "held": held_access},
        "licence_track": "reported beside (CC0 and CC BY records, T6's cc surface)",
        "attribution": attrib, "codes": CODE_LEGEND, "smoke": SMOKE,
        "level3_codes": meta["level3_table"], "features": full_features,
        "left_out_bands": list(LEFT_OUT_BANDS), "threads": threads,
        "outputs": {**digests, "mask_map.png": png_sha},
        "labels": ["relative habitat, PNW pilot, not shown"],
    }  # fmt: skip
    msha = write_manifest(out_dir / "manifest.json", manifest)
    log(f"manifest {msha}; done in {round(time.monotonic() - t0)} s")


def cmd_figures(work: Path, evidence: Path) -> None:
    """Recompute the figures reported beside every fit (base minus B, the within-weather-cell AUCs,
    the block-clustered intervals) from a finished fit's cached held-out predictions. Reads the
    work dir only; never fits; writes one JSON to the evidence dir."""
    cache = work / "cache"
    evidence.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True,
                            text=True, check=True).stdout.strip()  # fmt: skip
    r = mt.RESAMPLES
    data = Data(work, V9 / "presences_main.csv")
    _, _, forested, fsel = forested_selection(data)
    n = len(data.y)
    preds = {A_KEY: cached_predictions(cache, "A: e", n),
             B_KEY: cached_predictions(cache, "B: f", n),
             "base": cached_predictions(cache, "base", n),
             "full": cached_predictions(cache, "full", n)}  # fmt: skip
    out = {
        "written_utc": now(), "code_commit": commit, "cache": str(cache), "resamples": r,
        "seed": mt.SEED,
        "main": {
            "presences": data.n_presences, "background": data.n_background,
            "pooled_auc": {k: auc(data, v) for k, v in preds.items()},
            "base_minus_B": base_minus_b_figures(data.y, data.w, data.clusters, data.blocks, preds,
                                                 r),
            "within_weather_cell": within_cell_figures(data.y, data.w, data.clusters, preds, r),
            "within_weather_cell_block_clustered": within_cell_block_clustered_figures(
                data.y, data.w, data.clusters, data.blocks, preds, r),
            "block_clustered": block_clustered_figures(data.y, data.w, data.blocks, preds, fsel, r),
        },
        "side_runs": {},
    }  # fmt: skip
    del data
    for name, path, track in SIDE_RUNS:
        sd = Data(work, path, track=track)
        n = len(sd.y)
        sp = {k: cached_predictions(cache, f"{name}-{k[:4]}", n) for k in ("full", A_KEY, B_KEY)}
        sf = np.isin(sd.blocks, sorted(forested))
        out["side_runs"][name] = {
            "presences": sd.n_presences, "background": sd.n_background,
            "pooled_auc": {k: auc(sd, v) for k, v in sp.items()},
            "within_weather_cell": within_cell_figures(sd.y, sd.w, sd.clusters, sp, r),
            "within_weather_cell_block_clustered": within_cell_block_clustered_figures(
                sd.y, sd.w, sd.clusters, sd.blocks, sp, r),
            "block_clustered": block_clustered_figures(sd.y, sd.w, sd.blocks, sp, sf, r),
        }  # fmt: skip
        del sd
    out["seconds"] = round(time.monotonic() - t0)
    out["peak_rss_mb"] = round(peak_rss_mb(), 1)
    write_json(evidence / "figures_from_cache.json", out)


def _tile_id_range(tw: GridWindow):
    from forager_forecast.grid import GridCell  # noqa: PLC0415

    c0, c1 = tw.left // CELL_SIZE_M, tw.right // CELL_SIZE_M - 1
    r0, r1 = tw.bottom // CELL_SIZE_M, tw.top // CELL_SIZE_M - 1
    return GridCell(c0, r0).id, GridCell(c1, r1).id


def _rows_cols(ids: np.ndarray, tw: GridWindow):
    ids = ids.astype(np.int64)
    col = (ids & 0xFFFF) - (1 << 15)
    row = (ids >> 16) - (1 << 15)
    return tw.top // CELL_SIZE_M - 1 - row, col - tw.left // CELL_SIZE_M


def _frame_keys(folder: Path) -> set:
    keys = set()
    with (folder / "cell_level.csv").open(encoding="utf-8", newline="") as h:
        for row in csv.DictReader(h):
            keys.add(int(pack(int(row["lat_tenths"]), int(row["lon_tenths"]))))
    return keys


def write_block_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(
            (
                "code",
                "level3",
                "name",
                "level1",
                "presences",
                "background",
                "informative",
                "forested",
                "forested_share",
                "auc_full",
                "auc_A",
                "auc_B",
            )
        )
        for r in rows:
            w.writerow(
                (
                    r["code"],
                    r["level3"],
                    r["name"],
                    r["level1"],
                    r["presences"],
                    r["background"],
                    r["informative"],
                    r["forested"],
                    r["forested_share"],
                    r["auc"]["full"],
                    r["auc"]["A: effort only"],
                    r["auc"]["B: forest only"],
                )
            )


def mask_map(out_dir: Path, window: GridWindow, png: Path) -> str:
    """P9's picture: shaded cells in five equal-count classes, codes 2 to 6 in greys, the effort
    frame's outline and level III boundaries. Written, never shown (M8)."""
    import rasterio  # noqa: PLC0415

    from forager_forecast.pnw import png_bytes  # noqa: PLC0415
    from forager_forecast.t7.ecoregions import burn_level3  # noqa: PLC0415
    from forager_forecast.t7.keying import weather_cells_for_window  # noqa: PLC0415

    with rasterio.open(out_dir / "relative_habitat_pnw.tif") as ds:
        score = ds.read(1)
    with rasterio.open(out_dir / "applicability_pnw.tif") as ds:
        code = ds.read(1)
    step = 2  # 500 m pixels
    score, code = score[::step, ::step], code[::step, ::step]
    rgba = np.zeros(code.shape + (4,), dtype=np.uint8)
    rgba[...] = (255, 255, 255, 255)
    greys = {2: 200, 3: 225, 4: 235, 5: 215, 6: 245}
    for c, g in greys.items():
        rgba[code == c] = (g, g, g, 255)
    ok = np.isfinite(score)
    if ok.any():
        edges = np.quantile(score[ok], [0.2, 0.4, 0.6, 0.8])
        cls = np.digitize(score, edges)
        greens = [(237, 248, 233), (186, 228, 179), (116, 196, 118), (49, 163, 84), (0, 109, 44)]
        for k, colour in enumerate(greens):
            rgba[ok & (cls == k)] = (*colour, 255)
    lat_t, lon_t = weather_cells_for_window(window)
    frame = np.isin(pack(lat_t, lon_t), np.array(sorted(_frame_keys(T6 / "all"))))[::step, ::step]
    edge = np.zeros_like(frame)
    edge[1:, :] |= frame[1:, :] != frame[:-1, :]
    edge[:, 1:] |= frame[:, 1:] != frame[:, :-1]
    rgba[edge] = (90, 60, 140, 255)
    _, polygons = read_level3(LEVEL3)
    l3 = burn_level3(polygons, window)[::step, ::step]
    b = np.zeros_like(edge)
    b[1:, :] |= l3[1:, :] != l3[:-1, :]
    b[:, 1:] |= l3[:, 1:] != l3[:, :-1]
    rgba[b] = (40, 40, 40, 255)
    png.write_bytes(png_bytes(rgba))
    return sha256_file(png)


if __name__ == "__main__":
    args = sys.argv[1:]
    threads = 4
    if "--smoke" in args:
        args.remove("--smoke")
        SMOKE = True
    if "--threads" in args:
        k = args.index("--threads")
        threads = int(args[k + 1])
        del args[k : k + 2]
    if "--access-monotone" in args:
        k = args.index("--access-monotone")
        ACCESS_MONOTONE = int(args[k + 1])
        if ACCESS_MONOTONE not in (-1, 0, 1):
            raise SystemExit("--access-monotone is -1, 0 or 1")
        del args[k : k + 2]
    out = None
    if "--out" in args:
        k = args.index("--out")
        out = Path(args[k + 1])
        del args[k : k + 2]
    access_table = "--access" in args
    if access_table:
        args.remove("--access")
    if not args:
        raise SystemExit(__doc__)
    if args[0] == "table":
        cmd_table(Path(args[1]), ACCESS if access_table else None)
    elif args[0] == "timing":
        cmd_timing(Path(args[1]), Path(args[2]), threads)
    elif args[0] == "fit":
        if out is None:
            raise SystemExit("fit needs --out <new folder> for the map (never the judged run's)")
        cmd_fit(Path(args[1]), Path(args[2]), threads, out)
    elif args[0] == "figures":
        cmd_figures(Path(args[1]), Path(args[2]))
    else:
        raise SystemExit(__doc__)

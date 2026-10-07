"""T6b: one section of the continental run (D114). Start it only when no app build needs the laptop.

Usage (repository root):
    systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0 \
        .venv/bin/python scripts/t6b_run.py --until 07:00 [--stages mask,plots,trees,soil]
        [--workers 2]

- ``--until HH:MM`` is local time, the next occurrence of it. No new tile starts after it; tiles in
  hand finish. ``touch <drive>/forecast-data/t6b/PAUSE`` does the same at once (delete the file
  before the next section). Nothing restarts on its own.
- Stages run in the order given and each resumes from the manifest. ``mask`` and ``plots`` run once.
- At the end the manifest and this section's summary are copied to
  docs/audits/2026-10-07-t6b-run/, committed and pushed.
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from forager_forecast.grid import CELL_SIZE_M, GridWindow
from forager_forecast.t5_layer import scanfi_url
from forager_forecast.t6b_layers import (
    SCANFI_LAYERS,
    Tile,
    build_plot_table,
    require_free_space,
    scanfi_layer_tile,
    soil_tile,
    tiles_over,
    tree_tile,
)
from forager_forecast.t6b_mask import (
    COUNTRY_CAN,
    COUNTRY_US48,
    MASK_VERSION,
    SIDE_CA,
    build_mask,
    cells_in_study,
    political_rings,
    read_mask,
)
from forager_forecast.t6b_run import (
    append_line,
    done_units,
    next_stop,
    read_lines,
    run_section,
)

REPO = Path(__file__).resolve().parent.parent
DRIVE = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data")
T6B = DRIVE / "t6b"
SOURCES = T6B / "sources"
POLITICAL = (
    SOURCES / "politicalboundaries_shapefile" / "NA_PoliticalDivisions" / "data"
    / "boundaries_p_2021_v3.shp"
)  # fmt: skip
ECOREGIONS = (
    SOURCES / "terr_ecoregions_v2_level_iii_shapefile" / "NA_TerrEcoregions_III" / "data"
    / "NA_Terrestrial_Ecoregions_v2_level3.shp"
)  # fmt: skip
NALCMS = SOURCES / "nalcms/NA_NALCMS_landcover_2020v2_30m.tif"
TREEMAP = DRIVE / "t5" / "treemap2023"
MASK = T6B / "mask.tif"
MASK_INFO = T6B / "mask.json"
PLOTS = T6B / "plots.npz"
TILES = T6B / "tiles"
NATIVE_SOIL = T6B / "native" / "soil"
NATIVE_SCANFI = T6B / "native" / "scanfi"
MANIFEST = T6B / "manifest.jsonl"
PAUSE = T6B / "PAUSE"
EVIDENCE = REPO / "docs" / "audits" / "2026-10-07-t6b-run"
TREE_N, SOIL_N, SUPER = 256, 2048, 4
SCANFI_WHOLE = T6B / "scanfi_whole"
SCANFI_LAYER_TILES = T6B / "scanfi_layers"
REQUESTS = T6B / "requests"
FREE_MARGIN = 2_000_000_000  # bytes kept free beyond a layer being downloaded (D118)
PLOT_TABLE_RULINGS = "D87 to D91, D116"
TEN_CELLS = REPO / "docs" / "audits" / "2026-10-07-t6b-verify" / "ten_cells.json"


def log(msg: str) -> None:
    line = f"{datetime.now().astimezone().isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    with open(T6B / "run.log", "a") as f:
        f.write(line + "\n")


def mask_window() -> GridWindow:
    rings = [r for code, rs in political_rings(POLITICAL) if code in (COUNTRY_US48, COUNTRY_CAN)
             for r in rs]  # fmt: skip
    pts = np.vstack(rings)
    s = SOIL_N * CELL_SIZE_M  # snapped to whole soil tiles, so every tile reads inside it
    return GridWindow(
        int(np.floor(pts[:, 0].min() / s) * s), int(np.floor(pts[:, 1].min() / s) * s),
        int(np.ceil(pts[:, 0].max() / s) * s), int(np.ceil(pts[:, 1].max() / s) * s),
    )  # fmt: skip


def supersede(reason: str) -> None:
    """Move everything built on an older mask or plot table aside, kept, never deleted."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    dest = T6B / "superseded" / stamp
    dest.mkdir(parents=True)
    for name in ("mask.tif", "mask.json", "tiles_trees.json", "tiles_soil.json", "tiles",
                 "manifest.jsonl", "plots.npz", "plots.json", "scanfi_layers"):  # fmt: skip
        if (T6B / name).exists():
            shutil.move(str(T6B / name), str(dest / name))
    log(f"superseded ({reason}): moved to {dest}")


def stage_mask() -> None:
    if MASK.exists():
        info = json.loads(MASK_INFO.read_text()) if MASK_INFO.exists() else {}
        if info.get("version") == MASK_VERSION:
            return
        supersede(f"mask version {info.get('version')!r}, now {MASK_VERSION!r}")
    t0 = time.time()
    window = mask_window()
    counts = build_mask(POLITICAL, ECOREGIONS, window, MASK)
    info = {"version": MASK_VERSION, "counts": counts,
            "window": [window.left, window.bottom, window.right, window.top]}  # fmt: skip
    MASK_INFO.write_text(json.dumps(info, indent=2) + "\n")
    from forager_forecast.t6b_run import sha256_file

    append_line(MANIFEST, {"kind": "stage", "stage": "mask", "seconds": round(time.time() - t0, 1),
                           "sha256": sha256_file(MASK), **info})  # fmt: skip
    log(f"mask built in {time.time() - t0:.0f} s: {counts}")


def stage_plots() -> None:
    meta = T6B / "plots.json"
    if (
        PLOTS.exists()
        and meta.exists()
        and json.loads(meta.read_text()).get("rulings") == PLOT_TABLE_RULINGS
    ):
        return
    t0 = time.time()
    info = build_plot_table(
        TREEMAP / "RDS-2026-0038.zip", TREEMAP / "TreeMap2023_CONUS.tif.vat.dbf", PLOTS
    )
    meta.write_text(json.dumps({"rulings": PLOT_TABLE_RULINGS, **info}, indent=2) + "\n")
    append_line(MANIFEST, {"kind": "stage", "stage": "plots",
                           "seconds": round(time.time() - t0, 1), **info})  # fmt: skip
    log(f"plot table in {time.time() - t0:.0f} s: {info}")


def _window_from_info() -> GridWindow:
    return GridWindow(*json.loads(MASK_INFO.read_text())["window"])


def tile_list(n: int, name: str) -> list[dict]:
    """Tiles of size n with at least one study cell, and whether any is Canadian. Cached."""
    cache = T6B / f"tiles_{name}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    out = []
    for tile in tiles_over(_window_from_info(), n):
        study, side = cells_in_study(tile.window, *read_mask(MASK, tile.window))
        if study.any():
            out.append({"key": tile.key, "i": tile.i, "j": tile.j, "n": n,
                        "canada": bool((side == SIDE_CA).any())})  # fmt: skip
    cache.write_text(json.dumps(out) + "\n")
    return out


def _tile(key: str) -> Tile:
    n, i, j = (int(x) for x in key.split("_"))
    return Tile(i, j, n)


def super_key(key: str) -> str:
    t = _tile(key)
    return f"{SUPER * t.n}_{t.i // SUPER}_{t.j // SUPER}"


def tree_unit(key: str) -> dict:
    """A tree tile. Canadian cells take SCANFI from the whole-layer route (D118) when all eleven
    layers are regridded for this tile, else from a super-window fetched by window."""
    group = super_key(key)
    scanfi_dir = NATIVE_SCANFI / group
    layers_ready = all(
        (SCANFI_LAYER_TILES / f"scanfi_{layer}_{key}.npz").exists() for layer in SCANFI_LAYERS
    )
    result = tree_tile(
        _tile(key), MASK, TREEMAP / "TreeMap2023_CONUS.tif", PLOTS,
        scanfi_dir if (scanfi_dir / "scanfi_request.json").exists() else None, NALCMS,
        TILES / "trees", scanfi_layer_dir=SCANFI_LAYER_TILES if layers_ready else None,
    )  # fmt: skip
    result["scanfi_route"] = "whole layers (D118)" if layers_ready else "super-window"
    return result


def scanfi_layer_unit(key: str) -> dict:
    layer, tile = key.split(":")
    return scanfi_layer_tile(
        _tile(tile), SCANFI_WHOLE / f"{layer}.tif", layer, MASK, NALCMS, SCANFI_LAYER_TILES
    )


def stage_scanfi_layers(until, workers: int) -> dict:
    """D118: each SCANFI layer downloaded whole, one at a time, regridded over every Canadian
    tree tile, then deleted. A download stops at the section's stop time and resumes next time."""
    canadian = [t["key"] for t in tile_list(TREE_N, "trees") if t["canada"]]
    units = [f"{layer}:{key}" for layer in SCANFI_LAYERS for key in canadian]
    REQUESTS.mkdir(parents=True, exist_ok=True)

    def prepare(layer: str) -> dict:
        from forager_forecast.t6b_sources import download_resumable, http_headers, http_open_from

        path = SCANFI_WHOLE / f"{layer}.tif"
        request = REQUESTS / f"scanfi_whole_{layer}.request.json"
        if path.exists() and request.exists():
            return {"scanfi_whole": "already on the drive"}
        url = scanfi_url(layer, 2025)
        headers = http_headers(url)
        partial = path.with_name(path.name + ".partial")
        have = partial.stat().st_size if partial.exists() else 0
        try:
            free = require_free_space(T6B, headers["content_length"] - have + FREE_MARGIN)
        except OSError as err:
            log(f"SCANFI {layer}: not started, {err}")
            return {"stop_section": f"not enough free space for SCANFI {layer}: {err}"}
        requested_at = datetime.now(UTC).isoformat(timespec="seconds")
        t0 = time.time()
        result = download_resumable(http_open_from(url), headers["content_length"], path,
                                    deadline=until.timestamp())  # fmt: skip
        rate = (result["bytes"] - have) / max(time.time() - t0, 1e-9)
        log(f"SCANFI {layer}: {result['bytes']}/{headers['content_length']} bytes, "
            f"{rate / 1e3:.0f} kB/s, complete={result['complete']}")  # fmt: skip
        if not result["complete"]:
            return {"stop_section": f"SCANFI {layer} download not finished by the stop time",
                    "bytes": result["bytes"], "rate_bytes_per_s": round(rate)}  # fmt: skip
        record = {"source": url, "requested_at": requested_at, "account": "anonymous",
                  "http": headers, "file": path.name, "sha256": result["sha256"],
                  "free_bytes_before": free, "rulings": ["D92", "D118"]}  # fmt: skip
        request.write_text(json.dumps(record, indent=2) + "\n")
        return {"scanfi_whole": "downloaded", "rate_bytes_per_s": round(rate),
                "sha256": result["sha256"]}  # fmt: skip

    def cleanup(layer: str) -> dict:
        path = SCANFI_WHOLE / f"{layer}.tif"
        if path.exists():
            path.unlink()
        return {"scanfi_whole": "deleted, request kept"}

    log(f"scanfi-layers: {len(SCANFI_LAYERS)} layers over {len(canadian)} Canadian tiles")
    return run_section(units, scanfi_layer_unit, MANIFEST, SCANFI_LAYER_TILES, until=until,
                       pause_file=PAUSE, workers=workers, group_of=lambda u: u.split(":")[0],
                       prepare=prepare, cleanup=cleanup, layer="scanfi-layers")  # fmt: skip


def soil_unit(key: str) -> dict:
    result = soil_tile(_tile(key), MASK, NATIVE_SOIL, TILES / "soil")
    if "file" in result:
        result["files"] = {result["file"]: result["sha256"]}
    return result


def layers_ready(key: str) -> bool:
    return all(
        (SCANFI_LAYER_TILES / f"scanfi_{layer}_{key}.npz").exists() for layer in SCANFI_LAYERS
    )


def stage_trees(until, workers: int, max_units: int | None = None,
                only_groups: set[str] | None = None) -> dict:  # fmt: skip
    """Tree tiles that can run now: every US-only tile, and a tile with Canadian cells once the
    whole-layer route (D118) has all eleven SCANFI layers for it. No windowed SCANFI fetch."""
    tiles = tile_list(TREE_N, "trees")
    canadian = {t["key"] for t in tiles if t["canada"]}
    units = sorted((t["key"] for t in tiles),
                   key=lambda k: (-_tile(super_key(k)).j, _tile(super_key(k)).i,
                                  -_tile(k).j, _tile(k).i))  # fmt: skip
    waiting = [u for u in units if u in canadian and not layers_ready(u)]
    units = [u for u in units if u not in set(waiting)]
    log(f"trees: {len(tiles)} tiles, {len(canadian)} with Canadian cells; "
        f"{len(waiting)} wait for the SCANFI layers (D118)")  # fmt: skip
    if only_groups:
        units = [u for u in units if super_key(u) in only_groups]
        log(f"trees: this section offers only super-windows {sorted(only_groups)}")
    units = _first_pending(units, TILES / "trees", max_units)
    return run_section(units, tree_unit, MANIFEST, TILES / "trees", until=until, pause_file=PAUSE,
                       workers=workers, layer="trees")  # fmt: skip


def _first_pending(units: list[str], out_dir: Path, max_units: int | None) -> list[str]:
    """With --max-units N, this section offers only the first N tiles not yet done."""
    if max_units is None:
        return units
    done = done_units(MANIFEST, out_dir)
    return [u for u in units if u not in done][:max_units]


def stage_soil(until, workers: int, max_units: int | None = None) -> dict:
    units = [t["key"] for t in tile_list(SOIL_N, "soil")]
    log(f"soil: {len(units)} tiles")
    units = _first_pending(units, TILES / "soil", max_units)
    return run_section(units, soil_unit, MANIFEST, TILES / "soil", until=until, pause_file=PAUSE,
                       workers=workers, layer="soil")  # fmt: skip


def commit_progress(summaries: list[dict]) -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    shutil.copy(MANIFEST, EVIDENCE / "manifest.jsonl")
    for name in ("mask.json", "tiles_trees.json", "tiles_soil.json"):
        if (T6B / name).exists():
            shutil.copy(T6B / name, EVIDENCE / name)
    with open(EVIDENCE / "sections.jsonl", "a") as f:
        f.write(json.dumps({"summaries": summaries}) + "\n")
    shutil.copy(T6B / "run.log", EVIDENCE / "run.log.txt")
    subprocess.run(["git", "add", str(EVIDENCE)], cwd=REPO, check=True)
    done = sum(s.get("units_done_now", 0) for s in summaries)
    msg = (f"T6b run section: {done} tiles; " + "; ".join(
        f"{s.get('layer')}: {s.get('units_ok')} ok, {s.get('units_deferred')} deferred, "
        f"{s.get('units_remaining')} left, {s.get('stopped')}" for s in summaries)
        + "\n\nCo-Authored-By: Claude <noreply@anthropic.com>")  # fmt: skip
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO).returncode != 0:
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=REPO, check=True)
        subprocess.run(["git", "push", "-q", "origin", "t6b-continental-layers"], cwd=REPO,
                       check=False)  # fmt: skip


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--until", required=True, help="local HH:MM; no new tile starts after it")
    # Forager RECORD -620: night sections run mask, plots, soil, then the tree tiles that are
    # ready (US-only until the SCANFI layers are regridded). scanfi-layers is named explicitly.
    p.add_argument("--stages", default="mask,plots,soil,trees")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--max-soil-tiles", type=int, default=None,
                   help="at most this many new soil tiles in this section")  # fmt: skip
    p.add_argument("--max-tree-tiles", type=int, default=None)
    p.add_argument("--tree-groups", default=None,
                   help="comma-separated super-window keys this section may run")  # fmt: skip
    args = p.parse_args()
    if not DRIVE.is_dir():
        sys.exit("flash drive not mounted")
    until = next_stop(args.until, datetime.now())
    log(f"section start, until {until.isoformat(timespec='minutes')}, stages {args.stages}, "
        f"workers {args.workers}, pause file {PAUSE}")  # fmt: skip
    summaries = []
    try:
        for stage in args.stages.split(","):
            if PAUSE.exists() or datetime.now() >= until:
                log(f"not starting {stage}: stop condition")
                break
            if stage == "mask":
                stage_mask()
            elif stage == "plots":
                stage_plots()
            elif stage == "scanfi-layers":
                summaries.append(stage_scanfi_layers(until, args.workers))
            elif stage == "trees":
                summaries.append(
                    stage_trees(
                        until,
                        args.workers,
                        args.max_tree_tiles,
                        set(args.tree_groups.split(",")) if args.tree_groups else None,
                    )
                )
            elif stage == "soil":
                summaries.append(stage_soil(until, args.workers, args.max_soil_tiles))
            else:
                sys.exit(f"unknown stage {stage}")
            log(f"{stage}: {summaries[-1] if summaries and stage in ('trees', 'soil') else 'ok'}")
    finally:
        units = [e for e in read_lines(MANIFEST) if e.get("kind") == "unit"]
        log(f"section end: {len(units)} unit lines in the manifest")
        commit_progress(summaries)


if __name__ == "__main__":
    main()

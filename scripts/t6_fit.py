"""T6: count outings over D26's download, then fit and evaluate the effort surface (D101 to D108).

    uv run python scripts/t6_fit.py count ZIP OUT_DIR    # outings per track, step counts
    uv run python scripts/t6_fit.py fit OUT_DIR AUDIT_DIR [TRACK ...]

count reads D26's zip in place, streamed, never extracted, refuses a table without classKey, and
writes data/t6/counts/<track>_{fungi,lichen}.npz plus steps.json. fit runs the evaluation fixed in
docs/audits/2026-10-06-t6-proposal.md for each track ("all", then "cc"), writes the stored surface
to OUT_DIR/<track>/ and the results to AUDIT_DIR/<track>_results.json. A watchdog stops either
stage if resident memory passes 5 GB.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path

import numpy as np

from forager_forecast import effort as ef
from forager_forecast import effort_evaluation as ev
from forager_forecast.cells import Cell
from forager_forecast.records.filters import Pipeline, t6_effort_steps
from forager_forecast.records.occurrence import (
    OccurrenceLoader,
    missing_columns,
    read_occurrence_rows,
)

RSS_LIMIT_KB = 5 * 1024 * 1024
DOI_RECORD = Path("docs/pulls/gbif-fungi-us-canada-2015-2025.doi.json")


def _rss_kb() -> int:
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    raise RuntimeError("VmRSS not found")


def start_watchdog(peak: list[int]) -> None:
    def watch() -> None:
        while True:
            current = _rss_kb()
            peak[0] = max(peak[0], current)
            if current > RSS_LIMIT_KB:
                print(
                    f"STOP: resident memory {current} kB is over 5 GB", file=sys.stderr, flush=True
                )
                os._exit(3)
            time.sleep(1)

    threading.Thread(target=watch, daemon=True).start()


def log(line: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {line}", flush=True)


def save_counts(path: Path, counts: ef.OutingCounts) -> None:
    np.savez(
        path,
        lat_tenths=np.array([c.lat_tenths for c in counts.cells], dtype=np.int64),
        lon_tenths=np.array([c.lon_tenths for c in counts.cells], dtype=np.int64),
        cell=counts.cell,
        week=counts.week,
        day=counts.day,
        count=counts.count,
    )


def load_counts(path: Path) -> ef.OutingCounts:
    data = np.load(path)
    cells = [
        Cell(int(a), int(b)) for a, b in zip(data["lat_tenths"], data["lon_tenths"], strict=True)
    ]
    entries = zip(
        data["cell"].tolist(),
        data["week"].tolist(),
        data["day"].tolist(),
        data["count"].tolist(),
        strict=True,
    )
    return ef.OutingCounts.from_entries(cells, entries)


def count(zip_path: Path, out_dir: Path) -> None:
    peak = [0]
    start_watchdog(peak)
    started = time.time()

    def rows():
        with zipfile.ZipFile(zip_path) as archive, archive.open("occurrence.txt") as raw:
            reader = read_occurrence_rows(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
            first = True
            for row in reader:
                if first:
                    missing = missing_columns(row.keys())
                    if "classKey" not in row:
                        missing.append("classKey")
                    if missing:
                        raise SystemExit(f"columns missing: {missing}")
                    first = False
                yield row

    loader = OccurrenceLoader()
    pipeline = Pipeline(t6_effort_steps())
    survivors = pipeline.run(loader.load(rows()))
    log(f"pipeline done: {len(survivors)} survivors")
    counter = ef.OutingCounter()
    for record in survivors:
        counter.add(record)
    del survivors
    folder = out_dir / "counts"
    folder.mkdir(parents=True, exist_ok=True)
    summary = {
        "zip": zip_path.name,
        "rows_read": loader.rows_read,
        "unloadable": dict(loader.unloadable),
        "steps": [
            {"step": c.step, "before": c.before, "dropped": c.dropped, "after": c.after}
            for c in pipeline.counts
        ],
        "records_to_outings": counter.records_added,
        "records_in_partial_weeks": counter.outside_frame_weeks,
        "license_not_recognised": dict(counter.license_not_recognised),
        "tracks": {},
    }
    for track in ("all", "cc"):
        fungi = counter.counts(track, False)
        lichen = counter.counts(track, True, frame=fungi.cells)
        save_counts(folder / f"{track}_fungi.npz", fungi)
        save_counts(folder / f"{track}_lichen.npz", lichen)
        summary["tracks"][track] = {
            "frame_cells": fungi.n_cells,
            "bands": list(fungi.band_ids),
            "cells_per_band": {
                str(b): int((fungi.cell_band == i).sum()) for i, b in enumerate(fungi.band_ids)
            },
            "outings": fungi.total(),
            "lichen_outings": lichen.total(),
            "nonzero_entries": len(fungi.count),
            "frame_rows": fungi.n_cells * len(ef.frame_weeks()) * 2,
            "outings_by_year": {str(y): fungi.total(y) for y in ef.YEARS},
            "lichen_outings_by_year": {str(y): lichen.total(y) for y in ef.YEARS},
        }
    summary["seconds"] = round(time.time() - started, 1)
    summary["peak_rss_kb"] = peak[0]
    (folder / "steps.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


def season_comparison(counts: ef.OutingCounts, fungal: ef.Surface, lichen: ef.Surface) -> dict:
    """Each band's two season shapes, each divided by its own week-weighted mean: shown with no
    verdict (D103)."""
    weeks = counts.weeks_per_year_slot.sum(axis=0)
    out = {}
    for b, band in enumerate(counts.band_ids):
        f = fungal.season[b] / (fungal.season[b] @ weeks / weeks.sum())
        g = lichen.season[b] / (lichen.season[b] @ weeks / weeks.sum())
        out[str(band)] = {
            "cells": int((counts.cell_band == b).sum()),
            "all_fungi_peak_iso_week": int(np.argmax(f)) + 1,
            "lichen_peak_iso_week": int(np.argmax(g)) + 1,
            "all_fungi_max_over_min": float(f.max() / f.min()),
            "lichen_max_over_min": float(g.max() / g.min()),
            "correlation": float(np.corrcoef(f, g)[0, 1]) if f.std() > 0 and g.std() > 0 else None,
            "all_fungi_shape": [round(float(x), 4) for x in f],
            "lichen_shape": [round(float(x), 4) for x in g],
        }
    return out


def fit_track(out_dir: Path, audit_dir: Path, track: str) -> None:
    peak = [0]
    start_watchdog(peak)
    started = time.time()
    fungi = load_counts(out_dir / "counts" / f"{track}_fungi.npz")
    lichen = load_counts(out_dir / "counts" / f"{track}_lichen.npz")
    log(f"{track}: {fungi.n_cells} cells, {fungi.total():.0f} outings, {lichen.total():.0f} lichen")
    timing = time.time()
    probe = ef.fit(fungi, ef.YEARS, ef.Config(0.1, 1))
    log(f"{track}: one fit took {time.time() - timing:.2f} s, {probe.iterations} iterations")

    result = ev.evaluate(fungi, lichen, log=lambda line: log(f"{track}: {line}"))
    effort_name, full_name = ev.EFFORT, ev.LADDER[-1][0]
    verdict = {}
    point, interval = ev.difference_interval(
        result.per_cell[effort_name], result.per_cell[ev.CONSTANT]
    )
    verdict["beats_constant"] = {
        "effort_minus_constant": point,
        "interval_95": interval,
        "pass": ef.lower_deviance_condition(interval),
    }
    ladder = {}
    names = [ev.CONSTANT, *(n for n, _ in ev.LADDER), effort_name]
    for previous, current in zip(names[:-1], names[1:], strict=True):
        if current == effort_name:
            previous = full_name
        p, i = ev.difference_interval(result.per_cell[current], result.per_cell[previous])
        ladder[f"{current} vs {previous}"] = {"difference": p, "interval_95": i}
    pooled = {name: float(values.sum()) for name, values in result.per_cell.items()}
    p2, i2 = ev.difference_interval(result.per_cell[full_name], result.per_cell["+ season"])
    log(f"{track}: weekend bootstrap")
    ratio, ratio_interval = ev.weekend_ratio_interval(fungi, result.final_config)
    verdict["weekend"] = {
        "ratio": ratio,
        "interval_95": ratio_interval,
        "condition_1": ef.weekend_condition_1(ratio_interval),
        "day_type_minus_season_deviance": p2,
        "interval_95_condition_2": i2,
        "condition_2": ef.lower_deviance_condition(i2),
    }
    verdict["weekend"]["pass"] = (
        verdict["weekend"]["condition_1"] and verdict["weekend"]["condition_2"]
    )

    config = result.final_config
    fungal = ef.fit(fungi, ef.YEARS, config)
    lichen_fit = ef.fit(lichen, ef.YEARS, config)
    surface = ef.combine(fungal, lichen_fit, fungi, ef.YEARS)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    doi = json.loads(DOI_RECORD.read_text())
    manifest = {
        "task": "T6 effort surface (D101 to D108)",
        "licence_track": {"all": "all licences (D61)", "cc": "CC0_1_0 and CC_BY_4_0 only (D108)"}[
            track
        ],
        "input_doi": doi["doi"],
        "input_zip_sha256": doi["sha256_of_zip"],
        "code_commit": commit,
        "configuration": {
            "pull_pseudo_weeks": config.pull,
            "season_smoothing_weeks": config.smoothing,
        },
        "seed": ef.SEED,
        "frame_cells": fungi.n_cells,
        "frame_weeks": f"{ef.frame_weeks()[0].id} to {ef.frame_weeks()[-1].id}",
        "reads": "effort = cell_level.all_fungi x year_level.effort x season.effort (band, slot) x "
        "sum over day_type of all_fungi_per_day x days; forager_forecast.effort.EffortSurface",
    }
    digests = ef.write_surface(out_dir / track, fungi, fungal, lichen_fit, surface, manifest)
    results = {
        "track": track,
        "frame_cells": fungi.n_cells,
        "outings": fungi.total(),
        "lichen_outings": lichen.total(),
        "chosen_per_fold": {str(h): c.id for h, c in result.chosen.items()},
        "final_configuration": config.id,
        "outer_deviance_by_configuration": {c.id: v for c, v in result.outer_by_config.items()},
        "pooled_deviance": pooled,
        "pooled_deviance_year_level_interpolated": {
            n: float(v.sum()) for n, v in result.per_cell_interpolated.items()
        },
        "per_fold": {str(h): v for h, v in result.per_fold.items()},
        "per_fold_year_level_interpolated": {
            str(h): v for h, v in result.per_fold_interpolated.items()
        },
        "held_out_outings": {str(h): v for h, v in result.held_out_outings.items()},
        "verdict": verdict,
        "ladder": ladder,
        "beside_no_verdict": {
            "raw_weekend_ratio_all_fungi": ev.raw_weekend_ratios(fungi),
            "raw_weekend_ratio_lichen": ev.raw_weekend_ratios(lichen),
            "fitted_weekend_ratio_lichen": lichen_fit.weekend_ratio,
            "season_comparison_by_band": season_comparison(fungi, fungal, lichen_fit),
        },
        "stored_surface_sha256": digests,
        "fit_iterations_final": {"all_fungi": fungal.iterations, "lichen": lichen_fit.iterations},
        "seconds": round(time.time() - started, 1),
        "peak_rss_kb": peak[0],
    }
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / f"{track}_results.json").write_text(json.dumps(results, indent=2) + "\n")
    log(f"{track}: done; verdicts {json.dumps(verdict)}")


if __name__ == "__main__":
    if sys.argv[1] == "count":
        count(Path(sys.argv[2]), Path(sys.argv[3]))
    elif sys.argv[1] == "fit":
        for name in sys.argv[4:] or ["all", "cc"]:
            fit_track(Path(sys.argv[2]), Path(sys.argv[3]), name)
    else:
        raise SystemExit("usage: t6_fit.py count ZIP OUT_DIR | fit OUT_DIR AUDIT_DIR [TRACK ...]")

"""Features built by the scoring path equal features built by the training path, on a historical
Monday both can see (dispatch step 2; RECORD -814).

Run:  uv run python scripts/pnw_pilot_feature_check.py --cds-npz <npz from pnw_weather.build>
          --monday 2019-10-07 --cells 6 --out <dir> --ledger <live-weather ledger.jsonl>

Training path: the store's NetCDF files -> pnw_weather.build -> npz -> pnw_weather.weather_matrix.
Scoring path: Open-Meteo archive bodies (pinned per D19, D21, D25) -> open_meteo parser ->
pilot_output.weather_arrays -> npz -> pnw_weather.weather_matrix. The two npz files differ only in
where the daily values came from, so this is the D24 question asked one level up, of the 32
window features rather than the daily values.

Cells are drawn with seed 20260918 from the box's cells that the store has values for. A feature
the store cannot build yet (its variable's months not delivered) is reported as unavailable,
never as a pass. Bound: D24's half unit per daily value (equivalence_spec.md), so a mean is within
that half unit and a w-day sum within w half units; anything over the bound is listed.

The Open-Meteo request is entered in the fetch ledger so the day's budget counts it.
"""

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from pnw_weather import weather_matrix  # noqa: E402

from forager_forecast import live_weather as lw  # noqa: E402
from forager_forecast import pilot_output as po  # noqa: E402
from forager_forecast.cells import iso_week_of  # noqa: E402
from forager_forecast.daily_grid import FEATURES, feature_names  # noqa: E402
from forager_forecast.open_meteo import daily_weather_from_archive  # noqa: E402
from forager_forecast.t1_design import BOXES, WINDOW_DAYS  # noqa: E402

HALF_UNIT = {
    "temperature": 0.05,
    "precipitation": 0.05,
    "soil_temperature": 0.05,
    "soil_moisture": 0.0005,
}
EPS = 1e-6


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cds-npz", type=Path, required=True)
    ap.add_argument("--monday", type=date.fromisoformat, required=True)
    ap.add_argument("--cells", type=int, default=6)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--ledger", type=Path, required=True)
    a = ap.parse_args()
    if a.monday.isoweekday() != 1:
        raise SystemExit(f"{a.monday} is not a Monday")
    week = iso_week_of(a.monday)
    start, end = lw.window_span(week)
    z = np.load(a.cds_npz)
    po.check_ranges(z)  # the training side, built by pnw_weather.build with its own conversion
    have = {
        v: {tuple(int(x) for x in p) for p in z[f"{v}_points"]}
        for v in ("temperature", "precipitation")
    }
    pnw = next(b for b in BOXES if b.name == "pnw")
    box = lw.box_cells(pnw)
    if have["temperature"]:
        pool = [c for c in box if (c.lat_tenths, c.lon_tenths) in have["temperature"]]
    else:  # only rain delivered so far: any cell whose ERA5 point the store holds
        from forager_forecast.cells import quarter_cell_for  # noqa: PLC0415

        pool = [
            c
            for c in box
            if (lambda q: (q.lat_quarters, q.lon_quarters))(
                quarter_cell_for(c.center_latitude, c.center_longitude)
            )
            in have["precipitation"]
        ]
    rng = np.random.default_rng(20260918)
    cells = sorted(pool[int(i)] for i in rng.choice(len(pool), size=a.cells, replace=False))

    a.out.mkdir(parents=True, exist_ok=True)
    url = lw.multi_archive_url(cells, start, end)
    body_path = a.out / f"open-meteo-{a.monday.isoformat()}.json"
    if not body_path.exists():
        cost = lw.request_cost(len(cells), start, end)
        requested = datetime.now(UTC)
        with urllib.request.urlopen(url, timeout=180) as resp:
            status, raw = resp.status, resp.read()
        with a.ledger.open("a") as f:
            entry = {
                "utc": requested.isoformat(),
                "batch": "feature-check",
                "attempt": 1,
                "locations": len(cells),
                "cost": cost,
                "status": status,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "error": None,
            }
            f.write(json.dumps(entry) + "\n")
        body_path.write_bytes(raw)
        (a.out / f"open-meteo-{a.monday.isoformat()}.request.json").write_text(
            json.dumps({"url": url, "cells": [c.id for c in cells], **entry}, indent=1) + "\n"
        )
    per_cell = {}
    for c, item in lw.split_by_cell(cells, json.loads(body_path.read_bytes())).items():
        po.check_units(item)
        per_cell[c] = daily_weather_from_archive(item)
    live_npz = a.out / f"open-meteo-{a.monday.isoformat()}.npz"
    arrays = po.weather_arrays(per_cell, start, end)
    po.check_ranges(arrays)
    np.savez_compressed(live_npz, **arrays)

    rows = [{"cell": c, "scored": a.monday} for c in cells]
    train_x, names, _k1 = weather_matrix(a.cds_npz, rows)
    serve_x, names2, _k2 = weather_matrix(live_npz, rows)
    assert names == names2 == feature_names()
    report = {"monday": a.monday.isoformat(), "cells": [c.id for c in cells], "features": {}}
    over = []
    for j, name in enumerate(names):
        w = WINDOW_DAYS[j // len(FEATURES)]
        _prefix, variable, reduction = FEATURES[j % len(FEATURES)]
        bound = HALF_UNIT[variable] * (w if reduction == "sum" else 1) + EPS
        t, s = train_x[:, j], serve_x[:, j]
        if np.isnan(t).all():
            report["features"][name] = {"status": "unavailable: the store has no values yet"}
            continue
        if np.isnan(t).any() or np.isnan(s).any():
            report["features"][name] = {
                "status": "partial NaN",
                "train": t.tolist(),
                "serve": s.tolist(),
            }
            over.append(name)
            continue
        diff = float(np.max(np.abs(t - s)))
        ok = diff <= bound
        report["features"][name] = {
            "status": "within" if ok else "OVER",
            "max_abs_diff": diff,
            "bound": bound,
        }
        if not ok:
            over.append(name)
    compared = [n for n, r in report["features"].items() if not r["status"].startswith("unav")]
    report["compared"] = len(compared)
    report["over_bound"] = over
    (a.out / f"feature-check-{a.monday.isoformat()}.json").write_text(
        json.dumps(report, indent=1) + "\n"
    )
    print(json.dumps({k: report[k] for k in ("monday", "cells", "compared", "over_bound")}))
    for n in compared:
        print(n, report["features"][n])
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())

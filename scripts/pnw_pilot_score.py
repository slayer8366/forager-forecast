"""Score the PNW pilot for one ISO week and write the map's files (Forager RECORD -814).

Run:  uv run python scripts/pnw_pilot_score.py --week 2026-W41 --weather <live-weather dir>
          --model <model dir> --kind calendar|full --out <root> [--bridge <text>]
      uv run python scripts/pnw_pilot_score.py ... --synthetic   (a tiny booster on random data,
          for a sample the site can draw; its numbers mean nothing and the manifest says so)

The model directory is the builder's contract (planner, 2026-10-10): model.txt (a LightGBM
booster) and model.json naming the features in order. The features are built by the training
code itself: `pnw_t1_fit.calendar_matrix` for day of year and place at the cell centre on the
week's Monday, and `pnw_weather.weather_matrix` over this week's Open-Meteo days written in
pnw_weather's npz layout (pilot_output.weather_arrays). The names built here must equal the
model's list exactly, or the run stops.

A cell is scored when Open-Meteo returned all four variables for every one of the 90 days
(ERA5-Land has no value over sea) and its features are all finite. Other cells are left out of
the files, as D55 allows, and counted by reason in the manifest. The calendar model needs no
weather, but the same land rule applies so the two outputs cover the same cells.

Writes <out>/pnw-pilot/<week start>/cantharellus.geojson, the same features split by 1 degree
block under cantharellus/, and manifest.json, plus the weather npz beside the raw bodies.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from pnw_t1_fit import calendar_matrix  # noqa: E402
from pnw_weather import _index, weather_matrix  # noqa: E402

from forager_forecast import live_weather as lw  # noqa: E402
from forager_forecast import pilot_output as po  # noqa: E402
from forager_forecast.cells import Cell, IsoWeek  # noqa: E402
from forager_forecast.daily_grid import feature_names  # noqa: E402
from forager_forecast.open_meteo import ArchiveGap, daily_weather_from_archive  # noqa: E402
from forager_forecast.t1_design import BOXES  # noqa: E402

CALENDAR_NAMES = ["doy_sin", "doy_cos", "latitude", "longitude"]
FORBIDDEN = ("fruiting probability", "probability of finding", "chance of finding")

SIGHTING_CHANCE = (
    "Sighting chance: the chance chanterelles are reported in this weather cell this week, given "
    "at least one fungal observation of any kind there that week (D12). It is not the chance "
    "mushrooms are present, and not the chance you will find them."
)
COPERNICUS = (
    "Contains modified Copernicus Climate Change Service information 2024. Neither the European "
    "Commission nor ECMWF is responsible for any use that may be made of the Copernicus "
    "information or data it contains."
)
OPEN_METEO = "Weather data by Open-Meteo.com (https://open-meteo.com/), CC BY 4.0."
# D53, applied to the four datasets as docs/planning/evidence/
# 2026-09-20-cowork-attribution-licence-grid-report.md quotes them. Training read the two
# daily-statistics datasets through the Copernicus store; scoring reads ERA5-Land and ERA5 hourly
# through Open-Meteo.
ATTRIBUTION_DETAILS = [
    "ERA5-Land (scoring weather, via Open-Meteo): Generated using or contains modified Copernicus "
    "Climate Change Service information <2019>. Neither the European Commission nor ECMWF is "
    "responsible for any use that may be made of the Copernicus information or data it contains. "
    "Muñoz Sabater, J. (2019): ERA5-Land hourly data from 1950 to present. Copernicus Climate "
    "Change Service (C3S) Climate Data Store (CDS). DOI: 10.24381/cds.e2161bac",
    "ERA5 single levels (scoring rain, via Open-Meteo): Generated using or contains modified "
    "Copernicus Climate Change Service information 2023. Neither the European Commission nor "
    "ECMWF is responsible for any use that may be made of the Copernicus information or data it "
    "contains. Hersbach, H. et al. (2023): ERA5 hourly data on single levels from 1940 to "
    "present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS), "
    "DOI: 10.24381/cds.adbb2d47",
    "ERA5-Land daily statistics (training weather): " + COPERNICUS + " Muñoz Sabater, J., "
    "Comyn-Platt, E., Hersbach, H., Bell, B., Berrisford, P., Biavati, G., Horányi, A., Muñoz "
    "Sabater, J., Nicolas, J., Peubey, C., Radu, R., Rozum, I., Schepers, D., Simmons, A., Soci, "
    "C., Dee, D., Thépaut, J-N., Cagnazo, C., Cucchi, M. (2024): ERA5-land post-processed "
    "daily-statistics from 1950 to present. Copernicus Climate Change Service (C3S) Climate Data "
    "Store (CDS), DOI: 10.24381/cds.e9c9c792",
    "ERA5 single levels daily statistics (training rain): " + COPERNICUS + " Hersbach, H., "
    "Comyn-Platt, E., Bell, B., Berrisford, P., Biavati, G., Horányi, A., Muñoz Sabater, J., "
    "Nicolas, J., Peubey, C., Radu, R., Rozum, I., Schepers, D., Simmons, A., Soci, C., Dee, D., "
    "Thépaut, J-N., Cagnazo, C., Cucchi, M. (2023): ERA5 post-processed daily-statistics on single "
    "levels from 1940 to present. Copernicus Climate Change Service (C3S) Climate Data Store "
    "(CDS), DOI: 10.24381/cds.4991cf48",
    "Weather served through Open-Meteo.com, CC BY 4.0.",
]


def log(msg: str) -> None:
    print(f"{datetime.now(UTC).isoformat(timespec='seconds')} {msg}", flush=True)


def parse_week(text: str) -> IsoWeek:
    year, week = text.split("-W")
    return IsoWeek(int(year), int(week))


def read_live_weather(weather_dir: Path, start: date, end: date):
    """Every saved batch, split by cell and parsed by the archive parser; cells it refuses are
    returned with the parser's reason."""
    per_cell, refused, batches = {}, {}, 0
    for req_path in sorted((weather_dir / "raw").glob("batch_*.request.json")):
        req = json.loads(req_path.read_text())
        if (req["start"], req["end"]) != (start.isoformat(), end.isoformat()):
            raise SystemExit(
                f"{req_path} covers {req['start']} to {req['end']}, not {start}..{end}"
            )
        body_path = req_path.with_name(req_path.name.replace(".request", ""))
        raw = body_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != req["sha256"]:
            raise SystemExit(f"{body_path} does not match the hash in its request record")
        cells = [Cell(*map(int, cid.split("_"))) for cid in req["cells"]]
        for cell, item in lw.split_by_cell(cells, json.loads(raw)).items():
            po.check_units(item)
            try:
                per_cell[cell] = daily_weather_from_archive(item)
            except ArchiveGap as err:
                refused[cell] = str(err)
        batches += 1
    return per_cell, refused, batches


def store_land_cells(cds_dir: Path) -> tuple[set[tuple[int, int]], str]:
    """ERA5-Land's land cells in T1's box, from the first land file the store holds (either route):
    a cell is land when its first day's 2 m temperature has a value. The mask does not change with
    the day, so any delivered month gives it."""
    import h5py  # noqa: PLC0415

    files = sorted(cds_dir.glob("era5land-*.nc")) + sorted(
        cds_dir.glob("hourly-era5land-*.daily.h5")
    )
    if not files:
        raise SystemExit(f"no ERA5-Land file of T1's box in {cds_dir}")
    with h5py.File(files[0]) as h:
        lat, lon = _index(h["latitude"][:], 0.1), _index(h["longitude"][:], 0.1)
        first = h["t2m"][0]
    land = {
        (int(la), int(lo))
        for i, la in enumerate(lat)
        for j, lo in enumerate(lon)
        if np.isfinite(first[i, j])
    }
    return land, files[0].name


def synthetic_model(model_dir: Path, kind: str) -> None:
    """A tiny booster on random data, with the feature list a real model of `kind` carries."""
    import lightgbm as lgb  # noqa: PLC0415

    names = CALENDAR_NAMES + (feature_names() if kind == "full" else [])
    rng = np.random.default_rng(20260918)
    x = rng.normal(size=(400, len(names)))
    y = (x[:, 0] + rng.normal(size=400) > 1.0).astype(float)
    params = {"objective": "binary", "verbose": -1, "seed": 20260918, "num_leaves": 4}
    booster = lgb.train(params, lgb.Dataset(x, y, feature_name=names), num_boost_round=5)
    model_dir.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(model_dir / "model.txt"))
    (model_dir / "model.json").write_text(
        json.dumps({"features": names, "synthetic": True}, indent=1) + "\n"
    )


def model_features(meta: dict) -> list[str]:
    for key in ("features", "feature_names"):
        if key in meta:
            return list(meta[key])
    raise SystemExit(f"model.json names no feature list (keys: {sorted(meta)})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", required=True)
    ap.add_argument("--weather", type=Path, help="Open-Meteo live-weather dir (cross-check)")
    ap.add_argument(
        "--cds-npz",
        type=Path,
        help="the store's daily statistics for the window, built by pnw_weather.build "
        "(scripts/pnw_pilot_cds_build.py); the scoring source the owner chose (RECORD -819)",
    )
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--kind", choices=["calendar", "full"], required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--bridge", default="")
    ap.add_argument("--beats-calendar", choices=["true", "false", "null"], default="null")
    ap.add_argument("--t1-result", default="", help="JSON text of the builder's headline, or empty")
    ap.add_argument(
        "--land-from-store",
        type=Path,
        help="calendar model only: score every ERA5-Land land cell of the box, read from the "
        "store's directory, with no weather (the floor output)",
    )
    a = ap.parse_args()
    given = [x for x in (a.weather, a.cds_npz, a.land_from_store) if x is not None]
    if len(given) != 1:
        raise SystemExit("give exactly one of --weather, --cds-npz, --land-from-store")
    if a.land_from_store and a.kind != "calendar":
        raise SystemExit("--land-from-store has no weather, so it scores the calendar model only")
    source = "copernicus" if a.cds_npz else "open-meteo" if a.weather else "none"
    import lightgbm as lgb  # noqa: PLC0415

    week = parse_week(a.week)
    monday = week.monday()
    start, end = lw.window_span(week)
    if a.synthetic:
        synthetic_model(a.model, a.kind)
    model_txt = (a.model / "model.txt").read_bytes()
    meta = json.loads((a.model / "model.json").read_text())
    expected = CALENDAR_NAMES + (feature_names() if a.kind == "full" else [])
    names = model_features(meta)
    if names != expected:
        raise SystemExit(f"model features {names} are not the {a.kind} model's {expected}")
    digest = hashlib.sha256(model_txt).hexdigest()
    kind_label = "synthetic" if a.synthetic else a.kind
    model_version = f"pnw-pilot-t1-{kind_label}-{digest[:12]}"

    pnw = next(b for b in BOXES if b.name == "pnw")
    box = lw.box_cells(pnw)
    batches = None
    mask_file = None
    if source == "none":
        has, mask_file = store_land_cells(a.land_from_store)
        land = [c for c in box if (c.lat_tenths, c.lon_tenths) in has]
        refused = {c: "no ERA5-Land value in the store" for c in box if c not in set(land)}
        per_cell = set(land)
        npz = None
    elif source == "open-meteo":
        per_cell, refused, batches = read_live_weather(a.weather, start, end)
        npz = a.weather / f"weather_{week.id}.npz"
        arrays = po.weather_arrays(per_cell, start, end)
        po.check_ranges(arrays)
        np.savez_compressed(npz, **arrays)
        land = sorted(per_cell)
    else:
        npz = a.cds_npz
        z = np.load(npz)
        po.check_ranges(z)
        z_start = date.fromisoformat(str(z["start"]))
        if (
            z_start > start
            or (z_start - start).days + z["temperature_values"].shape[1] <= (end - start).days
        ):
            raise SystemExit(f"{npz} does not span {start} to {end}")
        values = z["temperature_values"]
        has = {
            (int(la), int(lo))
            for (la, lo), row in zip(z["temperature_points"], values, strict=True)
            if np.isfinite(row).any()
        }
        land = [c for c in box if (c.lat_tenths, c.lon_tenths) in has]
        refused = {c: "no ERA5-Land value in the store" for c in box if c not in set(land)}
        per_cell = set(land)
    rows = [
        {"cell": c, "scored": monday, "lat": c.center_latitude, "lon": c.center_longitude}
        for c in land
    ]
    cal_x, cal_names = calendar_matrix(rows) if rows else (np.zeros((0, 4)), CALENDAR_NAMES)
    assert cal_names == CALENDAR_NAMES
    if npz is not None and rows:
        wx, wnames = weather_matrix(npz, rows)
    else:
        wx, wnames = np.full((len(rows), 32), np.nan), feature_names()
    # The weather model needs every window; the calendar model needs only a land cell, so a
    # weather gap never removes a cell from the calendar output.
    complete = np.isfinite(wx).all(axis=1) if a.kind == "full" else np.ones(len(rows), bool)
    x = np.hstack([cal_x, wx]) if a.kind == "full" else cal_x
    all_names = cal_names + (wnames if a.kind == "full" else [])
    if all_names != names:
        raise SystemExit("built feature order differs from the model's")
    booster = lgb.Booster(model_file=str(a.model / "model.txt"))
    scored_idx = np.where(complete)[0]
    p = booster.predict(x[scored_idx]) if len(scored_idx) else np.zeros(0)
    contrib = (
        booster.predict(x[scored_idx], pred_contrib=True)
        if a.kind == "full" and len(scored_idx)
        else None
    )
    feats = []
    for k, i in enumerate(scored_idx):
        drv = po.drivers(all_names, x[i], contrib[k]) if contrib is not None else []
        through = end if a.kind == "full" else None
        feats.append(po.cell_feature(land[i], monday, float(p[k]), through, model_version, drv))

    omitted = Counter()
    for c in box:
        if c in refused:
            omitted["no_era5_land_value_(sea)"] += 1
        elif c not in per_cell:
            omitted["not_fetched_yet"] += 1
    omitted["incomplete_weather_window"] += int((~complete).sum())

    week_dir = a.out / "pnw-pilot" / monday.isoformat()
    block_dir = week_dir / "cantharellus"
    block_dir.mkdir(parents=True, exist_ok=True)
    for old in block_dir.glob("*.geojson"):
        old.unlink()
    files = {}
    combined = week_dir / "cantharellus.geojson"
    combined.write_text(json.dumps(po.collection(feats), separators=(",", ":"), ensure_ascii=False))
    files[str(combined.relative_to(a.out))] = combined
    block_names = []
    for bid, fc in po.blocks(feats).items():
        path = block_dir / f"{bid}.geojson"
        path.write_text(json.dumps(fc, separators=(",", ":"), ensure_ascii=False))
        files[str(path.relative_to(a.out))] = path
        block_names.append(bid)

    chances = np.array([f["properties"]["chance"] for f in feats]) if feats else np.zeros(0)
    ledger = a.weather / "ledger.jsonl" if a.weather else None
    calls = (
        sum(json.loads(line)["cost"] for line in ledger.read_text().splitlines())
        if ledger and ledger.exists()
        else None
    )
    manifest = {
        "published_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "pilot": True,
        "validated": False,
        "reviewed": False,
        "status_label": (
            "Unvalidated pilot. Unreviewed. Shown whether or not it beats the calendar."
        ),
        "model_kind": kind_label,
        "model_kind_note": {
            "synthetic": "SYNTHETIC SAMPLE: a tiny model on random numbers, for drawing only. "
            "The chances mean nothing.",
            "calendar": "Calendar model: day of year and place only. It knows nothing about this "
            "year's weather.",
            "full": "Weather model: day of year, place and T1's 32 weather windows.",
        }[kind_label],
        "beats_calendar": {"true": True, "false": False, "null": None}[a.beats_calendar],
        "t1_result": json.loads(a.t1_result) if a.t1_result else None,
        "sighting_chance_meaning": SIGHTING_CHANCE,
        "groups": [po.GROUP],
        "week": monday.isoformat(),
        "iso_week": week.id,
        "regions_published": [],
        "regions_note": (
            "No ecoregion is published under D5 (published only after beating the calendar on "
            "held-out years). The owner asked for this pilot to be shown regardless (Forager "
            "RECORD -814)."
        ),
        "attribution": f"{COPERNICUS} {OPEN_METEO}",
        "attribution_details": ATTRIBUTION_DETAILS,
        "layers": [
            {
                "kind": "cells_combined",
                "group": "cantharellus",
                "path": str(combined.relative_to(a.out)),
            },
            {
                "kind": "cell_blocks",
                "group": "cantharellus",
                "prefix": str(block_dir.relative_to(a.out)) + "/",
                "blocks": block_names,
                "block_naming": "south-west corner of the 1 degree square holding the cell "
                "centre, e.g. n47w123 holds centres 47 to 48 N, 123 to 122 W",
            },
        ],
        "layers_note": "No raster PMTiles and no vector PMTiles exist for the pilot.",
        "uncertainty_note": "uncertainty_low and uncertainty_high are null: the pilot model "
        "gives no interval.",
        "drivers_note": (
            "Up to three weather windows that moved this cell's score most (LightGBM "
            "contributions), largest first, each with its own value. Empty for the calendar "
            "model, which reads no weather."
        ),
        "applicable_note": (
            "Cells are listed only when scored. A cell is left out when the weather source has "
            "no ERA5-Land value for it (sea), or, for the weather model, any of its 90 days is "
            "missing. No area-of-applicability or training-range check (R7) has been run."
        ),
        "cells": {
            "in_box": len(box),
            "scored": len(feats),
            "omitted": dict(omitted),
            "chance_min": float(chances.min()) if len(chances) else None,
            "chance_median": float(np.median(chances)) if len(chances) else None,
            "chance_max": float(chances.max()) if len(chances) else None,
        },
        "weather_through": end.isoformat() if a.kind == "full" else None,
        "weather_through_note": (
            "null: the calendar model reads no weather."
            if a.kind == "calendar"
            else "the last day the windows read: the day before the week's Monday."
        ),
        "weather_source": source,
        "weather": {
            "source": (
                "Copernicus Climate Data Store: derived-era5-land-daily-statistics (daily_mean "
                "of 2m_temperature, soil_temperature_level_1, volumetric_soil_water_layer_1) and "
                "derived-era5-single-levels-daily-statistics (daily_sum of total_precipitation), "
                "time_zone utc+00:00, frequency 1_hourly: the products and requests training "
                "used (owner, Forager RECORD -819)"
                if source == "copernicus"
                else "none: calendar model, land cells from the store's ERA5-Land grid"
                if source == "none"
                else "Open-Meteo historical archive, models=era5_seamless, elevation=nan, "
                "cell_selection=nearest, timezone=UTC (D19, D21, D25)"
            ),
            "npz_sha256": hashlib.sha256(Path(npz).read_bytes()).hexdigest() if npz else None,
            "land_mask_from": mask_file,
            "days": [start.isoformat(), end.isoformat()],
            "open_meteo_batches": batches,
            "api_calls_by_pricing_rule": calls,
        },
        "weather_bridge": a.bridge or None,
        "model": {
            "version": model_version,
            "model_txt_sha256": digest,
            "model_json": meta,
        },
        "box": {
            "name": "pnw",
            "south": pnw.south,
            "north": pnw.north,
            "west": pnw.west,
            "east": pnw.east,
        },
    }
    manifest_path = week_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    files[str(manifest_path.relative_to(a.out))] = manifest_path
    for rel, path in files.items():
        text = path.read_text().lower()
        hits = [t for t in FORBIDDEN if t in text]
        if hits:
            raise SystemExit(f"{rel} carries forbidden terms {hits}")
    total = sum(path.stat().st_size for path in files.values())
    log(
        f"{kind_label}: {len(feats)} cells scored of {len(box)}, omitted {dict(omitted)}; "
        f"{len(files)} files, {total} bytes under {week_dir}"
    )
    for rel, path in sorted(files.items()):
        if not rel.endswith(".geojson") or "/cantharellus/" not in rel:
            log(f"  {rel} sha256 {hashlib.sha256(path.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

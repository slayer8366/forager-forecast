"""T7 re-fit, Phase 1 item 4 (dispatch 2026-10-17-T7R; Forager RECORD -1160, -1182): the specimen
records for P10b condition 4, as ONE occurrence download from the aggregator.

Usage:
  python scripts/t7_specimens.py submit <record json>
  python scripts/t7_specimens.py fetch  <record json> <data dir>
  python scripts/t7_specimens.py filter <record json> <data dir> <evidence dir>

``submit`` sends ``specimens.specimen_predicate()`` once, with the account in
``~/.config/forager-forecast/gbif.env`` (D26's account), and writes the key into the record; it
refuses if the record already exists, so a second request is an error, not a silent redo.
``fetch`` waits for the download, fetches its zip once (``gbif_download.fetch_download``: the size
checked against the aggregator's record, the file refused if it exists), records the DOI, size and
sha256 and makes the file read-only. ``filter`` reads the archive, checks its record and dataset
counts against the aggregator's record, keeps CC0 and CC BY records with a stated uncertainty of
1,000 m or less whose genus is in the mycorrhizal main run (``specimens.classify``), writes them
read-only, and writes the counts. Nothing is scored against the map: that is an owner's ruling.
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import re
import sys
import time
import zipfile
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from forager_forecast.grid import cell_for_lonlat
from forager_forecast.pnw import pnw_window
from forager_forecast.records import gbif_download as gd
from forager_forecast.t7 import specimens as sp
from forager_forecast.t7.ecoregions import burn_level3, read_level3
from forager_forecast.t7.keying import pack, weather_cells
from forager_forecast.t7.membership import MAIN_RUN, MYCORRHIZAL_GROUP, Join, load_list

REPO = Path(__file__).resolve().parent.parent
ENV_FILE = Path.home() / ".config/forager-forecast/gbif.env"
V9 = Path("/mnt/work/Zynergy/forecast-data/t7/v9")
LIST_FILE = V9 / "membership_list_fungaltraits_export.tsv"
TABLE_WORK = Path("/mnt/work/Zynergy/forecast-data/t7/refit")
csv.field_size_limit(1 << 24)


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def env_credentials() -> gd.GbifCredentials:
    env = dict(os.environ)
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return gd.credentials_from_env(env)


def cmd_submit(record: Path) -> None:
    if record.exists():
        raise SystemExit(f"{record} exists: the download was already requested (one request)")
    predicate = sp.specimen_predicate()
    key = gd.submit_download_request(env_credentials(), predicate)
    write_json(record, {
        "purpose": "T7 re-fit, P10b condition 4: herbarium specimen records in the PNW box "
                   "(dispatch docs/dispatch/2026-10-17-t7-refit.md, branch t7-strengthen-plan; "
                   "Forager RECORD -1160, -1182, -1183)",
        "download_key": key, "submitted_utc": now(),
        "request": gd.request_template(predicate),
        "predicate_source": "forager_forecast.t7.specimens.specimen_predicate()",
        "submitted_with": "scripts/t7_specimens.py submit; gbif_download.submit_download_request; "
                          "credentials from ~/.config/forager-forecast/gbif.env (D26's account: "
                          "its download 0012112-260928105237408 is in that account's list, read "
                          "2026-10-17); creator and notification address not recorded here",
    })  # fmt: skip
    print(key)


def cmd_fetch(record: Path, data: Path) -> None:
    rec = json.loads(record.read_text(encoding="utf-8"))
    key = rec["download_key"]
    while True:
        try:
            status = gd.download_status(key)
        except OSError as error:  # a status read only, never the file: logged, read again
            print(f"{now()} status read failed: {error!r}; trying again in 60 s", flush=True)
            time.sleep(60)
            continue
        if status["status"] in ("SUCCEEDED", "FAILED", "KILLED", "CANCELLED", "FILE_ERASED"):
            break
        print(f"{now()} {status['status']}", flush=True)
        time.sleep(60)
    if status["status"] != "SUCCEEDED":
        raise SystemExit(f"download {key}: {status['status']}")
    data.mkdir(parents=True, exist_ok=True)
    got = gd.fetch_download(key, data, int(status["size"]))
    os.chmod(got["path"], 0o444)
    rec.update({
        "doi": status.get("doi"), "created_utc": status.get("created"),
        "succeeded_utc": status.get("modified"), "total_records": status.get("totalRecords"),
        "number_of_datasets": status.get("numberDatasets"),
        "size_bytes": got["size_bytes"], "sha256_of_zip": got["sha256"],
        "gbif_license_of_download": status.get("license"),
        "stored_request": status.get("request"),
        "local_copy": got["path"], "fetched_utc": now(),
        "integrity_check": "The aggregator publishes no checksum for a download. The fetched zip's "
                           "byte size equals the download record's size field (fetch_download "
                           "refuses otherwise); the sha256 is this machine's own. The archive's "
                           "record and dataset counts are checked against the record by "
                           "scripts/t7_specimens.py filter.",
        "gbif_erases_after": status.get("eraseAfter"),
    })  # fmt: skip
    write_json(record, rec)
    print(json.dumps({k: rec[k] for k in ("doi", "size_bytes", "sha256_of_zip", "total_records")}))


def _fit_module():
    spec = importlib.util.spec_from_file_location("t7_fit", REPO / "scripts" / "t7_fit.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dataset_licences(z: zipfile.ZipFile) -> dict[str, dict]:
    """Each dataset's licence as its metadata in the archive states it (EML intellectualRights)."""
    out = {}
    for name in z.namelist():
        if not (name.startswith("dataset/") and name.endswith(".xml")):
            continue
        text = z.read(name).decode("utf-8", errors="replace")
        rights = re.search(r"<intellectualRights>(.*?)</intellectualRights>", text, re.S)
        rights_text = rights.group(1) if rights else ""
        url = re.search(r'url="([^"]+)"', rights_text)
        title = re.search(r"<title[^>]*>(.*?)</title>", text, re.S)
        out[Path(name).stem] = {
            "licence": url.group(1) if url else " ".join(re.sub(r"<[^>]+>", " ",
                                                                rights_text).split()),
            "title": " ".join(title.group(1).split()) if title else "",
        }  # fmt: skip
    return out


def decade(year: str) -> str:
    return f"{int(year) // 10 * 10}s" if year.strip().isdigit() else "no year"


def cmd_filter(record: Path, data: Path, evidence: Path) -> None:
    rec = json.loads(record.read_text(encoding="utf-8"))
    zpath = Path(rec["local_copy"])
    evidence.mkdir(parents=True, exist_ok=True)
    counts_v9 = json.loads((V9 / "counts.json").read_text(encoding="utf-8"))
    members = load_list(LIST_FILE, counts_v9["membership_list_sha256"])
    join = Join(members, counts_v9["membership_list_sha256"], MYCORRHIZAL_GROUP, MAIN_RUN)
    t7 = _fit_module()
    codes = dict(np.load(TABLE_WORK / "codes.npz"))
    frame = t7._frame_keys(t7.T6 / "all")
    window = pnw_window()
    _, polygons = read_level3(t7.LEVEL3)
    level3 = burn_level3(polygons, window)
    l3_names = {e.code: f"{e.level3} {e.name}" for e in read_level3(t7.LEVEL3)[0]}

    reasons = Counter()
    by_dataset = defaultdict(Counter)
    kept = []
    with zipfile.ZipFile(zpath) as z:
        licences = dataset_licences(z)
        with z.open("occurrence.txt") as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", newline=""),
                                    delimiter="\t", quoting=csv.QUOTE_NONE)  # fmt: skip
            n = 0
            for row in reader:
                n += 1
                ds = row.get("datasetKey", "")
                why = sp.classify(row, licences.get(ds, {}).get("licence", ""), join)
                reasons[why] += 1
                by_dataset[ds]["records"] += 1
                by_dataset[ds][why] += 1
                if why == sp.KEPT:
                    kept.append(row)
    if n != rec["total_records"]:
        raise SystemExit(
            f"archive holds {n} records, the aggregator's record {rec['total_records']}"
        )
    if len(by_dataset) != rec["number_of_datasets"] or set(by_dataset) - set(licences):
        raise SystemExit(f"{len(by_dataset)} datasets in records, {len(licences)} with metadata, "
                         f"the aggregator's record {rec['number_of_datasets']}")  # fmt: skip
    sp.assert_open_licences(kept, {k: v["licence"] for k, v in licences.items()})

    out_rows = []
    tally = defaultdict(Counter)
    for row in kept:
        lon, lat = float(row["decimalLongitude"]), float(row["decimalLatitude"])
        u = float(row["coordinateUncertaintyInMeters"])
        cell = cell_for_lonlat(lon, lat)
        try:
            r, c = window.pixel_of_cell(cell)
            block = int(level3[r, c])
        except IndexError:
            block = 0
        code = int(t7.tile_code_of(np.array([cell.id]), codes)[0])
        lat_t, lon_t = weather_cells(np.array([lon]), np.array([lat]))
        wk = int(pack(int(lat_t[0]), int(lon_t[0])))
        interior = bool(sp.INTERIOR.contains(lon, lat))
        out_rows.append({
            "gbif_id": row["gbifID"], "dataset_key": row["datasetKey"], "genus": row["genus"],
            "year": row.get("year", ""), "lat": lat, "lon": lon, "uncertainty_m": u,
            "license": row["license"], "dataset_licence": licences[row["datasetKey"]]["licence"],
            "cell_id": cell.id, "level3": block, "cell_code": code, "interior": interior,
        })  # fmt: skip
        tally["by block"][l3_names.get(block, "outside every block")] += 1
        tally["by decade"][decade(row.get("year", ""))] += 1
        tally["by uncertainty band"][sp.uncertainty_band(u)] += 1
        tally["by cell code (P4)"][str(code)] += 1
        tally["by dataset licence"][sp.licence_class(licences[row["datasetKey"]]["licence"])] += 1
        tally["record's weather cell in T6's effort frame"][str(wk in frame)] += 1
        tally["by genus"][row["genus"]] += 1
        if interior:
            tally["interior sub-box (42 to 49 N, 120 to 111 W)"]["kept"] += 1
            tally["interior, by uncertainty band"][sp.uncertainty_band(u)] += 1
            tally["interior, by cell code (P4)"][str(code)] += 1

    out = data / "specimens_kept.csv"
    if out.exists():
        raise SystemExit(f"{out} exists; written once")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)
    os.chmod(out, 0o444)
    import hashlib  # noqa: PLC0415

    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    datasets = [{"dataset_key": k, "title": licences.get(k, {}).get("title", ""),
                 "licence": licences.get(k, {}).get("licence", ""),
                 "licence_class": sp.licence_class(licences.get(k, {}).get("licence", "")),
                 **{r: v for r, v in c.items()}}
                for k, c in sorted(by_dataset.items(),
                                   key=lambda kv: -kv[1]["records"])]  # fmt: skip
    licence_counts = Counter()
    for d in datasets:
        licence_counts[d["licence_class"] or d["licence"]] += 1
    result = {
        "written_utc": now(), "download_key": rec["download_key"], "doi": rec["doi"],
        "zip_sha256": rec["sha256_of_zip"], "records_in_archive": n,
        "records_in_aggregator_record": rec["total_records"],
        "datasets_in_archive": len(by_dataset), "datasets_in_aggregator_record":
            rec["number_of_datasets"],
        "membership_list_sha256": members.sha256, "group": "mycorrhizal group, main run",
        "rules": {"licence": "dataset and record licence CC0 or CC BY",
                  "uncertainty": f"stated, at most {sp.MAX_UNCERTAINTY_M:g} m",
                  "genus": "in the main run (Join, lifestyle ectomycorrhizal, certainty clear)"},
        "outcomes": dict(reasons), "kept": len(kept),
        "kept_file": {"path": str(out), "sha256": digest, "bytes": out.stat().st_size},
        "datasets_by_licence": dict(licence_counts),
        "tallies_of_kept": {k: dict(sorted(v.items(), key=lambda kv: -kv[1]))
                            for k, v in tally.items()},
        "datasets": datasets,
    }  # fmt: skip
    write_json(evidence / "specimen_counts.json", result)
    print(json.dumps({k: result[k] for k in ("records_in_archive", "outcomes", "kept")}))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == "submit":
        cmd_submit(Path(a[1]))
    elif a[0] == "fetch":
        cmd_fetch(Path(a[1]), Path(a[2]))
    elif a[0] == "filter":
        cmd_filter(Path(a[1]), Path(a[2]), Path(a[3]))
    else:
        raise SystemExit(__doc__)

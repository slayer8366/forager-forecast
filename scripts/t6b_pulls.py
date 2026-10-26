"""Part A of the pulls queue (dispatch 2026-10-26-pulls): T6b's sources, one download at a time.

Run by the queue's driver (scripts/pulls_queue.sh on t8b-build) inside the detached unit; it can
also be run alone, from this repository's root:
    <venv>/bin/python scripts/t6b_pulls.py [cec] [nalcms] [treemap] [scanfi]
With no step named it runs all four, in that order. Exit 0: every step finished; 2: the queue
stopped itself (checksum mismatch, login wall, low space, PAUSE, network); 1: an error. The reason
is the last line of forecast-data/pulls/queue.log.
"""

import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from forager_forecast import pulls_queue as pq
from forager_forecast import t6b_pulls as tp
from forager_forecast import zip_extract as zx
from forager_forecast.drive import DRIVE
from forager_forecast.t5_layer import scanfi_url
from forager_forecast.t6b_layers import SCANFI_LAYERS
from forager_forecast.t6b_sources import (
    CEC_ECOREGIONS_URL,
    CEC_POLITICAL_URL,
    NALCMS_SMALL_MEMBERS,
    NALCMS_TIF_MEMBER,
    NALCMS_URL,
    download_layers,
    extract_zip_member,
    http_headers,
    http_range_reader,
)

LOG = DRIVE / "pulls" / "queue.log"
DISPATCH = "docs/dispatch/2026-10-26-pulls.md (t8b-build), Part A"


def log(msg: str) -> None:
    line = f"{datetime.now(UTC).isoformat(timespec='seconds')} [A] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def http_open(url: str):
    """A GET that hands back a 401 or 403 as a response, so the login-wall check sees it."""
    request = urllib.request.Request(url, headers={"User-Agent": "forager-forecast-pulls"})
    try:
        return urllib.request.urlopen(request, timeout=300)
    except urllib.error.HTTPError as err:
        if err.code in (401, 403):
            return err
        raise


def should_stop(still: int):
    return pq.stop_reason(DRIVE, still)


def _extract_done(record_path) -> bool:
    if not record_path.exists():
        return False
    rec = json.loads(record_path.read_text())
    return all(
        Path(f["path"]).is_file() and Path(f["path"]).stat().st_size == f["bytes"]
        for f in rec["files"]
    )


def step_cec() -> None:
    for name, url, sha, size, target in (
        ("cec_political", CEC_POLITICAL_URL, tp.CEC_POLITICAL_SHA256, tp.CEC_POLITICAL_BYTES,
         tp.POLITICAL),
        ("cec_ecoregions_l3", CEC_ECOREGIONS_URL, tp.CEC_ECOREGIONS_SHA256,
         tp.CEC_ECOREGIONS_BYTES, tp.ECOREGIONS),
    ):  # fmt: skip
        dest = tp.SOURCES / f"{name}.zip"
        tp.pull_file(url, dest, sha, DRIVE, http_open, log, expected_size=size,
                     extra={"dispatch": DISPATCH, "rulings": ["D113"]})  # fmt: skip
        record = tp.SOURCES / f"{name}.extract.json"
        if _extract_done(record) and target.is_file():
            log(f"{name}: already extracted; skipped")
            continue
        rec = zx.extract_beside_target(dest, target, should_stop=should_stop)
        rec["zip_sha256"] = sha
        record.write_text(json.dumps(rec, indent=2) + "\n")
        log(f"{name}: {len(rec['files'])} files extracted under {rec['root']}; "
            f"target member {rec['target_member']}")  # fmt: skip


def step_nalcms() -> None:
    out = tp.NALCMS_TIF.parent
    smalls = [out / m.rsplit("/", 1)[1] for m in NALCMS_SMALL_MEMBERS]
    if all(p.is_file() for p in smalls) and pq.already_verified(
        tp.NALCMS_TIF, tp.NALCMS_TIF_SHA256
    ):
        log("nalcms: already here, GeoTIFF sha256 matches; skipped")
        return
    reason = should_stop(tp.NALCMS_TIF_BYTES)
    if reason:
        raise pq.QueueStop(f"before nalcms: {reason}")

    def work():
        headers = http_headers(NALCMS_URL)
        reader = http_range_reader(NALCMS_URL)
        records = []
        for member in (*NALCMS_SMALL_MEMBERS, NALCMS_TIF_MEMBER):
            records.append(extract_zip_member(reader, headers["content_length"], member,
                                              out / member.rsplit("/", 1)[1]))  # fmt: skip
        return headers, records

    requested_at = datetime.now(UTC).isoformat(timespec="seconds")
    headers, records = tp.retrying(work, "nalcms", log)
    tif = records[-1]
    if tif["sha256"] != tp.NALCMS_TIF_SHA256:
        tp.NALCMS_TIF.rename(tp.NALCMS_TIF.with_name(tp.NALCMS_TIF.name + ".mismatch"))
        raise pq.ChecksumMismatch(f"nalcms GeoTIFF sha256 {tif['sha256']}, on file "
                                  f"{tp.NALCMS_TIF_SHA256}")  # fmt: skip
    body = {
        "source": NALCMS_URL,
        "dataset": "CEC NA Environmental Atlas, Land Cover 2020 30m (NALCMS), Ed. 2.0",
        "licence": "CC BY 4.0 (metadata, Use limitations)",
        "account": "anonymous",
        "requested_at": requested_at,
        "http": headers,
        "members": records,
        "expected_tif_sha256": tp.NALCMS_TIF_SHA256,
        "tif_sha256_ok": True,
        "dispatch": DISPATCH,
        "rulings": ["D112"],
    }
    (tp.SOURCES / "nalcms.request.json").write_text(json.dumps(body, indent=2) + "\n")
    log(f"nalcms: verified, GeoTIFF {tif['file_size']} B, CRC {tif['crc32']}, sha256 matches")


def step_treemap() -> None:
    dest = tp.TREEMAP_DIR / "RDS-2026-0038.zip"
    tp.pull_file(tp.TREEMAP_URL, dest, tp.TREEMAP_ZIP_SHA256, DRIVE, http_open, log,
                 extra={"catalogue": "https://www.fs.usda.gov/rds/archive/catalog/RDS-2026-0038",
                        "dispatch": DISPATCH, "rulings": ["D84"]})  # fmt: skip
    record = tp.TREEMAP_DIR / "RDS-2026-0038.extract.json"
    vat = tp.TREEMAP_DIR / "TreeMap2023_CONUS.tif.vat.dbf"
    if _extract_done(record) and pq.already_verified(vat, tp.TREEMAP_VAT_SHA256):
        log("treemap: already extracted; skipped")
        return
    rec = zx.extract_named(dest, tp.TREEMAP_MEMBERS, tp.TREEMAP_DIR, should_stop=should_stop)
    got = {f["path"].rsplit("/", 1)[1]: f["sha256"] for f in rec["files"]}
    if got["TreeMap2023_CONUS.tif.vat.dbf"] != tp.TREEMAP_VAT_SHA256:
        vat.rename(vat.with_name(vat.name + ".mismatch"))
        raise pq.ChecksumMismatch(f"TreeMap .vat.dbf sha256 {got[vat.name]}, on file "
                                  f"{tp.TREEMAP_VAT_SHA256}")  # fmt: skip
    rec["zip_sha256"] = tp.TREEMAP_ZIP_SHA256
    rec["vat_sha256_ok"] = True
    record.write_text(json.dumps(rec, indent=2) + "\n")
    log(f"treemap: extracted {rec['picked']}; .vat.dbf sha256 matches")


def step_scanfi() -> None:
    whole, requests = tp.T6B / "scanfi_whole", tp.T6B / "requests"
    for layer in SCANFI_LAYERS:
        reason = should_stop(0)
        if reason:
            raise pq.QueueStop(f"before SCANFI {layer}: {reason}")
        # The dispatch: "a partial file is re-fetched, never trusted", so no resume from here.
        (whole / f"{layer}.tif.partial").unlink(missing_ok=True)
        # The queue's floor (20 GiB) is above the script's --reserve-gb 8, so it is the reserve.
        out = download_layers([layer], lambda c: scanfi_url(c, 2025), whole, requests,
                              reserve=pq.MIN_FREE, log=log)  # fmt: skip
        if out["stopped"]:
            raise pq.QueueStop(f"SCANFI {out['stopped']}")
        request = requests / f"scanfi_whole_{layer}.request.json"
        tp.check_scanfi(layer, whole / f"{layer}.tif", request,
                        lambda _p, r=request: json.loads(r.read_text())["sha256"])  # fmt: skip
        sha = json.loads(request.read_text())["sha256"]
        on_file = "matches the one on file" if layer in tp.SCANFI_SHA256 else "none on file"
        log(f"SCANFI {layer}: {'already here' if out['already'] else 'verified'}, sha256 {sha} "
            f"({on_file})")  # fmt: skip


STEPS = {"cec": step_cec, "nalcms": step_nalcms, "treemap": step_treemap, "scanfi": step_scanfi}


def main(argv: list[str]) -> int:
    if not DRIVE.is_dir():
        log(f"STOP: {DRIVE} is not mounted")
        return 2
    names = argv or list(STEPS)
    log(f"Part A start: steps {names}")
    code = tp.run([(n, STEPS[n]) for n in names], log)
    log(f"Part A end: exit {code}")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

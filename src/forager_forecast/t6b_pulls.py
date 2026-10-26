"""Part A of the pulls queue: T6b's sources, one at a time (dispatch 2026-10-26-pulls).

Order: the two CEC zips, each extracted at once to where scripts/t6b_run.py:81-88 reads it; NALCMS
2020 (its GeoTIFF streamed out of the remote zip, as scripts/t6b_fetch_sources.py does); TreeMap
2023 with its ``.tif`` and ``.vat.dbf`` extracted; then SCANFI v2 2025's eleven layers.

Every file is checked against what is on file for it, read from the committed records cited beside
each constant, and a mismatch stops the queue. Each pull leaves a request record beside its file
(``<file stem>.request.json``), to be copied to docs/pulls/ as the earlier pulls were.
"""

import json
import time
import traceback
from pathlib import Path

from forager_forecast import pulls_queue as pq
from forager_forecast.drive import DRIVE
from forager_forecast.pulls_queue import QueueStop

# Where scripts/t6b_run.py:79-90 reads each source (a test holds the two equal).
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
NALCMS_TIF = SOURCES / "nalcms/NA_NALCMS_landcover_2020v2_30m.tif"
TREEMAP_DIR = DRIVE / "t5" / "treemap2023"

# docs/pulls/t6b-cec-political-boundaries-2021.request.json:10 and :8.
CEC_POLITICAL_SHA256 = "29f3aec70604ed5be9e18c22e2d504da883fedd6d81aff27156456b4899a0c28"
CEC_POLITICAL_BYTES = 184_774_593
# docs/pulls/t6b-cec-terrestrial-ecoregions-l3.request.json:10 and :8.
CEC_ECOREGIONS_SHA256 = "a99b4967e37b309651dfe117435573542d31576dafd779826f80874e015b3338"
CEC_ECOREGIONS_BYTES = 35_236_046
# docs/pulls/t6b-nalcms-2020-30m.request.json, the GeoTIFF member.
NALCMS_TIF_SHA256 = "0d6b497ac21d15b73a01b2d0d95f24bd895612719ca483a99b17897fa93671b7"
NALCMS_TIF_BYTES = 3_363_872_655
# docs/audits/2026-10-25-t6b-rebuild-check/report.md, re-fetch list (catalogue RDS-2026-0038).
TREEMAP_URL = "https://usfs-public.box.com/shared/static/xlaazfhic3ugd1yetoxcicjgtl2t3mry.zip"
# docs/pulls/t5-treemap2023-strip.request.json "zip_sha256", the catalogue's own.
TREEMAP_ZIP_SHA256 = "348264eb608cd55cf49cacec0fa354d03e3f6963d7895582502315629e66abb7"
# docs/pulls/t5-treemap2023-strip-d88.request.json "attribute_table_sha256".
TREEMAP_VAT_SHA256 = "3f0208e01107c7f44abf4afcda6bcef4d22420c7845b4908fdc1c95e892e77d3"
TREEMAP_MEMBERS = ["TreeMap2023_CONUS.tif", "TreeMap2023_CONUS.tif.vat.dbf"]
# docs/audits/2026-10-25-t6b-rebuild-check/manifest_read.out.txt: the five layers whose whole-file
# sha256 the old manifest kept. The other six have none; the download's size check is all they get.
SCANFI_SHA256: dict[str, str] = {
    "otherConiferous": "164e925087b1b18710998793feff9b40eb54d1d75e22f48e7c30b6ea334a61fe",
    "ponderosaPine": "1d5d289e175c9bec6bbe5f88e45370c421ea752b2fbae9d5a6295a5b6e294b5c",
    "tamarack": "dfcfc8ad751b0621b646afde00c3c4729cc0dd22646b3f297487926b13db061e",
    "whiteRedPine": "cc5598a63b28ce7d3fa9840293f706680d0516f3e0147b1261ee621ff915f50b",
    "att_closure": "84e7490d97cf72d22949843ffb7935f4fa4a453da44901f4ce88b67d021d1a94",
}
RETRY_DELAYS = (60, 300, 900)


def write_record(dest: Path, record: dict) -> Path:
    dest = Path(dest)
    path = dest.with_name(dest.name.split(".")[0] + ".request.json")
    path.write_text(json.dumps(record, indent=2) + "\n")
    return path


def retrying(work, label: str, log, sleep=None, delays=RETRY_DELAYS):
    """``work()``, retried after each delay on a network error (OSError); then a queue stop."""
    sleep = sleep or time.sleep
    for n in range(len(delays) + 1):
        try:
            return work()
        except QueueStop:
            raise
        except OSError as err:
            log(f"{label}: attempt {n + 1} failed: {err!r}")
            if n == len(delays):
                raise QueueStop(f"{label}: network errors after {n + 1} attempts: {err!r}") from err
            sleep(delays[n])


def pull_file(
    url: str,
    dest: Path,
    sha256: str,
    root: Path,
    opener,
    log,
    expected_size=None,
    sleep=None,
    free_bytes=None,
    retry_delays=RETRY_DELAYS,
    extra=None,
) -> dict | None:
    """One whole file: skipped if already verified, else fetched with retries and recorded."""
    dest = Path(dest)
    if pq.already_verified(dest, sha256):
        log(f"{dest.name}: already here, sha256 matches; skipped")
        return None
    sleep = sleep or time.sleep

    def should_stop(still):
        return pq.stop_reason(root, still, free_bytes=free_bytes)

    reason = should_stop(expected_size or 0)
    if reason:
        raise QueueStop(f"before {dest.name}: {reason}")
    record = retrying(
        lambda: pq.fetch_verified(
            url, dest, sha256, opener, should_stop=should_stop, expected_size=expected_size
        ),
        dest.name, log, sleep=sleep, delays=retry_delays,
    )  # fmt: skip
    record.update(extra or {})
    write_record(dest, record)
    log(f"{dest.name}: verified, {record['bytes']} B, sha256 {record['sha256']}")
    return record


def check_scanfi(layer: str, path: Path, request: Path, sha256_of) -> None:
    """A layer with a sha256 on file must match it; a mismatch is set aside and stops the queue."""
    want = SCANFI_SHA256.get(layer)
    if want is None:
        return
    got = sha256_of(path)
    if got != want:
        path.rename(path.with_name(path.name + ".mismatch"))
        request.rename(request.with_name(request.name + ".mismatch"))
        raise pq.ChecksumMismatch(f"SCANFI {layer}: sha256 {got}, on file {want}")


def run(steps, log) -> int:
    """Each step in order; 0 when all finish, 2 when the queue stopped itself, 1 on an error."""
    for name, step in steps:
        log(f"step {name}: start")
        try:
            step()
        except QueueStop as err:
            log(f"STOP in step {name}: {err}")
            return 2
        except Exception as err:  # noqa: BLE001  logged with its traceback's end, then the queue stops
            tail = traceback.format_exc().strip().splitlines()[-3:]
            log(f"ERROR in step {name}: {type(err).__name__}: {err} | {' | '.join(tail)}")
            return 1
        log(f"step {name}: done")
    return 0

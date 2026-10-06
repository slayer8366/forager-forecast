"""GBIF occurrence download requests: the T1 predicate, the DWCA request, and its submission.

SPEC.md, Constraints: "Bulk record pulls go through GBIF downloads, which give a citable DOI."
New downloads are requested in Darwin Core Archive format through request_template (D45, D67):
SIMPLE_CSV carries neither informationWithheld nor acceptedTaxonKey, which the obscured step and
D27's key need. The SIMPLE_CSV request that fetched T1's provisional download 0005709 on 2026-09-19
(T1 credentialed run report) is retired; that download is read only by the code kept as its
evidence (records/t1_simple_csv.py, D67).

The predicate in gbif/t1_fungi_two_boxes_2015_2025.json is T1's dispatch "Verify first" item 1 as
a GBIF predicate: kingdom Fungi (backbone key 5), human observations, years 2015 to 2025, records
with coordinates, inside the two T1 boxes. D26's download keeps those filters and replaces the boxes
with the United States and Canada (D47) by GBIF's GADM country tag, else GBIF's country field where
a record has no tag (D71, D72): d26_predicate below, passed to request_template.

Waiting for and fetching a finished download: download_status and fetch_download, which need no
credentials, since a finished download is public at its key.

Requesting a download needs a GBIF account. The request endpoint answered 403 without credentials
and 401 with wrong ones on 2026-09-18. This module reads GBIF_USER, GBIF_PWD and GBIF_EMAIL from
the environment and refuses, naming what is missing, rather than trying anyway.
"""

import base64
import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from forager_forecast.t1_design import BOXES, FIRST_YEAR, FUNGI_KINGDOM_KEY, LAST_YEAR

PREDICATE_PATH = Path(__file__).parent / "gbif" / "t1_fungi_two_boxes_2015_2025.json"
DOWNLOAD_REQUEST_URL = "https://api.gbif.org/v1/occurrence/download/request"
DOWNLOAD_STATUS_URL = "https://api.gbif.org/v1/occurrence/download/{key}"
DOWNLOAD_FILE_URL = "https://api.gbif.org/v1/occurrence/download/request/{key}.zip"

# D47, D71, D72. GADM_LEVEL_0_GID is the download key of the search parameter gadmLevel0Gid
# (https://techdocs.gbif.org/openapi/occurrence.json, read 2026-10-06), as GBIF's own converter
# /v1/occurrence/download/request/predicate returned it for gadmLevel0Gid=USA&gadmLevel0Gid=CAN.
# GADM codes are ISO 3166-1 alpha-3, the country field's are alpha-2.
D26_GADM_COUNTRIES = ("USA", "CAN")
D26_COUNTRY_CODES = ("US", "CA")

# Carried over from T2's records/gbif_download.py under D42 and D45, with request_template below.
# GBIF Backbone Taxonomy. TAXON_KEY 5 is Fungi in this checklist
# (https://api.gbif.org/v1/species/5 -> "Fungi", rank KINGDOM, opened 2026-09-18). Named
# explicitly because the API-downloads documentation's examples carry a checklistKey, and the one
# they carry is the Catalogue of Life, in which key 5 means something else.
GBIF_BACKBONE_CHECKLIST_KEY = "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"

USER_VARIABLE = "GBIF_USER"
PASSWORD_VARIABLE = "GBIF_PWD"
EMAIL_VARIABLE = "GBIF_EMAIL"


class MissingGbifCredentials(RuntimeError):
    """One or more of GBIF_USER, GBIF_PWD, GBIF_EMAIL is not set."""


@dataclass(frozen=True)
class GbifCredentials:
    user: str
    password: str
    email: str


def credentials_from_env(env: Mapping[str, str]) -> GbifCredentials:
    """Read the three variables, or raise naming every one that is missing or empty."""
    missing = [
        name
        for name in (USER_VARIABLE, PASSWORD_VARIABLE, EMAIL_VARIABLE)
        if not env.get(name, "").strip()
    ]
    if missing:
        raise MissingGbifCredentials(
            "GBIF download requests need "
            + ", ".join((USER_VARIABLE, PASSWORD_VARIABLE, EMAIL_VARIABLE))
            + "; not set: "
            + ", ".join(missing)
        )
    return GbifCredentials(
        user=env[USER_VARIABLE].strip(),
        password=env[PASSWORD_VARIABLE].strip(),
        email=env[EMAIL_VARIABLE].strip(),
    )


def load_t1_predicate() -> dict:
    with PREDICATE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def expected_t1_predicate() -> dict:
    """The predicate rebuilt from t1_design, so a test can hold the JSON file to the dispatch."""
    return {
        "type": "and",
        "predicates": [
            {"type": "equals", "key": "TAXON_KEY", "value": str(FUNGI_KINGDOM_KEY)},
            {"type": "equals", "key": "BASIS_OF_RECORD", "value": "HUMAN_OBSERVATION"},
            {"type": "greaterThanOrEquals", "key": "YEAR", "value": str(FIRST_YEAR)},
            {"type": "lessThanOrEquals", "key": "YEAR", "value": str(LAST_YEAR)},
            {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
            {
                "type": "or",
                "predicates": [{"type": "within", "geometry": box.wkt_polygon()} for box in BOXES],
            },
        ],
    }


def d26_predicate() -> dict:
    """D26's area: the T1 template's five filters, and the US and Canada in place of the boxes.

    A record is in when its GADM country tag is USA or CAN, or when it has no GADM tag and its
    country field is US or CA (D72). A record tagged as another country stays out. No CONTINENT
    (D26) and no licence filter (D61). On GBIF's predicate search at 06:49 UTC on 2026-10-06 this
    counted 2,493,578 records, and every record in both T1 boxes
    (docs/audits/2026-10-06-d26-verify/combined.json).
    """
    t1_filters = expected_t1_predicate()["predicates"][:5]
    area = {
        "type": "or",
        "predicates": [
            {"type": "in", "key": "GADM_LEVEL_0_GID", "values": list(D26_GADM_COUNTRIES)},
            {
                "type": "and",
                "predicates": [
                    {"type": "isNull", "parameter": "GADM_LEVEL_0_GID"},
                    {"type": "in", "key": "COUNTRY", "values": list(D26_COUNTRY_CODES)},
                ],
            },
        ],
    }
    return {"type": "and", "predicates": [*t1_filters, area]}


def request_template(predicate: dict[str, Any]) -> dict[str, Any]:
    """The request body without the fields that belong to a person: no email, no notification.

    Carried over from T2 under D42 and D45. T2's took no argument and filled in its own continent
    predicate, which D26 forbids; the predicate is now the caller's, so D26's geometry predicate is
    passed in. Why DWCA and not SIMPLE_CSV, from T2's module docstring: the SIMPLE_CSV column list
    on https://techdocs.gbif.org/en/data-use/download-formats (opened 2026-09-18) has neither
    informationWithheld nor dataGeneralizations, and informationWithheld is the field that marks a
    user-obscured iNaturalist record on GBIF. The DWCA occurrence.txt carries both.
    """
    return {
        "format": "DWCA",
        "checklistKey": GBIF_BACKBONE_CHECKLIST_KEY,
        "predicate": predicate,
    }


def submit_download_request(
    credentials: GbifCredentials,
    predicate: dict,
    url: str = DOWNLOAD_REQUEST_URL,
    opener: Callable = urlopen,
) -> str:
    """POST the DWCA request with HTTP basic auth and return GBIF's download key.

    The body is request_template's with the fields that belong to a person added (D67). This
    function first ran against the real endpoint on 2026-09-19 UTC, returning key
    0005709-260916113435855 (T1 credentialed run report); it then sent the retired SIMPLE_CSV body,
    and it has not run against GBIF since this change.
    """
    body_fields = {
        **request_template(predicate),
        "creator": credentials.user,
        "notificationAddresses": [credentials.email],
        "sendNotification": True,
    }
    body = json.dumps(body_fields).encode("utf-8")
    token = base64.b64encode(f"{credentials.user}:{credentials.password}".encode()).decode()
    request = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Basic {token}",
        },
    )
    with opener(request, timeout=60) as response:
        status = getattr(response, "status", None)
        key = response.read().decode("utf-8").strip()
    if status not in (200, 201) or not key:
        raise RuntimeError(f"download request answered HTTP {status} with body {key!r}")
    return key


def download_status(key: str, opener: Callable = urlopen) -> dict[str, Any]:
    """GBIF's record of one download: status, size, totalRecords, doi, eraseAfter. No login."""
    request = Request(
        DOWNLOAD_STATUS_URL.format(key=key), method="GET", headers={"Accept": "application/json"}
    )
    with opener(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_download(
    key: str,
    directory: Path,
    expected_size: int,
    opener: Callable = urlopen,
    chunk_bytes: int = 1 << 20,
) -> dict[str, Any]:
    """Fetch a finished download's zip once, into directory, and return its size and sha256.

    Refuses to overwrite an existing file, so a second fetch is an error, not a silent redo. GBIF
    publishes no checksum for a download, so the check is the byte size against GBIF's record;
    the sha256 is this machine's own. A size that disagrees removes the partial file and raises.
    """
    target = Path(directory) / f"{key}.zip"
    if target.exists():
        raise FileExistsError(f"{target} exists; a download is fetched once")
    partial = target.with_name(target.name + ".part")
    # Created here, before the request, so the cleanup below only ever removes a file this call
    # made. A partial file left by an earlier run is refused and kept (D26 review, finding 3).
    try:
        out = partial.open("xb")
    except FileExistsError as error:
        raise FileExistsError(
            f"{partial} exists; left by an earlier fetch, so it is not removed here"
        ) from error
    digest = hashlib.sha256()
    size = 0
    request = Request(DOWNLOAD_FILE_URL.format(key=key), method="GET")
    try:
        with out, opener(request, timeout=600) as response:
            while chunk := response.read(chunk_bytes):
                out.write(chunk)
                digest.update(chunk)
                size += len(chunk)
        if size != expected_size:
            raise RuntimeError(f"fetched {size} bytes, GBIF's record says {expected_size}")
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    partial.rename(target)
    return {"path": str(target), "size_bytes": size, "sha256": digest.hexdigest()}

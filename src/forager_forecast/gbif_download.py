"""The GBIF occurrence download T1 needs, prepared and not yet requested.

SPEC.md, Constraints: "Bulk record pulls go through GBIF downloads, which give a citable DOI."
The predicate in gbif/t1_fungi_two_boxes_2015_2025.json is the dispatch's "Verify first" item 1
as a GBIF predicate: kingdom Fungi (backbone key 5), human observations, years 2015 to 2025,
records with coordinates, inside the two T1 boxes. On 2026-09-18 the same predicate posted to
https://api.gbif.org/v1/occurrence/search/predicate with limit 0 counted 1,195,034 records
(T1 completion report).

Requesting a download needs a GBIF account. The request endpoint answered 403 without
credentials and 401 with wrong ones on 2026-09-18. This module reads GBIF_USER, GBIF_PWD and
GBIF_EMAIL from the environment and refuses, naming what is missing, rather than trying anyway.
"""

import base64
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from forager_forecast.t1_design import BOXES, FIRST_YEAR, FUNGI_KINGDOM_KEY, LAST_YEAR

PREDICATE_PATH = Path(__file__).parent / "gbif" / "t1_fungi_two_boxes_2015_2025.json"
DOWNLOAD_REQUEST_URL = "https://api.gbif.org/v1/occurrence/download/request"
DOWNLOAD_FORMAT = "SIMPLE_CSV"

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


def build_download_request(credentials: GbifCredentials, predicate: dict) -> dict:
    """The JSON body GBIF's download request endpoint takes."""
    return {
        "creator": credentials.user,
        "notificationAddresses": [credentials.email],
        "sendNotification": True,
        "format": DOWNLOAD_FORMAT,
        "predicate": predicate,
    }


def submit_download_request(
    credentials: GbifCredentials,
    predicate: dict,
    url: str = DOWNLOAD_REQUEST_URL,
    opener: Callable = urlopen,
) -> str:
    """POST the request with HTTP basic auth and return GBIF's download key. Not run in T1: no
    credentials existed on the machine (T1 completion report, "Owner items")."""
    body = json.dumps(build_download_request(credentials, predicate)).encode("utf-8")
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

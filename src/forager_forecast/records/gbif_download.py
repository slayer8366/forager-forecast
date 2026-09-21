"""The GBIF occurrence download that T2 shares with T1.

Prepared, not run. A download request needs a GBIF.org account, authenticated with the username
(not the email) and password, and returns a key that resolves to a DOI once the download is ready
(https://techdocs.gbif.org/en/data-use/api-downloads, opened 2026-09-18). This machine has no
such credentials (T2 completion report, "Owner items"), so this module builds the exact request
and a test holds it still; nothing here opens a connection.

Why format DWCA and not SIMPLE_CSV: the SIMPLE_CSV column list on
https://techdocs.gbif.org/en/data-use/download-formats (opened 2026-09-18) has
coordinateUncertaintyInMeters and identifiedBy but neither informationWithheld nor
dataGeneralizations, and informationWithheld is the field that marks a user-obscured
iNaturalist record on GBIF (T2 report, verify-first item 1). The DWCA occurrence.txt carries all
four.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

DOWNLOAD_REQUEST_URL = "https://api.gbif.org/v1/occurrence/download/request"

# GBIF Backbone Taxonomy. TAXON_KEY 5 is Fungi in this checklist
# (https://api.gbif.org/v1/species/5 -> "Fungi", rank KINGDOM, opened 2026-09-18). Named
# explicitly because the API-downloads documentation's examples carry a checklistKey, and the one
# they carry is the Catalogue of Life, in which key 5 means something else.
GBIF_BACKBONE_CHECKLIST_KEY = "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"
FUNGI_TAXON_KEY = 5

FIRST_YEAR = 2015
LAST_YEAR = 2025

# Environment variables read for credentials. The names follow rgbif and pygbif, so an owner who
# has used either already has them set. Nothing else is read: no ~/.netrc, no config file.
ENV_USER = "GBIF_USER"
ENV_PASSWORD = "GBIF_PWD"
ENV_EMAIL = "GBIF_EMAIL"


def predicate() -> dict[str, Any]:
    """Kingdom Fungi, human observations, 2015 to 2025, with coordinates, North America.

    The five terms of the dispatch, and nothing added. Key names are in the upper-case form the
    download API requires (API-downloads page, "Occurrence search parameters"). No credential-free
    endpoint validates a predicate (GET /occurrence/download/request/predicate returned 404 on
    2026-09-18), so the names rest on that page until a submission accepts them.
    """
    return {
        "type": "and",
        "predicates": [
            {"type": "equals", "key": "TAXON_KEY", "value": str(FUNGI_TAXON_KEY)},
            {"type": "equals", "key": "BASIS_OF_RECORD", "value": "HUMAN_OBSERVATION"},
            {"type": "greaterThanOrEquals", "key": "YEAR", "value": str(FIRST_YEAR)},
            {"type": "lessThanOrEquals", "key": "YEAR", "value": str(LAST_YEAR)},
            {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
            {"type": "equals", "key": "CONTINENT", "value": "NORTH_AMERICA"},
        ],
    }


def request_template() -> dict[str, Any]:
    """The request body without the fields that belong to a person: no email, no notification."""
    return {
        "format": "DWCA",
        "checklistKey": GBIF_BACKBONE_CHECKLIST_KEY,
        "predicate": predicate(),
    }


def request_template_json() -> str:
    """The committed form of the template, docs/pulls/gbif-fungi-north-america-2015-2025.json."""
    return json.dumps(request_template(), indent=2) + "\n"


@dataclass(frozen=True)
class Credentials:
    user: str
    password: str
    email: str


class MissingCredentials(LookupError):
    """Raised with the names of every variable that is unset. There is no fallback."""

    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__(f"GBIF credentials not set: {', '.join(missing)}")


def credentials_from_env(environ: Mapping[str, str]) -> Credentials:
    missing = [name for name in (ENV_USER, ENV_PASSWORD, ENV_EMAIL) if not environ.get(name)]
    if missing:
        raise MissingCredentials(missing)
    return Credentials(environ[ENV_USER], environ[ENV_PASSWORD], environ[ENV_EMAIL])


def request_body(credentials: Credentials) -> dict[str, Any]:
    """The template plus the notification address, as the download API wants it."""
    body = request_template()
    body["notificationAddresses"] = [credentials.email]
    body["sendNotification"] = True
    return body


def curl_argv(credentials: Credentials, body_path: str) -> list[str]:
    """The submission as the API-downloads page shows it, with the body read from a file.

    The password sits in the argument list, as in GBIF's own example. Run it from a shell whose
    history is off, or replace "--user" with "--netrc" and a ~/.netrc entry for api.gbif.org.
    """
    return [
        "curl",
        "--include",
        "--user",
        f"{credentials.user}:{credentials.password}",
        "--header",
        "Content-Type: application/json",
        "--data",
        f"@{body_path}",
        DOWNLOAD_REQUEST_URL,
    ]

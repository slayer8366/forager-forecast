"""The shared GBIF download request, held still.

The committed file docs/pulls/gbif-fungi-north-america-2015-2025.json is what the owner submits.
These tests keep it equal to the code that describes it, and keep the predicate at the dispatch's
five terms. Nothing here reaches the network.
"""

import json
from pathlib import Path

import pytest

from forager_forecast.records import gbif_download as g

REPO = Path(__file__).resolve().parents[1]
PREDICATE_FILE = REPO / "docs" / "pulls" / "gbif-fungi-north-america-2015-2025.json"


def test_committed_request_file_matches_the_code():
    assert PREDICATE_FILE.read_text(encoding="utf-8") == g.request_template_json()


def test_predicate_is_exactly_the_dispatch_terms():
    clauses = {(p["key"], p["type"], p["value"]) for p in g.predicate()["predicates"]}
    assert clauses == {
        ("TAXON_KEY", "equals", "5"),
        ("BASIS_OF_RECORD", "equals", "HUMAN_OBSERVATION"),
        ("YEAR", "greaterThanOrEquals", "2015"),
        ("YEAR", "lessThanOrEquals", "2025"),
        ("HAS_COORDINATE", "equals", "true"),
        ("CONTINENT", "equals", "NORTH_AMERICA"),
    }
    assert g.predicate()["type"] == "and"


def test_format_is_dwca_because_simple_csv_lacks_information_withheld():
    template = json.loads(g.request_template_json())
    assert template["format"] == "DWCA"
    assert template["checklistKey"] == "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"


def test_missing_credentials_name_every_unset_variable():
    with pytest.raises(g.MissingCredentials) as info:
        g.credentials_from_env({"GBIF_USER": "someone"})
    assert info.value.missing == ["GBIF_PWD", "GBIF_EMAIL"]


def test_empty_variable_counts_as_unset():
    with pytest.raises(g.MissingCredentials) as info:
        g.credentials_from_env({"GBIF_USER": "someone", "GBIF_PWD": "", "GBIF_EMAIL": "a@b.c"})
    assert info.value.missing == ["GBIF_PWD"]


def test_request_body_adds_only_the_notification_fields():
    creds = g.credentials_from_env(
        {"GBIF_USER": "someone", "GBIF_PWD": "secret", "GBIF_EMAIL": "someone@example.org"}
    )
    body = g.request_body(creds)
    assert body["notificationAddresses"] == ["someone@example.org"]
    assert body["sendNotification"] is True
    assert body["predicate"] == g.predicate()
    assert set(body) == {
        "format",
        "checklistKey",
        "predicate",
        "notificationAddresses",
        "sendNotification",
    }


def test_curl_argv_posts_the_body_file_with_basic_auth():
    creds = g.Credentials("someone", "secret", "someone@example.org")
    argv = g.curl_argv(creds, "/tmp/query.json")
    assert argv[-1] == "https://api.gbif.org/v1/occurrence/download/request"
    assert argv[argv.index("--user") + 1] == "someone:secret"
    assert argv[argv.index("--data") + 1] == "@/tmp/query.json"
    assert "Content-Type: application/json" in argv

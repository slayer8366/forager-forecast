import json

import pytest

from forager_forecast.records.gbif_download import (
    DOWNLOAD_REQUEST_URL,
    PREDICATE_PATH,
    GbifCredentials,
    MissingGbifCredentials,
    build_download_request,
    credentials_from_env,
    expected_t1_predicate,
    load_t1_predicate,
    request_template,
    submit_download_request,
)


def test_the_saved_predicate_is_the_dispatch_in_gbif_terms():
    assert PREDICATE_PATH.name == "t1_fungi_two_boxes_2015_2025.json"
    assert load_t1_predicate() == expected_t1_predicate()


def test_the_boxes_in_the_predicate_are_counter_clockwise_and_closed():
    boxes = load_t1_predicate()["predicates"][-1]["predicates"]
    assert [b["geometry"] for b in boxes] == [
        "POLYGON((-125.0 42.0,-121.0 42.0,-121.0 49.5,-125.0 49.5,-125.0 42.0))",
        "POLYGON((-84.0 38.0,-70.0 38.0,-70.0 46.0,-84.0 46.0,-84.0 38.0))",
    ]


def test_missing_credentials_are_named_not_guessed():
    with pytest.raises(MissingGbifCredentials) as excinfo:
        credentials_from_env({})
    message = str(excinfo.value)
    for name in ("GBIF_USER", "GBIF_PWD", "GBIF_EMAIL"):
        assert name in message
    with pytest.raises(MissingGbifCredentials, match="not set: GBIF_EMAIL$"):
        credentials_from_env({"GBIF_USER": "someone", "GBIF_PWD": "secret", "GBIF_EMAIL": " "})


def test_credentials_are_read_from_the_three_variables():
    creds = credentials_from_env(
        {"GBIF_USER": "someone", "GBIF_PWD": "secret", "GBIF_EMAIL": "someone@example.org"}
    )
    assert creds == GbifCredentials("someone", "secret", "someone@example.org")


def test_download_request_body():
    creds = GbifCredentials("someone", "secret", "someone@example.org")
    body = build_download_request(creds, load_t1_predicate())
    assert body["creator"] == "someone"
    assert body["notificationAddresses"] == ["someone@example.org"]
    assert body["format"] == "SIMPLE_CSV"
    assert body["predicate"] == load_t1_predicate()


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_submit_posts_basic_auth_json_and_returns_the_key():
    seen = {}

    def opener(request, timeout):
        seen["url"] = request.full_url
        seen["method"] = request.get_method()
        seen["headers"] = dict(request.header_items())
        seen["body"] = json.loads(request.data)
        return FakeResponse(201, b"0012345-250918000000000")

    creds = GbifCredentials("someone", "secret", "someone@example.org")
    key = submit_download_request(creds, load_t1_predicate(), opener=opener)
    assert key == "0012345-250918000000000"
    assert seen["url"] == DOWNLOAD_REQUEST_URL
    assert seen["method"] == "POST"
    assert seen["headers"]["Authorization"] == "Basic c29tZW9uZTpzZWNyZXQ="
    assert seen["headers"]["Content-type"] == "application/json"
    assert seen["body"]["predicate"] == load_t1_predicate()


def test_submit_reports_a_refusal():
    def opener(request, timeout):
        return FakeResponse(403, b"Access is denied")

    creds = GbifCredentials("someone", "secret", "someone@example.org")
    with pytest.raises(RuntimeError, match="HTTP 403"):
        submit_download_request(creds, load_t1_predicate(), opener=opener)


# Carried over from T2's tests/test_records_gbif_download.py under D42 and D45, pointed at the
# unified request_template with a predicate passed in. T2's other six tests covered code not
# carried over and were deleted with it (stage 2b ready report).


def test_format_is_dwca_because_simple_csv_lacks_information_withheld():
    template = request_template(expected_t1_predicate())
    assert template["format"] == "DWCA"
    assert template["checklistKey"] == "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"


def test_request_template_carries_the_callers_predicate_and_nothing_personal():
    predicate = {"type": "equals", "key": "HAS_COORDINATE", "value": "true"}
    template = request_template(predicate)
    assert template["predicate"] == predicate
    assert set(template) == {"format", "checklistKey", "predicate"}

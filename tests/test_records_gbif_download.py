import json

import pytest

from forager_forecast.records import gbif_download as gd
from forager_forecast.records.gbif_download import (
    DOWNLOAD_REQUEST_URL,
    PREDICATE_PATH,
    GbifCredentials,
    MissingGbifCredentials,
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
    # Two of three missing: both are named, in order (stage 2b report; the move review's proposal).
    with pytest.raises(MissingGbifCredentials, match="not set: GBIF_PWD, GBIF_EMAIL$"):
        credentials_from_env({"GBIF_USER": "someone"})


def test_credentials_are_read_from_the_three_variables():
    creds = credentials_from_env(
        {"GBIF_USER": "someone", "GBIF_PWD": "secret", "GBIF_EMAIL": "someone@example.org"}
    )
    assert creds == GbifCredentials("someone", "secret", "someone@example.org")


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
    # D67: new downloads use the DWCA request; the body is request_template's plus the fields
    # that belong to a person. SIMPLE_CSV is retired for new downloads.
    assert seen["body"] == {
        **request_template(load_t1_predicate()),
        "creator": "someone",
        "notificationAddresses": ["someone@example.org"],
        "sendNotification": True,
    }
    assert seen["body"]["format"] == "DWCA"


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


# D26's download: the area by GBIF's GADM country tag, else the country field (D71, D72).

D26_REQUEST = {
    "format": "DWCA",
    "checklistKey": "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c",
    "predicate": {
        "type": "and",
        "predicates": [
            {"type": "equals", "key": "TAXON_KEY", "value": "5"},
            {"type": "equals", "key": "BASIS_OF_RECORD", "value": "HUMAN_OBSERVATION"},
            {"type": "greaterThanOrEquals", "key": "YEAR", "value": "2015"},
            {"type": "lessThanOrEquals", "key": "YEAR", "value": "2025"},
            {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
            {
                "type": "or",
                "predicates": [
                    {"type": "in", "key": "GADM_LEVEL_0_GID", "values": ["USA", "CAN"]},
                    {
                        "type": "and",
                        "predicates": [
                            {"type": "isNull", "parameter": "GADM_LEVEL_0_GID"},
                            {"type": "in", "key": "COUNTRY", "values": ["US", "CA"]},
                        ],
                    },
                ],
            },
        ],
    },
}


def _keys(node):
    """Every "key" and "parameter" named anywhere in a predicate tree."""
    if isinstance(node, dict):
        for name in ("key", "parameter"):
            if name in node:
                yield node[name]
        for value in node.values():
            yield from _keys(value)
    elif isinstance(node, list):
        for value in node:
            yield from _keys(value)


def test_d26_request_is_the_t1_filters_plus_tag_else_country():
    assert request_template(gd.d26_predicate()) == D26_REQUEST


def test_d26_predicate_has_no_continent_and_no_licence_filter():
    keys = set(_keys(gd.d26_predicate()))
    assert "CONTINENT" not in keys, "D26: never select by the continent field"
    assert "LICENSE" not in keys, "D61: records of every licence"
    assert keys == {
        "TAXON_KEY",
        "BASIS_OF_RECORD",
        "YEAR",
        "HAS_COORDINATE",
        "GADM_LEVEL_0_GID",
        "COUNTRY",
    }


def test_d26_predicate_keeps_the_t1_template_filters_unchanged():
    """D26: the content of the predicate does not change; only the area replaces the boxes."""
    t1 = expected_t1_predicate()["predicates"]
    assert gd.d26_predicate()["predicates"][:5] == t1[:5]


class FakeStream:
    def __init__(self, status, chunks):
        self.status = status
        self._chunks = list(chunks)

    def read(self, size=-1):
        return self._chunks.pop(0) if self._chunks else b""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_download_status_reads_gbifs_record_without_credentials():
    seen = {}
    record = {"key": "0000001-261006000000000", "status": "RUNNING", "size": 0}

    def opener(request, timeout):
        seen["url"] = request.full_url
        seen["method"] = request.get_method()
        seen["auth"] = request.get_header("Authorization")
        return FakeStream(200, [json.dumps(record).encode()])

    assert gd.download_status("0000001-261006000000000", opener=opener) == record
    assert seen["url"] == "https://api.gbif.org/v1/occurrence/download/0000001-261006000000000"
    assert seen["method"] == "GET"
    assert seen["auth"] is None


def test_fetch_download_writes_once_and_returns_size_and_sha256(tmp_path):
    import hashlib

    payload = [b"PK\x03\x04 first", b" second", b" third"]
    seen = {}

    def opener(request, timeout):
        seen["url"] = request.full_url
        return FakeStream(200, payload)

    whole = b"".join(payload)
    result = gd.fetch_download("0000001-261006000000000", tmp_path, len(whole), opener=opener)
    target = tmp_path / "0000001-261006000000000.zip"
    assert seen["url"] == (
        "https://api.gbif.org/v1/occurrence/download/request/0000001-261006000000000.zip"
    )
    assert target.read_bytes() == whole
    assert result == {
        "path": str(target),
        "size_bytes": len(whole),
        "sha256": hashlib.sha256(whole).hexdigest(),
    }
    with pytest.raises(FileExistsError):
        gd.fetch_download("0000001-261006000000000", tmp_path, len(whole), opener=opener)


def test_fetch_download_refuses_a_size_that_disagrees_with_gbif(tmp_path):
    def opener(request, timeout):
        return FakeStream(200, [b"short"])

    with pytest.raises(RuntimeError, match="5 bytes, GBIF's record says 9"):
        gd.fetch_download("0000001-261006000000000", tmp_path, 9, opener=opener)
    assert not (tmp_path / "0000001-261006000000000.zip").exists()
    assert not list(tmp_path.iterdir()), "no partial file is left behind"

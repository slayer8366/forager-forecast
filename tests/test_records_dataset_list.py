"""D29: each download's constituent datasets with licence and record count, and by-licence counts.

Read with D48 (the licence that counts is each record's own licence field) and D61. GBIF's public
API is read without credentials, one request at a time; the counts come from the rows themselves.
"""

import json

import pytest

from forager_forecast.records import dataset_list as dl


class FakeResponse:
    def __init__(self, body: dict):
        self.status = 200
        self._body = json.dumps(body).encode("utf-8")

    def read(self, size=-1):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_dataset_metadata_reads_gbifs_public_record_without_credentials():
    seen = []

    def opener(request, timeout):
        seen.append(request)
        return FakeResponse({"key": "k1", "title": "A dataset", "license": "http://x/by/4.0"})

    assert dl.dataset_metadata("k1", opener=opener)["license"] == "http://x/by/4.0"
    (request,) = seen
    assert request.full_url == "https://api.gbif.org/v1/dataset/k1"
    assert request.get_method() == "GET"
    assert request.get_header("Authorization") is None
    assert "forager-forecast" in request.get_header("User-agent")


def test_download_datasets_pages_until_gbif_says_the_end():
    pages = {
        0: {"endOfRecords": False, "results": [{"datasetKey": "a", "numberRecords": 5}]},
        1: {"endOfRecords": True, "results": [{"datasetKey": "b", "numberRecords": 2}]},
    }
    urls = []

    def opener(request, timeout):
        urls.append(request.full_url)
        offset = int(request.full_url.split("offset=")[1].split("&")[0])
        return FakeResponse(pages[offset])

    got = dl.download_datasets("0012112-260928105237408", opener=opener, limit=1)
    assert [r["datasetKey"] for r in got] == ["a", "b"]
    assert urls == [
        "https://api.gbif.org/v1/occurrence/download/0012112-260928105237408/datasets"
        "?offset=0&limit=1",
        "https://api.gbif.org/v1/occurrence/download/0012112-260928105237408/datasets"
        "?offset=1&limit=1",
    ]


def test_tally_counts_every_row_by_dataset_and_by_each_records_own_licence():
    tally = dl.DatasetTally()
    rows = [
        {"datasetKey": "inat", "license": "CC_BY_NC_4_0"},
        {"datasetKey": "inat", "license": "CC_BY_4_0"},
        {"datasetKey": "inat", "license": "CC0_1_0"},
        {"datasetKey": "inat", "license": "CC_BY_NC_4_0"},
        {"datasetKey": "mo", "license": "CC_BY_4_0"},
        {"datasetKey": "", "license": ""},
    ]
    for row in rows:
        tally.add_row(row)
    assert tally.rows == 6
    assert tally.by_dataset() == {"inat": 4, "mo": 1, "(empty)": 1}
    assert tally.by_license() == {"CC_BY_NC_4_0": 2, "CC_BY_4_0": 2, "CC0_1_0": 1, "(empty)": 1}
    assert tally.by_dataset_and_license()["inat"] == {
        "CC_BY_NC_4_0": 2,
        "CC_BY_4_0": 1,
        "CC0_1_0": 1,
    }


def test_rights_file_is_read_as_title_and_rights_pairs_in_order():
    text = (
        "Dataset: Observation.org, Nature data from around the World \n"
        "Rights as supplied: http://creativecommons.org/licenses/by-nc/4.0/legalcode\n"
        "Dataset: \n"
        "Rights as supplied: http://creativecommons.org/licenses/by/4.0/legalcode\n"
    )
    assert dl.parse_rights(text) == [
        (
            "Observation.org, Nature data from around the World",
            "http://creativecommons.org/licenses/by-nc/4.0/legalcode",
        ),
        ("", "http://creativecommons.org/licenses/by/4.0/legalcode"),
    ]


def test_a_rights_file_out_of_step_is_refused():
    with pytest.raises(ValueError, match="line 2"):
        dl.parse_rights("Dataset: A\nDataset: B\n")

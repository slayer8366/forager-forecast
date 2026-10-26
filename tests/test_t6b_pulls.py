"""Part A of the pulls queue: what is on file for each source, skip, retry, record and stop."""

import hashlib
import io
import json
from pathlib import Path

import pytest

from forager_forecast import pulls_queue as pq
from forager_forecast import t6b_pulls as tp

ROOT = Path(__file__).resolve().parent.parent
PULLS = ROOT / "docs" / "pulls"
GIB = 1024**3


def _json(name):
    return json.loads((PULLS / name).read_text())


def test_the_cec_checksums_are_the_ones_on_file():
    pol = _json("t6b-cec-political-boundaries-2021.request.json")
    eco = _json("t6b-cec-terrestrial-ecoregions-l3.request.json")
    assert tp.CEC_POLITICAL_SHA256 == pol["sha256"]
    assert tp.CEC_POLITICAL_BYTES == pol["http"]["content_length"]
    assert tp.CEC_ECOREGIONS_SHA256 == eco["sha256"]
    assert tp.CEC_ECOREGIONS_BYTES == eco["http"]["content_length"]
    # The dispatch's own short forms (Part B item 4: a99b4967...3338).
    assert tp.CEC_ECOREGIONS_SHA256.startswith("a99b4967") and tp.CEC_ECOREGIONS_SHA256.endswith(
        "3338"
    )


def test_the_nalcms_and_treemap_checksums_are_the_ones_on_file():
    tif = _json("t6b-nalcms-2020-30m.request.json")["members"][-1]
    assert tif["file"] == "NA_NALCMS_landcover_2020v2_30m.tif"
    assert (tp.NALCMS_TIF_SHA256, tp.NALCMS_TIF_BYTES) == (tif["sha256"], tif["file_size"])
    assert tp.TREEMAP_ZIP_SHA256 == _json("t5-treemap2023-strip.request.json")["zip_sha256"]
    assert tp.TREEMAP_ZIP_SHA256.startswith("348264eb") and tp.TREEMAP_ZIP_SHA256.endswith("abb7")
    assert (
        tp.TREEMAP_VAT_SHA256
        == _json("t5-treemap2023-strip-d88.request.json")["attribute_table_sha256"]
    )
    assert (
        tp.TREEMAP_URL
        == "https://usfs-public.box.com/shared/static/xlaazfhic3ugd1yetoxcicjgtl2t3mry.zip"
    )


def test_the_scanfi_checksums_are_the_five_on_file():
    out = (ROOT / "docs/audits/2026-10-25-t6b-rebuild-check/manifest_read.out.txt").read_text()
    assert set(tp.SCANFI_SHA256) == {
        "otherConiferous",
        "ponderosaPine",
        "tamarack",
        "whiteRedPine",
        "att_closure",
    }
    for layer, sha in tp.SCANFI_SHA256.items():
        assert f'"group": "{layer}"' in out and f'"sha256": "{sha}"' in out


class Resp(io.BytesIO):
    status = 200
    url = "https://d.example/x.zip"

    def __init__(self, body):
        super().__init__(body)
        self.headers = {"Content-Length": str(len(body)), "Content-Type": "application/zip"}


def test_a_verified_file_is_skipped_without_a_request(tmp_path):
    f = tmp_path / "x.zip"
    f.write_bytes(b"abc")

    def opener(url):
        raise AssertionError("no request expected")

    got = tp.pull_file(
        "https://d.example/x.zip",
        f,
        hashlib.sha256(b"abc").hexdigest(),
        tmp_path,
        opener,
        log=lambda m: None,
        free_bytes=lambda _: 100 * GIB,
    )
    assert got is None


def test_a_pull_is_recorded_beside_its_file(tmp_path):
    body = b"z" * 1000
    rec = tp.pull_file(
        "https://d.example/x.zip",
        tmp_path / "x.zip",
        hashlib.sha256(body).hexdigest(),
        tmp_path,
        lambda u: Resp(body),
        log=lambda m: None,
        free_bytes=lambda _: 100 * GIB,
        extra={"rulings": ["D113"]},
    )
    on_disk = json.loads((tmp_path / "x.request.json").read_text())
    assert on_disk == rec
    assert on_disk["sha256"] == hashlib.sha256(body).hexdigest() and on_disk["rulings"] == ["D113"]


def test_a_network_error_is_retried_then_stops_the_queue(tmp_path):
    body = b"y" * 10
    calls = []

    def flaky(url):
        calls.append(url)
        if len(calls) < 3:
            raise OSError("connection reset")
        return Resp(body)

    slept = []
    tp.pull_file(
        "https://d.example/x.zip",
        tmp_path / "x.zip",
        hashlib.sha256(body).hexdigest(),
        tmp_path,
        flaky,
        log=lambda m: None,
        sleep=slept.append,
        free_bytes=lambda _: 100 * GIB,
        retry_delays=(1, 2),
    )
    assert len(calls) == 3 and slept == [1, 2]

    def down(url):
        raise OSError("name resolution")

    with pytest.raises(pq.QueueStop, match="network"):
        tp.pull_file(
            "https://d.example/y.zip",
            tmp_path / "y.zip",
            "0" * 64,
            tmp_path,
            down,
            log=lambda m: None,
            sleep=lambda s: None,
            free_bytes=lambda _: 100 * GIB,
            retry_delays=(1, 2),
        )


def test_a_mismatch_is_not_retried(tmp_path):
    calls = []

    def opener(url):
        calls.append(url)
        return Resp(b"wrong")

    with pytest.raises(pq.ChecksumMismatch):
        tp.pull_file(
            "https://d.example/x.zip",
            tmp_path / "x.zip",
            "0" * 64,
            tmp_path,
            opener,
            log=lambda m: None,
            sleep=lambda s: None,
            free_bytes=lambda _: 100 * GIB,
        )
    assert len(calls) == 1


def test_low_space_stops_before_any_request(tmp_path):
    def opener(url):
        raise AssertionError("no request expected")

    with pytest.raises(pq.QueueStop, match="free"):
        tp.pull_file(
            "https://d.example/x.zip",
            tmp_path / "x.zip",
            "0" * 64,
            tmp_path,
            opener,
            log=lambda m: None,
            expected_size=2 * GIB,
            free_bytes=lambda _: 21 * GIB,
        )


def test_a_scanfi_layer_off_its_checksum_is_set_aside(tmp_path):
    tif, req = tmp_path / "tamarack.tif", tmp_path / "scanfi_whole_tamarack.request.json"
    tif.write_bytes(b"t")
    req.write_text("{}")
    with pytest.raises(pq.ChecksumMismatch, match="tamarack"):
        tp.check_scanfi("tamarack", tif, req, lambda p: "f" * 64)
    assert not tif.exists() and not req.exists()
    assert (tmp_path / "tamarack.tif.mismatch").exists()
    # A layer with no sha256 on file is left as the download's size check passed it.
    tp.check_scanfi("broadleaf", tmp_path / "broadleaf.tif", req, lambda p: "f" * 64)
    # And a matching one stays.
    tif.write_bytes(b"t")
    tp.check_scanfi("tamarack", tif, req, lambda p: tp.SCANFI_SHA256["tamarack"])
    assert tif.exists()


def test_the_queue_logs_why_it_stopped_and_runs_nothing_after(tmp_path):
    lines, ran = [], []

    def ok():
        ran.append("a")

    def pause():
        raise pq.QueueStop("PAUSE file at x")

    def never():
        ran.append("c")

    assert tp.run([("a", ok), ("b", pause), ("c", never)], lines.append) == 2
    assert ran == ["a"] and any("STOP" in m and "PAUSE" in m for m in lines)
    lines.clear()
    assert tp.run([("a", ok), ("e", lambda: 1 / 0)], lines.append) == 1
    assert any("ERROR" in m and "ZeroDivisionError" in m for m in lines)
    assert tp.run([("a", ok)], lines.append) == 0


def test_the_targets_are_where_the_runner_reads_them():
    import importlib.util

    spec = importlib.util.spec_from_file_location("t6b_run_script", ROOT / "scripts" / "t6b_run.py")
    run = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run)
    assert tp.POLITICAL == run.POLITICAL and tp.ECOREGIONS == run.ECOREGIONS
    assert tp.NALCMS_TIF == run.NALCMS and tp.TREEMAP_DIR == run.TREEMAP
    assert tp.SOURCES == run.SOURCES and tp.T6B == run.T6B


def test_retrying_gives_up_with_a_stop_after_the_last_delay():
    seen, slept = [], []

    def work():
        seen.append(1)
        raise OSError("timed out")

    with pytest.raises(pq.QueueStop, match="nalcms: network errors after 3 attempts"):
        tp.retrying(work, "nalcms", log=lambda m: None, sleep=slept.append, delays=(5, 6))
    assert len(seen) == 3 and slept == [5, 6]
    assert tp.retrying(lambda: 7, "x", log=lambda m: None, sleep=slept.append, delays=(5,)) == 7

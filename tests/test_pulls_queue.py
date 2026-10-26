"""The pulls queue's stops and its whole-file fetch, over in-memory responses (no network)."""

import hashlib
import io

import pytest

from forager_forecast import pulls_queue as pq

GIB = 1024**3


class Response(io.BytesIO):
    def __init__(self, body: bytes, status=200, url="https://data.example/f.zip", headers=None):
        super().__init__(body)
        self.status = status
        self.url = url
        self.headers = {"Content-Length": str(len(body)), "Content-Type": "application/zip"}
        self.headers.update(headers or {})


def opener_for(*responses):
    calls = []
    queue = list(responses)

    def opener(url):
        calls.append(url)
        return queue.pop(0)

    opener.calls = calls
    return opener


def test_a_pause_file_stops_the_queue(tmp_path):
    (tmp_path / "PAUSE").touch()
    assert "PAUSE" in pq.stop_reason(tmp_path, free_bytes=lambda _: 100 * GIB)


def test_under_20_gib_free_after_the_file_stops_the_queue(tmp_path):
    assert pq.stop_reason(tmp_path, 0, free_bytes=lambda _: 25 * GIB) is None
    # 25 GiB free, 6 GiB to come: 19 GiB would be left.
    assert "free" in pq.stop_reason(tmp_path, 6 * GIB, free_bytes=lambda _: 25 * GIB)
    assert pq.MIN_FREE == 20 * GIB


@pytest.mark.parametrize(
    ("status", "url", "ctype", "wall"),
    [
        (200, "https://data.example/f.zip", "application/zip", False),
        (200, "https://dl.boxcloud.example/d/1/abc/download", "application/octet-stream", False),
        (401, "https://data.example/f.nc", "text/plain", True),
        (403, "https://data.example/f.nc", "application/json", True),
        (200, "https://urs.example.gov/oauth/authorize?client_id=x", "application/zip", True),
        (200, "https://data.example/f.zip", "text/html; charset=utf-8", True),
    ],
)
def test_a_login_wall_is_recognised(status, url, ctype, wall):
    assert pq.is_login_wall(status, url, ctype) is wall


def test_a_file_whose_checksum_matches_is_kept_and_its_partial_deleted(tmp_path):
    f = tmp_path / "a.zip"
    f.write_bytes(b"abc")
    (tmp_path / "a.zip.partial").write_bytes(b"ab")
    assert pq.already_verified(f, hashlib.sha256(b"abc").hexdigest())
    assert not (tmp_path / "a.zip.partial").exists()
    assert not pq.already_verified(f, "0" * 64)
    assert not pq.already_verified(tmp_path / "missing.zip", "0" * 64)


def test_a_fetch_writes_the_file_only_when_its_sha256_matches(tmp_path):
    body = b"forest" * 100_000
    dest = tmp_path / "x.zip"
    rec = pq.fetch_verified(
        "https://data.example/x.zip",
        dest,
        hashlib.sha256(body).hexdigest(),
        opener_for(Response(body)),
    )
    assert dest.read_bytes() == body
    assert rec["sha256"] == hashlib.sha256(body).hexdigest() and rec["sha256_ok"] is True
    assert rec["bytes"] == len(body) and rec["file"] == "x.zip"
    assert not (tmp_path / "x.zip.partial").exists()


def test_a_mismatch_is_set_aside_and_stops_the_queue(tmp_path):
    dest = tmp_path / "x.zip"
    with pytest.raises(pq.ChecksumMismatch, match="sha256"):
        pq.fetch_verified("https://data.example/x.zip", dest, "0" * 64, opener_for(Response(b"zz")))
    assert not dest.exists()
    assert (tmp_path / "x.zip.mismatch").read_bytes() == b"zz"


def test_a_stale_partial_is_never_resumed(tmp_path):
    body = b"0123456789" * 1000
    dest = tmp_path / "x.zip"
    (tmp_path / "x.zip.partial").write_bytes(b"garbage")
    opener = opener_for(Response(body))
    pq.fetch_verified("https://d.example/x.zip", dest, hashlib.sha256(body).hexdigest(), opener)
    assert dest.read_bytes() == body


def test_a_login_page_is_refused_and_nothing_is_kept(tmp_path):
    page = Response(b"<html>sign in</html>", headers={"Content-Type": "text/html"})
    with pytest.raises(pq.LoginWall):
        pq.fetch_verified("https://d.example/x.zip", tmp_path / "x.zip", "0" * 64, opener_for(page))
    assert list(tmp_path.iterdir()) == []


def test_a_short_body_is_not_kept(tmp_path):
    short = Response(b"abc", headers={"Content-Length": "10"})
    with pytest.raises(OSError, match="3 of 10 bytes"):
        pq.fetch_verified("https://d.example/x", tmp_path / "x", "0" * 64, opener_for(short))
    assert list(tmp_path.iterdir()) == []


def test_a_size_other_than_the_one_on_file_is_refused_before_reading(tmp_path):
    with pytest.raises(pq.ChecksumMismatch, match="expected 99"):
        pq.fetch_verified(
            "https://d.example/x", tmp_path / "x", "0" * 64, opener_for(Response(b"abc")),
            expected_size=99,
        )  # fmt: skip


def test_a_pause_mid_file_stops_and_leaves_no_file(tmp_path):
    body = b"x" * (3 * (8 << 20))
    seen = []

    def should_stop(n):
        seen.append(n)
        return "PAUSE file" if n > 0 else None

    with pytest.raises(pq.QueueStop, match="PAUSE"):
        pq.fetch_verified(
            "https://d.example/x", tmp_path / "x", hashlib.sha256(body).hexdigest(),
            opener_for(Response(body)), should_stop=should_stop,
        )  # fmt: skip
    assert not (tmp_path / "x").exists()
    assert seen[0] == len(body)  # asked first with the whole file still to come

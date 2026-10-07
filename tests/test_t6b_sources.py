"""T6b sources: a deflated member streamed out of a remote zip, checked against its CRC."""

import io
import zipfile

import pytest

from forager_forecast.t6b_sources import extract_zip_member


def _zip_bytes(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in members.items():
            z.writestr(name, data)
    return buf.getvalue()


def _range_reader(blob: bytes):
    def read_range(start: int, length: int):
        return io.BytesIO(blob[start : start + length])

    return read_range


def test_a_member_comes_out_byte_identical_without_the_rest_of_the_zip(tmp_path):
    payload = bytes(range(256)) * 5000
    blob = _zip_bytes({"other.bin": b"x" * 100_000, "data/layer.tif": payload})
    out = tmp_path / "layer.tif"
    record = extract_zip_member(_range_reader(blob), len(blob), "data/layer.tif", out)
    assert out.read_bytes() == payload
    assert record["crc32_ok"] is True
    assert record["file_size"] == len(payload)


def test_a_corrupted_member_is_refused_not_written_as_good(tmp_path):
    payload = b"forest" * 50_000
    blob = bytearray(_zip_bytes({"m.bin": payload}))
    info = zipfile.ZipFile(io.BytesIO(bytes(blob))).getinfo("m.bin")
    # Flip one byte inside the stored member's compressed data.
    start = info.header_offset + 30 + len(info.filename) + len(info.extra) + 10
    blob[start] ^= 0xFF
    out = tmp_path / "m.bin"
    with pytest.raises(ValueError):
        extract_zip_member(_range_reader(bytes(blob)), len(blob), "m.bin", out)
    assert not out.exists()


def test_a_missing_member_is_an_error(tmp_path):
    blob = _zip_bytes({"a": b"1"})
    with pytest.raises(KeyError):
        extract_zip_member(_range_reader(blob), len(blob), "b", tmp_path / "b")


def test_a_download_stops_at_its_deadline_and_resumes_where_it_stopped(tmp_path):
    from forager_forecast.t6b_sources import download_resumable

    payload = bytes(range(256)) * 4000  # 1,024,000 bytes

    def open_from(start):
        return io.BytesIO(payload[start:])

    ticks = iter([0.0, 0.0, 99.0])  # passes the deadline after the second chunk
    dest = tmp_path / "layer.tif"
    first = download_resumable(open_from, len(payload), dest, deadline=50.0,
                               clock=lambda: next(ticks, 99.0), chunk=300_000)  # fmt: skip
    assert first["complete"] is False and not dest.exists()
    assert dest.with_name("layer.tif.partial").stat().st_size == 600_000
    second = download_resumable(open_from, len(payload), dest, deadline=None, chunk=300_000)
    assert second["complete"] is True and dest.read_bytes() == payload
    import hashlib

    assert second["sha256"] == hashlib.sha256(payload).hexdigest()

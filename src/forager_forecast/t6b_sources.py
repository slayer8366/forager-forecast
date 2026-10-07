"""T6b sources fetched whole: CEC boundaries, CEC ecoregions and NALCMS 2020 land cover.

docs/dispatch/2026-10-06-t6b-continental-layers.md, rulings D111 to D115.

- The two CEC vector zips are small and are downloaded whole to the flash drive.
- NALCMS 2020 30 m (CEC North American Atlas, CC BY 4.0, D112) is published only inside a 3.95 GB
  zip whose members are deflated, so it cannot be read by window over HTTP. Only its GeoTIFF member
  (3.36 GB) is wanted, so ``extract_zip_member`` streams that member's byte range out of the remote
  zip, inflates it, and checks it against the CRC-32 the zip itself carries. That CRC is the only
  publisher-side check available: CEC publishes no checksum for the zip. A mismatch deletes the
  partial file and raises.
"""

import hashlib
import io
import struct
import urllib.request
import zipfile
import zlib
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

CEC_POLITICAL_URL = (
    "https://www.cec.org/files/atlas_layers/0_reference/0_01_political_boundaries/"
    "politicalboundaries_shapefile.zip"
)
CEC_ECOREGIONS_URL = (
    "https://www.cec.org/files/atlas_layers/1_terrestrial_ecosystems/1_06_3_terr_ecoregions_iii/"
    "terr_ecoregions_v2_level_iii_shapefile.zip"
)
NALCMS_URL = (
    "https://www.cec.org/files/atlas_layers/1_terrestrial_ecosystems/1_01_0_land_cover_2020_30m/"
    "land_cover_2020v2_30m_tif.zip"
)
NALCMS_DIR = "land_cover_2020v2_30m_tif/NA_NALCMS_landcover_2020v2_30m/"
NALCMS_TIF_MEMBER = NALCMS_DIR + "data/NA_NALCMS_landcover_2020v2_30m.tif"
NALCMS_SMALL_MEMBERS = (
    NALCMS_DIR + "data/NA_NALCMS_landcover_2020v2_30m.tif.vat.dbf",
    NALCMS_DIR + "data/NA_NALCMS_landcover_2020v2_30m.tif.aux.xml",
    NALCMS_DIR + "NALCMS_Class_Definitions_en.doc",
    "land_cover_2020v2_30m_tif/Terms of use.doc",
    "land_cover_2020v2_30m_tif/HowToCite_ComoCitar_CommentCiter.txt",
)
_CHUNK = 8 << 20

ReadRange = Callable[[int, int], BinaryIO]


def http_headers(url: str) -> dict:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=120) as response:
        return {
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "content_length": int(response.headers.get("Content-Length")),
        }


def http_range_reader(url: str) -> ReadRange:
    def read_range(start: int, length: int) -> BinaryIO:
        headers = {"Range": f"bytes={start}-{start + length - 1}"}
        response = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=300)
        if response.status != 206:
            raise ValueError(f"{url}: the server ignored the byte range (HTTP {response.status})")
        return response

    return read_range


class _RangeFile(io.RawIOBase):
    """A seekable file over a ReadRange, for zipfile's central-directory reads only."""

    def __init__(self, read_range: ReadRange, size: int) -> None:
        self._read_range, self._size, self._pos = read_range, size, 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._pos

    def seek(self, offset: int, whence: int = 0) -> int:
        base = {0: 0, 1: self._pos, 2: self._size}[whence]
        self._pos = base + offset
        return self._pos

    def readinto(self, b) -> int:
        n = min(len(b), self._size - self._pos)
        if n <= 0:
            return 0
        data = self._read_range(self._pos, n).read()
        b[: len(data)] = data
        self._pos += len(data)
        return len(data)


def extract_zip_member(read_range: ReadRange, size: int, member: str, dest: Path) -> dict:
    """Stream one deflated or stored member of a remote zip to ``dest``, checking its CRC-32."""
    dest = Path(dest)
    zf = zipfile.ZipFile(io.BufferedReader(_RangeFile(read_range, size), buffer_size=1 << 16))
    info = zf.getinfo(member)
    head = read_range(info.header_offset, 30).read()
    if head[:4] != b"PK\x03\x04":
        raise ValueError(f"{member}: no local header at {info.header_offset}")
    name_len, extra_len = struct.unpack("<HH", head[26:30])
    start = info.header_offset + 30 + name_len + extra_len
    if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        raise ValueError(f"{member}: compression type {info.compress_type} is not handled")
    inflate = zlib.decompressobj(-15) if info.compress_type == zipfile.ZIP_DEFLATED else None
    crc = 0
    written = 0
    sha = hashlib.sha256()
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".partial")
    try:
        with partial.open("wb") as out:
            stream = read_range(start, info.compress_size)
            while chunk := stream.read(_CHUNK):
                data = inflate.decompress(chunk) if inflate else chunk
                crc = zlib.crc32(data, crc)
                sha.update(data)
                out.write(data)
                written += len(data)
            if inflate:
                tail = inflate.flush()
                crc = zlib.crc32(tail, crc)
                sha.update(tail)
                out.write(tail)
                written += len(tail)
    except zlib.error as err:
        partial.unlink(missing_ok=True)
        raise ValueError(f"{member}: the deflate stream is damaged ({err})") from err
    if written != info.file_size or crc != info.CRC:
        partial.unlink(missing_ok=True)
        raise ValueError(
            f"{member}: {written} bytes with CRC {crc:08x}; the zip says "
            f"{info.file_size} bytes with CRC {info.CRC:08x}"
        )
    partial.rename(dest)
    return {
        "member": member,
        "file": dest.name,
        "file_size": written,
        "crc32": f"{crc:08x}",
        "crc32_ok": True,
        "sha256": sha.hexdigest(),
    }


def download(url: str, dest: Path) -> dict:
    """A whole file to ``dest``, with its HTTP validators, time and sha256."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    requested_at = datetime.now(UTC).isoformat(timespec="seconds")
    headers = http_headers(url)
    sha = hashlib.sha256()
    partial = dest.with_name(dest.name + ".partial")
    with urllib.request.urlopen(url, timeout=300) as response, partial.open("wb") as out:
        while chunk := response.read(_CHUNK):
            sha.update(chunk)
            out.write(chunk)
    if partial.stat().st_size != headers["content_length"]:
        partial.unlink()
        raise ValueError(f"{url}: short download")
    partial.rename(dest)
    return {
        "source": url,
        "requested_at": requested_at,
        "account": "anonymous",
        "http": headers,
        "file": dest.name,
        "sha256": sha.hexdigest(),
    }


def http_open_from(url: str):
    """A function giving the file from byte ``start`` to its end, for ``download_resumable``."""

    def open_from(start: int) -> BinaryIO:
        headers = {"Range": f"bytes={start}-"} if start else {}
        response = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=300)
        if start and response.status != 206:
            raise ValueError(f"{url}: the server ignored the byte range (HTTP {response.status})")
        return response

    return open_from


def download_resumable(open_from, size: int, dest: Path, deadline: float | None,
                       clock=None, chunk: int = _CHUNK) -> dict:  # fmt: skip
    """A whole file to ``dest`` through ``dest.partial``, resumable, stopping at ``deadline``.

    D118 and D114: a SCANFI layer can take hours, and a run section ends at its stop time, so the
    download stops between chunks once the deadline (a ``clock()`` value) has passed and the next
    section carries on from the partial file. The sha256 is taken over the whole file at the end.
    """
    import time

    clock = clock or time.time
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".partial")
    start = partial.stat().st_size if partial.exists() else 0
    if start < size:
        stream = open_from(start)
        with partial.open("ab") as out:
            while start < size:
                if deadline is not None and clock() >= deadline:
                    return {"complete": False, "bytes": start, "size": size}
                data = stream.read(chunk)
                if not data:
                    break
                out.write(data)
                start += len(data)
    if partial.stat().st_size != size:
        raise ValueError(f"{dest.name}: {partial.stat().st_size} bytes, expected {size}")
    sha = hashlib.sha256()
    with partial.open("rb") as f:
        while block := f.read(_CHUNK):
            sha.update(block)
    partial.rename(dest)
    return {"complete": True, "bytes": size, "size": size, "sha256": sha.hexdigest()}

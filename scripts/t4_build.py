"""T4 build: SoilGrids pH for western Washington to the master grid and a zoom-9 PMTiles archive.

Usage:
  uv run python scripts/t4_build.py fetch [--data-dir data/t4]   # the one SoilGrids fetch
  uv run python scripts/t4_build.py build [--data-dir data/t4]   # master grid, then archive

``fetch`` reads nine windows over the network from ISRIC's WebDAV (D80 depths x D81 statistics)
and writes data/t4/native/ with request.json beside it. Copy request.json to docs/pulls/ after a
real fetch. ``build`` needs no network. Then run scripts/t4_ten_cells.py on the same data dir.
data/ is gitignored; nothing here writes into the repository.
"""

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path

from forager_forecast.soilgrids import (
    PROPERTY,
    SOILGRIDS_BASE_URL,
    layer_name,
    layers,
    parse_checksums,
    verify_sha256,
    vrt_url,
)
from forager_forecast.t4_layer import (
    ARCHIVE_NAME,
    WESTERN_WASHINGTON,
    build_archive,
    build_master,
    fetch_natives,
)


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as response, open(dest, "wb") as out:
        shutil.copyfileobj(response, out)


def fetch(data: Path) -> int:
    """Check each VRT against ISRIC's published sha256, then read the nine windows."""
    vrt_dir = data / "vrt"
    checksum_url = f"{SOILGRIDS_BASE_URL}/{PROPERTY}/checksum.sha256.txt"
    _download(checksum_url, vrt_dir / "checksum.sha256.txt")
    checksums = parse_checksums((vrt_dir / "checksum.sha256.txt").read_text())
    verified = []
    for depth, stat in layers():
        name = f"{layer_name(depth, stat)}.vrt"
        _download(vrt_url(depth, stat), vrt_dir / name)
        verified.append(verify_sha256(vrt_dir / name, checksums, name))
        print(f"{name}: {verified[-1]['verdict']}", flush=True)
    request = fetch_natives(data / "native", WESTERN_WASHINGTON)
    body = json.loads(request.read_text())
    body["isric_checksums"] = {
        "source": checksum_url,
        "covers": "the VRT and OVR files only; ISRIC publishes no checksum for the GeoTIFF tiles",
        "vrt_files": verified,
    }
    request.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n")
    print(f"request record: {request}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["fetch", "build"])
    parser.add_argument("--data-dir", type=Path, default=Path("data/t4"))
    args = parser.parse_args(argv)
    data = args.data_dir
    if args.step == "fetch":
        return fetch(data)
    summary = build_master(data / "native", data / "master.tif", WESTERN_WASHINGTON)
    header, metadata = build_archive(data / "master.tif", data / "archive")
    archive = data / "archive" / f"{ARCHIVE_NAME}.pmtiles"
    report = {
        "master": summary,
        "archive": {
            "path": str(archive),
            "bytes": archive.stat().st_size,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "min_zoom": header["min_zoom"],
            "max_zoom": header["max_zoom"],
            "tile_type": header["tile_type"],
            "addressed_tiles": header.get("addressed_tiles_count"),
        },
        "metadata": metadata,
    }
    (data / "build.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

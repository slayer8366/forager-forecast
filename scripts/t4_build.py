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
import sys
from pathlib import Path

from forager_forecast.t4_layer import (
    ARCHIVE_NAME,
    WESTERN_WASHINGTON,
    build_archive,
    build_master,
    fetch_natives,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["fetch", "build"])
    parser.add_argument("--data-dir", type=Path, default=Path("data/t4"))
    args = parser.parse_args(argv)
    data = args.data_dir
    if args.step == "fetch":
        request = fetch_natives(data / "native", WESTERN_WASHINGTON)
        print(f"request record: {request}")
        return 0
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

"""T6b: download SCANFI v2 2025's eleven layers whole, download only (Forager RECORD -620, D118).

A daytime job beside app builds, so it runs light (network-bound) and at low priority:
    nice -n 19 ionice -c3 .venv/bin/python scripts/t6b_fetch_scanfi_layers.py [--reserve-gb 8]
        [--until HH:MM]
Each layer goes to forecast-data/t6b/scanfi_whole/<layer>.tif with its request record and sha256 in
forecast-data/t6b/requests/. A layer already there is skipped; a partial one resumes. Before each
layer the free space must cover it plus the reserve, kept for the night sections' outputs; the job
stops there otherwise. The scanfi-layers stage of scripts/t6b_run.py regrids and deletes them later.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from forager_forecast.t5_layer import scanfi_url
from forager_forecast.t6b_layers import SCANFI_LAYERS
from forager_forecast.t6b_run import next_stop
from forager_forecast.t6b_sources import download_layers

DRIVE = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data")
T6B = DRIVE / "t6b"
LOG = T6B / "scanfi_download.log"


def log(msg: str) -> None:
    line = f"{datetime.now().astimezone().isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--reserve-gb", type=float, default=8.0)
    p.add_argument("--until", default=None, help="local HH:MM; a download stops there, resumable")
    args = p.parse_args()
    if not DRIVE.is_dir():
        sys.exit("flash drive not mounted")
    deadline = next_stop(args.until, datetime.now()).timestamp() if args.until else None
    log(f"start: {len(SCANFI_LAYERS)} layers, reserve {args.reserve_gb} GB, until {args.until}")
    out = download_layers(
        SCANFI_LAYERS, lambda layer: scanfi_url(layer, 2025), T6B / "scanfi_whole",
        T6B / "requests", reserve=int(args.reserve_gb * 1e9), deadline=deadline, log=log,
    )  # fmt: skip
    log(f"end: done {[d['layer'] for d in out['done']]}, already {out['already']}, "
        f"stopped {out['stopped']}")  # fmt: skip


if __name__ == "__main__":
    main()

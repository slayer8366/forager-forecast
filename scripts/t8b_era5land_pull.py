"""Part B item 3 of the pulls queue (dispatch 2026-10-26-pulls): ERA5-Land, one month at a time.

Run by scripts/pulls_queue.sh inside the detached unit, or alone from this repository's root:
    <venv>/bin/python scripts/t8b_era5land_pull.py
Files go to forecast-data/t8b/era5land/era5land-YYYY-MM.nc, each with its request record beside
it. Exit 0: all 135 months verified; 2: the queue stopped itself (MD5 or size off the store's,
login wall, licence refusal, low space, PAUSE, three failed attempts); 1: an error. The reason is
the last line of forecast-data/pulls/queue.log.
"""

import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

from forager_forecast.t8b import cds_pull as cp

LOG = cp.FORECAST_DATA / "pulls" / "queue.log"


def log(msg: str) -> None:
    line = f"{datetime.now(UTC).isoformat(timespec='seconds')} [B] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def main() -> int:
    if not cp.FORECAST_DATA.is_dir():
        log(f"STOP: {cp.FORECAST_DATA} is not mounted")
        return 2
    url, key = cp.read_cdsapirc(Path.home() / ".cdsapirc")
    api = cp.HttpApi(url, key)
    todo = cp.months()
    log(f"ERA5-Land start: {len(todo)} months, {cp.DATASET}, area {cp.AREA}, out {cp.OUT}")
    try:
        for n, (year, month) in enumerate(todo, 1):
            rec = cp.pull_month(api, cp.http_opener, year, month, cp.OUT, cp.FORECAST_DATA, log,
                                time.sleep)  # fmt: skip
            log(f"[{n}/{len(todo)}] {year}-{month:02d} {'skipped' if rec is None else 'done'}")
    except cp.QueueStop as err:
        log(f"STOP in ERA5-Land: {err}")
        return 2
    except Exception as err:  # noqa: BLE001  logged with its traceback's end, then the queue stops
        tail = " | ".join(traceback.format_exc().strip().splitlines()[-3:])
        log(f"ERROR in ERA5-Land: {type(err).__name__}: {err} | {tail}")
        return 1
    log("ERA5-Land end: all months verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())

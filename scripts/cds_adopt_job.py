"""Wait for one job the store already holds under this account; download it with a request record.

Run:  uv run --with cdsapi==0.7.7 python scripts/cds_adopt_job.py <job id> <target .nc> <note>

Used for job d6ae24ed (ERA5 daily rain 2026-07 to 2026-10, submitted by the scoring coder under the
shared account, adopted at the planner's instruction of 2026-10-10). The request is read back from
the store (`?request=true`) and written beside the file, as D52 asks.
"""

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


def main(job: str, target: Path, note: str) -> int:
    import cdsapi  # noqa: PLC0415

    client = cdsapi.Client(quiet=True, progress=False)
    headers = {"PRIVATE-TOKEN": client.key}
    info = client.session.get(
        f"{client.url}/retrieve/v1/jobs/{job}?request=true", headers=headers, timeout=60
    ).json()
    t0 = time.monotonic()
    tmp = target.with_suffix(".nc.part")
    client.client.get_remote(job).download(str(tmp))
    tmp.rename(target)
    record = {
        "dataset": info.get("processID"),
        "request": info.get("metadata", {}).get("request", {}).get("ids"),
        "job_id": job,
        "submitted_utc": info.get("created"),
        "adopted": note,
        "seconds_waited_after_adoption": round(time.monotonic() - t0, 1),
        "bytes": target.stat().st_size,
        "downloaded_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "account": "the CDS test account (D43); key read by cdsapi from ~/.cdsapirc, not recorded",
    }
    target.with_suffix(".request.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], Path(sys.argv[2]), sys.argv[3]))

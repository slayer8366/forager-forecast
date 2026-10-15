import sys, json, time
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, "scripts")
import cdsapi, cds_jobs
import pnw_cds_precip_hourly as p
out = Path.home() / "Zynergy/forecast-data-pnw-pilot/cds"
name, request = [c for c in p.scoring_chunks() if c[0].endswith("10-05T00")][0]
nc, rec = out / f"{name}.nc", out / f"{name}.request.json"
client = cdsapi.Client(quiet=True, progress=False)
while True:
    requested_at = datetime.now(UTC).isoformat(timespec="seconds"); t0 = time.monotonic()
    try:
        tmp = nc.with_suffix(".nc.part"); adopted = cds_jobs.fetch(client, p.DATASET, request, str(tmp)); tmp.rename(nc); break
    except Exception as err:
        if "temporarily limited" in str(err): time.sleep(120); continue
        print("FAILED", repr(err), flush=True); sys.exit(1)
rec.write_text(json.dumps({"dataset": p.DATASET, "request": request, "requested_at_utc": requested_at,
    "seconds": round(time.monotonic() - t0, 1), "bytes": nc.stat().st_size, "adopted_job": adopted,
    "account": p.ACCOUNT, "client": "cdsapi==0.7.7 via uv run --with",
    "note": "submitted beside the sequential rain step to save queue time (same request as scoring_chunks())"}, indent=2) + "\n")
print(name, "ok", nc.stat().st_size, flush=True)

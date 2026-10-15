"""Read-only on the drive: build the new plot table from the real TreeMap 2023 tree table into a
temporary folder under the repository (never the drive), time it, and summarise each band.

Writes nothing under forecast-data/. Output: plot_table_real.out.json beside this file.
"""

import json
import resource
import sys
import time
from pathlib import Path

import numpy as np

from forager_forecast.t6b_hosts import BAND_LAYOUT
from forager_forecast.t6b_layers import build_plot_table

TREEMAP = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t5/treemap2023")
out = Path(sys.argv[1]) / "plots_new.npz"
out.parent.mkdir(parents=True, exist_ok=True)
t0 = time.time()
info = build_plot_table(TREEMAP / "RDS-2026-0038.zip", TREEMAP / "TreeMap2023_CONUS.tif.vat.dbf", out)
seconds = time.time() - t0
with np.load(out) as z:
    bands = z["bands"].tolist()
    table = z["table"]
per_band = {b: {"plots_with_cover": int((table[:, 1 + k] > 0).sum()),
                "max_cover_pct": round(float(np.nanmax(table[:, 1 + k])), 3)}
            for k, b in enumerate(bands)}
summary = {"seconds": round(seconds, 1), "band_layout": BAND_LAYOUT, "columns": table.shape[1],
           "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024),
           "file_bytes": out.stat().st_size, **{k: v for k, v in info.items() if k != "file"},
           "per_band": per_band}
print(json.dumps(summary, indent=1))

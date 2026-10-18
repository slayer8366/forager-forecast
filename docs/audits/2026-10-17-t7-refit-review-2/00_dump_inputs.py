"""Review 2: dump the training table's y, w, blocks, clusters, year and columns, assembled by the
coder's own Data loader (input assembly only; every AUC and interval after this is my own code)."""
import sys
from pathlib import Path
sys.path.insert(0, "scripts")
import numpy as np
import t7_fit as f
work = Path("/mnt/work/Zynergy/forecast-data/t7/refit")
SIDE = {}
d = f.Data(work, f.V9 / "presences_main.csv", access_band=f.MAIN_ACCESS)
np.savez("/mnt/work/Zynergy/rv2-scratch/main.npz", y=d.y, w=d.w, blocks=d.blocks, clusters=d.clusters, year=d.year,
         x=d.x, columns=np.array(d.columns), held_access=d.held_access)
print("main", d.n_presences, d.n_background, d.columns, d.held_access)
import json
json.dump({"genus": [p["genus"] for p in d.presences], "gbif_id": [p["gbif_id"] for p in d.presences]},
          open("/mnt/work/Zynergy/rv2-scratch/main_presences.json", "w"))

"""Review 2: dump the saprotroph-main and comparison-group tables the same way as 00_dump_inputs.py."""
import sys
from pathlib import Path
sys.path.insert(0, "scripts")
import numpy as np
import t7_fit as f
work = Path("/mnt/work/Zynergy/forecast-data/t7/refit")
for name, path, tag in (("saprotroph main", f.V9C / "presences_saprotroph_main.csv", "sap"),
                        ("comparison group", f.V9 / "presences_comparison.csv", "lae")):
    d = f.Data(work, path, track="all", access_band=f.MAIN_ACCESS)
    np.savez(f"/mnt/work/Zynergy/rv2-scratch/{tag}.npz", y=d.y, w=d.w, blocks=d.blocks, clusters=d.clusters, x=d.x)
    print(name, d.n_presences, d.n_background)

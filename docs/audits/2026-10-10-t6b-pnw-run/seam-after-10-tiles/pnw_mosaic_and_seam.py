"""PNW mosaic and 49 N seam check after the 8 Canadian tiles, written only under /mnt/work.
Runs scripts/pnw_build.py's stage_mosaic and scripts/pnw_checks.py's seam with their output
folder pointed at a scratch directory, so the drive's forecast-data/pnw/ is not rewritten."""
import importlib.util, json, sys
from pathlib import Path
REPO = Path(sys.argv[1]); OUT = Path(sys.argv[2])
def load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
b = load("pnw_build"); b.OUT = OUT; b.MOSAIC = OUT / "mosaic"
OUT.mkdir(parents=True, exist_ok=True)
b.check_free = lambda: None
mosaic = b.stage_mosaic()
print(json.dumps({"mosaic": mosaic}, indent=1))
c = load("pnw_checks"); c.OUT = OUT
s = c.seam(); s["us_side_samples"] = c.seam_us_samples()
(OUT / "seam.out.json").write_text(json.dumps(s, indent=1, default=str) + "\n")
print(json.dumps({b_: {k: v for k, v in r.items() if k != "border_steps"} for b_, r in s["bands"].items()}, indent=1, default=str))

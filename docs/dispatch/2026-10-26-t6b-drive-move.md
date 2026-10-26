# Dispatch: point T6b's drive setting at the new 231 GB drive

Written by the forecast planner (Alder Bearing), 2026-10-26, for Ash Transect. The 57 GB flash drive is gone. The
owner said the drive now plugged in, label `forager-storage` (ext4, 231 GB), is for forecast data: "Forecast data:
use it". The owner made the folder `/run/media/zynergy-labs/forager-storage/forecast-data` ("done"). The planner
checked it: owned by zynergy-labs, writable, 194 GB free. The drive also holds `rollback/` (34 GB of map tiles and
routing segments from the Pi/map work), which isn't ours.

**Do:** change `DRIVE` in `src/forager_forecast/drive.py` to
`Path("/run/media/zynergy-labs/forager-storage/forecast-data")`. Update its docstring and the tests in
`tests/test_t6b_drive.py` (tests first: show the test failing against the old value). Re-run `drive_check.py`
from `docs/audits/2026-10-25-t6b-rebuild-check/` against the new path, and commit its output beside the old one as
`drive_check.run4.out.txt`. Then run the full suite.

**Don't:** touch anything outside `forecast-data/` on that drive, and never `rollback/`. Download nothing, and
start no run. Delete the check's scratch files after it runs, as before. Keep processes under 2 GB
(`systemd-run --user --scope -p MemoryMax=2G -p MemorySwapMax=0 nice -n 10`), with the venv and uv cache under
`/mnt/work/scratch/t6b-drive-move/`, deleted at the end.

**Hand-back:** the pushed commit hash (from `git ls-remote origin t6b-rebuild`), the failing-then-passing test,
the drive check's result, and the test counts. Commit messages end with "Co-Authored-By: Claude <noreply@anthropic.com>".

"""Read-only: the new plot table's T5 columns against the run's own plots.npz on the drive.

Columns 0 to 8 (tree-list total and T5's eight bands) and the last (CANOPYPCT) must be identical,
bit for bit; that is the dispatch's "no existing column changes its meaning". Prints JSON.
"""

import json
import sys
from pathlib import Path

import numpy as np

DRIVE_PLOTS = Path(
    "/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b/plots.npz"
)
with np.load(DRIVE_PLOTS) as z:
    old_ids, old = z["ids"], z["table"]
with np.load(Path(sys.argv[1])) as z:
    new_ids, new = z["ids"], z["table"]
same = lambda a, b: bool(np.array_equal(a, b, equal_nan=True))  # noqa: E731
print(json.dumps({
    "old_shape": list(old.shape), "new_shape": list(new.shape),
    "ids_identical": same(old_ids, new_ids),
    "columns_0_to_8_identical": same(old[:, :9], new[:, :9]),
    "canopypct_identical": same(old[:, -1], new[:, -1]),
}, indent=1))  # fmt: skip

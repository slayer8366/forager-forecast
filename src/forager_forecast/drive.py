"""Where T6b's store lives: the one setting every script reads.

Since 2026-10-26 it is the ``forecast-data`` folder on the drive labelled ``forager-storage``
(ext4, 231 GB), which mounts at a path named by its label. The 57 GB flash drive labelled
``forecast-data`` (forecast RECORD 2026-09-28-2056), whose mount was the setting before, is gone.
The owner gave the new drive to forecast data ("Forecast data: use it") and made the folder
(dispatch 2026-10-26-t6b-drive-move). The setting is the folder, not the mount, because the drive
also holds ``rollback/`` from the map work, which isn't ours: nothing here writes outside
``DRIVE``. Below it the layout is as before: T6b's store is ``DRIVE / "t6b"``, TreeMap 2023 is
``DRIVE / "t5" / "treemap2023"`` and the PNW render is ``DRIVE / "pnw"`` (dispatch
2026-10-25-t6b-rebuild-check, item 1).
"""

from pathlib import Path

DRIVE = Path("/run/media/zynergy-labs/forager-storage/forecast-data")

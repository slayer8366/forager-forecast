"""Where the flash drive holding T6b's store is mounted: the one setting every script reads.

The drive was reformatted ext4 with the label ``forecast-data`` (forecast RECORD 2026-09-28-2056),
so it mounts at a path named by its label, which survives a reformat, where the old one was named
by its filesystem UUID and broke when the drive was lost (-2053). The mount itself takes the place
of the old drive's ``forecast-data`` folder: T6b's store is ``DRIVE / "t6b"``, TreeMap 2023 is
``DRIVE / "t5" / "treemap2023"`` and the PNW render is ``DRIVE / "pnw"``, as before below that
folder (dispatch 2026-10-25-t6b-rebuild-check, item 1).
"""

from pathlib import Path

DRIVE = Path("/run/media/zynergy-labs/forecast-data")

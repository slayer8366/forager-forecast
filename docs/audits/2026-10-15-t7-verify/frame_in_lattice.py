"""Cross-check for box_cells.py's frame count: effort-frame cell keys inside the box's 0.1 degree
lattice (centres 40.0 to 49.0 N, 125.0 to 111.0 W). Reads lat_tenths and lon_tenths only."""

import csv
from pathlib import Path

p = Path.home() / "Zynergy/forager-forecast-t6/data/t6/all/cell_level.csv"
n = 0
tot = 0
for r in csv.DictReader(p.open()):
    tot += 1
    a, b = int(r["lat_tenths"]), int(r["lon_tenths"])
    n += 400 <= a <= 490 and -1250 <= b <= -1110
print({"frame_cells": tot, "frame_cells_in_box_lattice": n})

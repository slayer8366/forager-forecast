"""Review 2, question 4: V9's thinned presence count recounted for three genera from the D26
zip with my own code, from the rules as read (records/filters.py:58-131, occurrence.py:85-122,
cells.py:68-87, t7/presences.py docstring and thin()).

One streamed pass over occurrence.txt inside the zip (never extracted, never written). Rows of
the three genera only are kept in memory. Compared against V9's counts.json per-genus figures and
against the (genus, cell) pairs of presences_main.csv. No project code is imported.
"""

import csv
import io
import json
import math
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import date
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path

from pyproj import Transformer

HERE = Path(__file__).resolve().parent
ZIP = Path.home() / "Zynergy/forager-forecast-d26/data/d26/downloads/0012112-260928105237408.zip"
V9 = Path("/mnt/work/Zynergy/forecast-data/t7/v9")
GENERA = ("Amanita", "Craterellus", "Humaria")
BOX = (40.0, 49.0, -125.0, -111.0)  # south, north, west, east, edges inclusive
FWD = Transformer.from_crs("EPSG:4269", "ESRI:102008", always_xy=True)
BACK = Transformer.from_crs("ESRI:102008", "EPSG:4269", always_xy=True)
HALF = Decimal("0.5")


def tenths(value: float) -> int:
    return int((Decimal(repr(value)) * 10 + HALF).to_integral_value(rounding=ROUND_FLOOR))


def event_day(text: str):
    text = text.strip()
    if not text:
        return None
    ends = text.split("/")
    if len(ends) > 2:
        return None
    days = []
    for end in ends:
        d = end.partition("T")[0]
        if len(d) != 10:
            return None
        try:
            days.append(date.fromisoformat(d))
        except ValueError:
            return None
    if len(days) == 2 and days[0] != days[1]:
        return None
    return days[0]


def cell_of(lon: float, lat: float):
    x, y = FWD.transform(lon, lat)
    col, row = math.floor(x / 250), math.floor(y / 250)
    cid = ((row + 32768) << 16) | (col + 32768)
    clon, clat = BACK.transform((col + 0.5) * 250, (row + 0.5) * 250)
    return cid, clon, clat


def main():
    counts = Counter()
    kept = defaultdict(list)  # genus -> records that pass R6 (before duplicate step)
    with zipfile.ZipFile(ZIP) as z, z.open("occurrence.txt") as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", newline=""), delimiter="\t",
                                quoting=csv.QUOTE_NONE)
        for row in reader:
            counts["rows"] += 1
            g = (row.get("genus") or "").strip()
            if g not in GENERA:
                continue
            counts[f"{g} rows"] += 1
            day = event_day(row.get("eventDate") or "")
            if day is None:
                counts[f"{g} unloadable date"] += 1
                continue
            try:
                lat, lon = float(row["decimalLatitude"]), float(row["decimalLongitude"])
            except (ValueError, KeyError):
                counts[f"{g} no coordinates"] += 1
                continue
            if (row.get("informationWithheld") or "").strip() or (row.get("dataGeneralizations") or "").strip():
                counts[f"{g} user_obscured"] += 1
                continue
            u = (row.get("coordinateUncertaintyInMeters") or "").strip()
            try:
                u = float(u)
            except ValueError:
                u = None
            if u is None or u > 250.0:
                counts[f"{g} coordinate_uncertainty"] += 1
                continue
            kept[g].append((int(row["gbifID"]), row["acceptedTaxonKey"], (row.get("recordedBy") or "").strip(),
                            lat, lon, day, u, (row.get("license") or "").strip()))
    out = {"rows_read": counts["rows"], "zip": str(ZIP)}
    with open(V9 / "presences_main.csv", newline="") as f:
        v9 = defaultdict(set)
        for r in csv.DictReader(f):
            if r["genus"] in GENERA:
                v9[r["genus"]].add((int(r["gbif_id"]), int(r["cell_id"])))
    v9c = json.loads((V9 / "counts.json").read_text())["runs"]["main"]["thinned"]["per_genus"]
    for g in GENERA:
        recs = kept[g]
        # duplicate step: lowest gbifID per (taxon, observer, 0.1 degree cell, day)
        best = {}
        for rec in recs:
            gid, taxon, who, lat, lon, day, u, lic = rec
            key = (taxon, who, tenths(lat), tenths(lon), day)
            if key not in best or gid < best[key][0]:
                best[key] = rec
        survivors = list(best.values())
        inbox = []
        for rec in survivors:
            cid, clon, clat = cell_of(rec[4], rec[3])
            if BOX[0] <= clat <= BOX[1] and BOX[2] <= clon <= BOX[3]:
                inbox.append((rec[0], cid))
        thin = {}
        for gid, cid in inbox:
            if cid not in thin or gid < thin[cid]:
                thin[cid] = gid
        mine = {(gid, cid) for cid, gid in thin.items()}
        out[g] = {
            "rows": counts[f"{g} rows"], "unloadable_date": counts[f"{g} unloadable date"],
            "no_coordinates": counts[f"{g} no coordinates"],
            "dropped_user_obscured": counts[f"{g} user_obscured"],
            "dropped_uncertainty": counts[f"{g} coordinate_uncertainty"],
            "after_filters": len(recs), "after_duplicate_step": len(survivors), "in_box": len(inbox),
            "thinned_mine": len(mine), "thinned_v9_counts_json": v9c.get(g),
            "v9_presence_rows": len(v9[g]),
            "same_gbif_id_and_cell_set_as_v9_file": mine == v9[g],
            "only_mine": len(mine - v9[g]), "only_v9": len(v9[g] - mine),
        }
    (HERE / "v9_recount.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

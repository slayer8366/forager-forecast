"""Q4: recount V9's thinned presences for three genera from the D26 zip with the reviewer's own
code, and compare with counts.json and the presence files (gbifID sets).

Rules re-implemented from their text (records/filters.py r6_audit_steps, records/occurrence.py
parse_event, grid.py, pnw.PNW_BOX, D144 rule 3), not imported:
  date: eventDate is one calendar day (YYYY-MM-DD[Thh:mm...]) or a range within one day;
  not user-obscured: informationWithheld and dataGeneralizations both empty;
  uncertainty present and <= 250 m;
  duplicate: one record per (acceptedTaxonKey, recordedBy stripped, 0.1 degree cell, day), lowest
    gbifID; the cell is the nearest tenth, exact ties toward +infinity (decimal arithmetic);
  box: the 250 m cell's centre (ESRI:102008, from EPSG:4269 with no datum step) inside
    40..49 N, -125..-111 E, edges included;
  thinning: one per genus per 250 m cell, lowest gbifID.
Streams occurrence.txt out of the zip; nothing is extracted."""

import csv
import io
import json
import math
import sys
import zipfile
from collections import Counter, defaultdict
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path

from pyproj import Transformer

csv.field_size_limit(1 << 30)
ZIP = Path.home() / "Zynergy/forager-forecast-d26/data/d26/downloads/0012112-260928105237408.zip"
V9 = Path("/mnt/work/Zynergy/forecast-data/t7/v9")
GENERA = {"Cantharellus": "main", "Humaria": "main", "Laetiporus": "comparison"}
OUT = Path(__file__).parent / "q4_v9_recount.json"


def one_day(text):
    text = text.strip()
    if not text:
        return None
    ends = text.split("/")
    if len(ends) > 2:
        return None
    days = []
    for e in ends:
        d = e.partition("T")[0]
        if len(d) != 10:
            return None
        try:
            import datetime as dt
            dt.date.fromisoformat(d)
        except ValueError:
            return None
        days.append(d)
    if len(days) == 2 and days[0] != days[1]:
        return None
    return days[0]


def tenth(text):
    v = Decimal(text.strip()) * 10 + Decimal("0.5")
    return int(v.to_integral_value(rounding=ROUND_FLOOR))


to_grid = Transformer.from_crs("EPSG:4269", "ESRI:102008", always_xy=True)
to_ll = Transformer.from_crs("ESRI:102008", "EPSG:4269", always_xy=True)

steps = Counter()
best = {}  # dup key -> (gbif_id, lat, lon, genus, year, licence)
with zipfile.ZipFile(ZIP) as z, z.open("occurrence.txt") as raw:
    rd = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""), delimiter="\t",
                    quoting=csv.QUOTE_NONE)
    head = next(rd)
    ix = {h: i for i, h in enumerate(head)}
    for row in rd:
        steps["rows"] += 1
        g = row[ix["genus"]]
        if g not in GENERA:
            continue
        steps[f"{g} rows"] += 1
        day = one_day(row[ix["eventDate"]])
        if day is None:
            steps[f"{g} undated"] += 1
            continue
        if row[ix["informationWithheld"]].strip() or row[ix["dataGeneralizations"]].strip():
            steps[f"{g} obscured"] += 1
            continue
        u = row[ix["coordinateUncertaintyInMeters"]].strip()
        try:
            uv = float(u)
        except ValueError:
            uv = None
        if uv is None or uv > 250:
            steps[f"{g} uncertainty"] += 1
            continue
        lat_s, lon_s = row[ix["decimalLatitude"]], row[ix["decimalLongitude"]]
        key = (row[ix["acceptedTaxonKey"]], row[ix["recordedBy"]].strip(), tenth(lat_s),
               tenth(lon_s), day)
        gid = int(row[ix["gbifID"]])
        rec = (gid, float(lat_s), float(lon_s), g, int(day[:4]), row[ix["license"]], uv)
        if key not in best or gid < best[key][0]:
            if key in best:
                steps[f"{g} duplicate"] += 1
            best[key] = rec
        else:
            steps[f"{g} duplicate"] += 1
print(dict(steps), flush=True)

thin = {}
for gid, lat, lon, g, year, lic, uv in best.values():
    x, y = to_grid.transform(lon, lat)
    col, rw = math.floor(x / 250), math.floor(y / 250)
    clon, clat = to_ll.transform((col + 0.5) * 250, (rw + 0.5) * 250)
    if not (40 <= clat <= 49 and -125 <= clon <= -111):
        steps[f"{g} outside box"] += 1
        continue
    cid = ((rw + 32768) << 16) | (col + 32768)
    k = (g, cid)
    if k not in thin or gid < thin[k][0]:
        thin[k] = (gid, cid)
mine = defaultdict(set)
for (g, _), (gid, _) in thin.items():
    mine[g].add(gid)

counts = json.loads((V9 / "counts.json").read_text())
theirs_files = defaultdict(set)
for run in ("main", "comparison"):
    with open(V9 / f"presences_{run}.csv", newline="") as f:
        for r in csv.DictReader(f):
            if r["genus"] in GENERA:
                theirs_files[r["genus"]].add(int(r["gbif_id"]))
out = {"rows_read": steps["rows"], "steps": dict(steps), "genera": {}}
for g, run in GENERA.items():
    reported = counts["runs"][run]["thinned"]["per_genus"].get(g)
    out["genera"][g] = {"mine": len(mine[g]), "counts_json": reported,
                        "presence_file": len(theirs_files[g]),
                        "gbif_id_sets_equal": mine[g] == theirs_files[g],
                        "only_mine": len(mine[g] - theirs_files[g]),
                        "only_theirs": len(theirs_files[g] - mine[g])}
OUT.write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))

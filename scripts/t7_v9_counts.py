"""T7 V9: the presence count for the PNW, under D144's four counting rules (Forager RECORD -1081).

Usage:
  python scripts/t7_v9_counts.py <evidence dir in the repo> <data dir outside the repo>

1. Checks the D26 zip's sha256 against its pull record (docs/pulls/
   gbif-fungi-us-canada-2015-2025.doi.json, "sha256_of_zip"); refuses on a difference.
2. Writes the normalised membership list from the committed FungalTraits export (D143) to the
   data dir and refuses unless its sha256 is ``fungaltraits.NORMALISED_LIST_SHA256``.
3. Three passes over occurrence.txt, streamed out of the zip, each through ``names.load_named``
   and ``presences.select_presences`` (R6's steps, the box test by the 250 m cell's centre, the
   join): the mycorrhizal group's main run, its side run (M2: mixed and uncertain genera, and
   family-only records whose family is wholly ectomycorrhizal in the list), and the comparison
   group (M4, genus Laetiporus). Every row read is checked to be accounted for.
4. Thinning, one presence per genus (or family label) per 250 m cell, lowest gbifID kept (D144
   rule 3); the CC0 and CC BY licence track (D108's licences) is filtered *before* thinning, so its
   kept record is the lowest CC one in each genus-cell. Weights under rule 4 (30, pooled below).
5. Per presence: side and study area from the T6b mask, level III and level I block by cell
   centre (``ecoregions.burn_level3``), inside or outside T6's effort frame (the stored surface's
   cell keys, no effort value read), year.

Writes counts.json to the evidence dir (counts only, no record identifier, no coordinate), and the
thinned presence tables (gbifID, genus, cell id, weather cell, year, uncertainty, licence) to the
data dir for the fit. Read only on the flash drive.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import resource
import sys
import time
import zipfile
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from pyproj import Transformer

from forager_forecast.effort import CC_TRACK_LICENSES
from forager_forecast.grid import CELL_SIZE_M, GEOGRAPHIC_CRS, GRID_CRS, cell_from_id
from forager_forecast.pnw import PNW_BOX, pnw_window
from forager_forecast.records.occurrence import (
    OccurrenceLoader,
    missing_columns,
    read_occurrence_rows,
)
from forager_forecast.t6b_mask import (
    COUNTRY_CAN,
    COUNTRY_US48,
    ECO_OTHER,
    SIDE_CA,
    SIDE_US,
    read_mask,
    side_rule,
)
from forager_forecast.t7 import fungaltraits as ft
from forager_forecast.t7.ecoregions import burn_level3, read_level3
from forager_forecast.t7.membership import (
    COMPARISON_GROUP,
    MAIN_RUN,
    MYCORRHIZAL_GROUP,
    SIDE_RUN,
    Join,
    load_list,
)
from forager_forecast.t7.names import load_named, missing_name_columns
from forager_forecast.t7.presences import (
    OUTSIDE_BOX,
    POOLED,
    PROPOSED_MIN_PRESENCES_PER_GENUS,
    genus_weights,
    select_presences,
    thin,
)

REPO = Path(__file__).resolve().parent.parent
ZIP = Path.home() / "Zynergy/forager-forecast-d26/data/d26/downloads/0012112-260928105237408.zip"
PULL_RECORD = REPO / "docs/pulls/gbif-fungi-us-canada-2015-2025.doi.json"
T6B = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b")
MASK = T6B / "mask.tif"
LEVEL3 = (
    T6B / "sources/terr_ecoregions_v2_level_iii_shapefile/NA_TerrEcoregions_III/data"
    / "NA_Terrestrial_Ecoregions_v2_level3.shp"
)  # fmt: skip
EFFORT_CELLS = Path.home() / "Zynergy/forager-forecast-t6/data/t6/all/cell_level.csv"
EFFORT_CELLS_SHA256 = "5c243721d41349d7dbc6b27a55bcc24ed060ffaa3d0e1ba10992a5ffe46893ff"
MIN = PROPOSED_MIN_PRESENCES_PER_GENUS  # D144 rule 4
BLOCK_MIN = 30  # D139
RUNS = {
    "main": (MYCORRHIZAL_GROUP, MAIN_RUN),
    "side": (MYCORRHIZAL_GROUP, SIDE_RUN),
    "comparison": (COMPARISON_GROUP, MAIN_RUN),
}


def saprotroph_runs(genera) -> dict:
    """STUB (tests first)."""
    return {}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def one_pass(join: Join):
    loader = OccurrenceLoader()
    with zipfile.ZipFile(ZIP).open("occurrence.txt") as raw:
        handle = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        rows = read_occurrence_rows(handle)
        presences, counts = select_presences(load_named(rows, loader), join, PNW_BOX)
    survivors = counts.r6_steps[-1].after
    if loader.rows_read != counts.r6_steps[0].before + sum(loader.unloadable.values()):
        raise SystemExit("rows read are not all accounted for")
    if survivors != sum(counts.outcomes.values()):
        raise SystemExit("R6 survivors are not all accounted for by the box test and the join")
    return presences, counts, loader


class Places:
    """Side, study area, level III and level I for master cells, read once over the box."""

    def __init__(self) -> None:
        self.window = pnw_window()
        self.table, polygons = read_level3(LEVEL3)
        self.l3 = burn_level3(polygons, self.window)
        del polygons
        self.country, self.eco = read_mask(MASK, self.window)
        self.by_code = {e.code: e for e in self.table}
        self._to_lonlat = Transformer.from_crs(GRID_CRS, GEOGRAPHIC_CRS, always_xy=True)

    def of(self, cell_ids: np.ndarray) -> dict[str, np.ndarray]:
        cells = [cell_from_id(int(c)) for c in cell_ids]
        top = self.window.top // CELL_SIZE_M
        r = np.array([top - 1 - c.row for c in cells], dtype=np.int64)
        k = np.array([c.col - self.window.left // CELL_SIZE_M for c in cells], dtype=np.int64)
        x = (np.array([c.col for c in cells]) + 0.5) * CELL_SIZE_M
        y = (np.array([c.row for c in cells]) + 0.5) * CELL_SIZE_M
        lon, lat = self._to_lonlat.transform(x, y)
        country, eco = self.country[r, k], self.eco[r, k]
        study = ((country == COUNTRY_US48) | (country == COUNTRY_CAN)) & (eco == ECO_OTHER)
        side = np.where(study, side_rule(np.asarray(lon), np.asarray(lat), country), 0)
        code = self.l3[r, k]
        return {"study": study, "side": side, "l3": code}


def tally(presences, places: Places, frame: set) -> dict:
    if not presences:
        return {"presences": 0}
    ids = np.array([p.cell_id for p in presences], dtype=np.int64)
    at = places.of(ids)
    side_name = np.where(at["side"] == SIDE_US, "US", np.where(at["side"] == SIDE_CA, "Canada",
                                                               "outside study area"))  # fmt: skip
    l3_name = [
        f"{places.by_code[int(c)].level3} {places.by_code[int(c)].name}" if c else "none"
        for c in at["l3"]
    ]
    l1_name = [places.by_code[int(c)].level1 if c else "none" for c in at["l3"]]
    in_frame = np.array([(p.lat_tenths, p.lon_tenths) in frame for p in presences])
    per_genus = Counter(p.genus for p in presences)
    per_block = defaultdict(Counter)
    per_block_genus = defaultdict(Counter)
    for p, s, b in zip(presences, side_name, l3_name, strict=True):
        per_block[b][s] += 1
        if s == "US":
            per_block_genus[b][p.genus] += 1
    us = side_name == "US"
    return {
        "presences": len(presences),
        "genera": len(per_genus),
        "per_genus": dict(per_genus.most_common()),
        "per_year": dict(sorted(Counter(p.year for p in presences).items())),
        "per_year_us": dict(
            sorted(Counter(p.year for p, u in zip(presences, us, strict=True) if u).items())
        ),  # fmt: skip
        "per_side": dict(Counter(side_name.tolist()).most_common()),
        "per_level3": {
            b: dict(c) for b, c in sorted(per_block.items(), key=lambda kv: -sum(kv[1].values()))
        },
        "per_level1": dict(Counter(l1_name).most_common()),
        "per_level1_us": dict(
            Counter(n for n, u in zip(l1_name, us, strict=True) if u).most_common()
        ),  # fmt: skip
        "us_blocks_under_minimum": sorted(
            b for b, c in per_block.items() if b != "none" and 0 < c.get("US", 0) < BLOCK_MIN
        ),
        "us_blocks_with_none": sorted(
            f"{e.level3} {e.name}"
            for e in places.table
            if f"{e.level3} {e.name}" in per_block
            and per_block[f"{e.level3} {e.name}"].get("US", 0) == 0
        ),  # fmt: skip
        "outside_effort_frame": int((~in_frame).sum()),
        "outside_effort_frame_us": int((~in_frame & us).sum()),
        "per_licence": dict(Counter(p.license for p in presences).most_common()),
    }


def weights_summary(presences) -> dict:
    gw = genus_weights(presences, MIN)
    alone = sorted(u for u in gw.presences_per_unit if u != POOLED)
    pooled_genera = sorted(g for g, u in gw.unit_of.items() if u == POOLED)
    return {
        "minimum_per_genus": MIN,
        "units": len(gw.presences_per_unit),
        "genera_counting_alone": len(alone),
        "genera_pooled": len(pooled_genera),
        "presences_in_pool": gw.presences_per_unit.get(POOLED, 0),
        "pooled_genera": pooled_genera,
        "total_weight": float(gw.weights.sum()),
    }


def write_presences(path: Path, presences) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    with partial.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(("gbif_id", "genus", "cell_id", "lat_tenths", "lon_tenths", "year",
                    "uncertainty_m", "license"))  # fmt: skip
        for p in presences:
            w.writerow((p.gbif_id, p.genus, p.cell_id, p.lat_tenths, p.lon_tenths, p.year,
                        repr(p.uncertainty_m), p.license))  # fmt: skip
    partial.rename(path)
    return sha256_file(path)


def main(evidence: Path, data: Path) -> None:
    t0 = time.monotonic()
    started = datetime.now(UTC).isoformat(timespec="seconds")
    record = json.loads(PULL_RECORD.read_text(encoding="utf-8"))
    zip_sha = sha256_file(ZIP)
    if zip_sha != record["sha256_of_zip"]:
        raise SystemExit(f"zip sha256 {zip_sha} is not the pull record's {record['sha256_of_zip']}")
    print("zip sha256 ok", zip_sha, flush=True)
    if sha256_file(EFFORT_CELLS) != EFFORT_CELLS_SHA256:
        raise SystemExit("T6's cell_level.csv is not the stored one")
    with zipfile.ZipFile(ZIP).open("occurrence.txt") as raw:
        header = io.TextIOWrapper(raw, encoding="utf-8", newline="").readline()
    names = header.rstrip("\r\n").split("\t")
    lacking = missing_columns(names) + missing_name_columns(names)
    if lacking:
        raise SystemExit(f"occurrence.txt lacks {lacking}")

    data.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    list_path = data / "membership_list_fungaltraits_export.tsv"
    list_sha = ft.convert_export(list_path)
    members = load_list(list_path, ft.NORMALISED_LIST_SHA256)
    frame = set()
    with EFFORT_CELLS.open(encoding="utf-8", newline="") as h:
        for row in csv.DictReader(h):
            frame.add((int(row["lat_tenths"]), int(row["lon_tenths"])))
    places = Places()
    print("places ready", round(time.monotonic() - t0, 1), flush=True)

    out = {
        "started_utc": started,
        "zip": str(ZIP),
        "zip_sha256": zip_sha,
        "zip_sha256_in_pull_record": record["sha256_of_zip"],
        "membership_list_sha256": list_sha,
        "export_sha256": ft.EXPORT_DATA_SHA256,
        "rule_version": ft.RULE_VERSION,
        "effort_frame_cells": len(frame),
        "level3_table_size": len(places.table),
        "rules": "D144: (1) mushroom-forming genera only by fruitbody type, via the list's "
        "'clear' certainty in the main run; (2) family-only records in the side run "
        "only; (3) one presence per genus per 250 m cell; (4) 30 to count alone, pooled "
        "below",  # fmt: skip
        "runs": {},
    }
    files = {}
    for name, (group, run) in RUNS.items():
        t = time.monotonic()
        raw_presences, counts, loader = one_pass(Join(members, list_sha, group, run))
        thinned = thin(raw_presences)
        entry = {
            "group": group.name,
            "run": run,
            "rows_read": loader.rows_read,
            "unloadable": dict(loader.unloadable.most_common()),
            **counts.as_dict(),
            "all_fungi_r6_survivors_in_box": int(sum(v for k, v in counts.outcomes.items()
                                                     if k != OUTSIDE_BOX)),
            "presences_before_thinning": len(raw_presences),
            "thinned": tally(thinned, places, frame),
            "weights": weights_summary(thinned),
            "seconds": round(time.monotonic() - t, 1),
            "peak_rss_mb_so_far": round(peak_rss_mb(), 1),
        }  # fmt: skip
        if name == "side":
            family_only = [p for p in raw_presences if p.genus.startswith("(family ")]
            entry["family_only_records_before_thinning"] = dict(
                Counter(p.genus for p in family_only).most_common()
            )
            main_genera = set(out["runs"]["main"]["thinned"]["per_genus"])
            entry["genera_added_by_side_run"] = {
                g: n for g, n in entry["thinned"]["per_genus"].items() if g not in main_genera
            }
            entry["genera_added_notes"] = {
                g: members.rows[g].note for g in entry["genera_added_by_side_run"]
                if g in members.rows
            }  # fmt: skip
        out["runs"][name] = entry
        files[name] = write_presences(data / f"presences_{name}.csv", thinned)
        if name == "main":
            cc = thin([p for p in raw_presences if p.license in CC_TRACK_LICENSES])
            out["runs"]["licence_track"] = {
                "group": group.name, "run": "main, CC0 and CC BY records only (D108)",
                "licences": sorted(CC_TRACK_LICENSES),
                "presences_before_thinning": sum(p.license in CC_TRACK_LICENSES
                                                 for p in raw_presences),
                "thinned": tally(cc, places, frame), "weights": weights_summary(cc),
            }  # fmt: skip
            files["licence_track"] = write_presences(data / "presences_licence_track.csv", cc)
        del raw_presences, thinned
        print(name, entry["presences_before_thinning"], entry["thinned"]["presences"],
              entry["seconds"], flush=True)  # fmt: skip
    out["presence_files_outside_repo"] = {k: {"path": str(data / f"presences_{k}.csv"),
                                              "sha256": v} for k, v in files.items()}  # fmt: skip
    out["ended_utc"] = datetime.now(UTC).isoformat(timespec="seconds")
    out["seconds"] = round(time.monotonic() - t0, 1)
    out["peak_rss_mb"] = round(peak_rss_mb(), 1)
    text = json.dumps(out, indent=1, ensure_ascii=False) + "\n"
    (evidence / "counts.json").write_text(text, encoding="utf-8")
    (data / "counts.json").write_text(text, encoding="utf-8")
    print("done", out["seconds"], flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))

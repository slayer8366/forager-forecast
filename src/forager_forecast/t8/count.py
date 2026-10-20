"""T8's count (plan section 9, item 2; the first point of no return): the jump check and the lichen
attach, under one word. scripts/t8_count.py is the command line; this module does the work.

What it reads: D26's zip in place (its sha256 checked first, occurrence.txt streamed, never
extracted), and T1's own unit files and summaries. No weather is read (plan section 2).

1. Every loadable row in T1's PNW box is kept (t1_design.box_of), as scripts/pnw_t1_records.py
   keeps them. Beside each Cantharellus row its speciesKey and taxonRank are kept for J6; and the
   genus keys of J5's six names are resolved from the zip's own genus and genusKey columns,
   refusing a name that maps to no key or to more than one.
2. Each of T1's three step lists (design.T1_LISTS) runs over those records, as T1's records script
   runs them. Its units and outcomes are recounted (units.recount_units) and must equal T1's
   stored units exactly (units.check_same_units), with extras only by the number T1 dropped for
   want of weather, read from T1's own summary. Lichen outcomes and outings are attached to its
   units (units.attach_lichens).
3. On the headline list only, the jump check: J1 to J6 (jump.tally) and the plan's rule
   (jump.read_jump).

The count refuses to start while any reading it depends on is open (design.require_ruled).
"""

from __future__ import annotations

import dataclasses
import hashlib
import io
import json
import math
import resource
import time
import zipfile
from collections import Counter
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from forager_forecast.cell_weeks import cell_week_of
from forager_forecast.cells import iso_week_of
from forager_forecast.effort import observer_of
from forager_forecast.records.filters import (
    FilterStep,
    Pipeline,
    Steps,
    UncertaintyAbove,
    t1_steps,
)
from forager_forecast.records.occurrence import (
    OccurrenceLoader,
    Record,
    missing_columns,
    read_occurrence_rows,
)
from forager_forecast.t1_design import CANTHARELLUS_GENUS_KEY, box_of
from forager_forecast.t8 import design
from forager_forecast.t8 import jump as jp
from forager_forecast.t8 import units as tu

# As scripts/pnw_t1_records.py (T1's records script).
CC_LICENSES = frozenset({"CC0_1_0", "CC_BY_4_0"})
UNCERTAINTY_STEP = "coordinate uncertainty present and at most 1,000 m"
EXTRA_COLUMNS = ("classKey", "speciesKey", "taxonRank", "genus")
# J6 (design.PENDING J-species): "the record carries a GBIF speciesKey" is the proposal; the
# alternative is a taxonRank at species or below.
SPECIES_OR_BELOW = frozenset({"SPECIES", "SUBSPECIES", "VARIETY", "SUBVARIETY", "FORM", "SUBFORM"})


class CountRefused(RuntimeError):
    """The count cannot run as fixed: a checksum, a column, a genus key or T1's units differ."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def with_uncertainty_limit(steps: Steps, limit_m: float) -> Steps:
    """T1's records script's 5,000 m list: t1_steps() with only the uncertainty limit changed."""
    filters = tuple(
        FilterStep(
            f"coordinate uncertainty present and at most {limit_m:,.0f} m",
            UncertaintyAbove(limit_m),
        )
        if s.name == UNCERTAINTY_STEP
        else s
        for s in steps.filters
    )
    if filters == steps.filters:
        raise CountRefused("the uncertainty step was not found in t1_steps()")
    return dataclasses.replace(steps, filters=filters)


def list_steps(name: str) -> tuple[Steps, Callable[[Record], bool]]:
    """Each T1 list's steps and the record filter applied before them (T1's records script)."""
    if name == "t1_1000m":
        return t1_steps(), lambda r: True
    if name == "t1_5000m":
        return with_uncertainty_limit(t1_steps(), 5000.0), lambda r: True
    if name == "t1_1000m_cc":
        return t1_steps(), lambda r: r.license in CC_LICENSES
    raise ValueError(f"unknown list {name!r}")


@dataclass
class BoxRead:
    records: list[Record]
    rows_read: int
    unloadable: dict[str, int]
    species_key: dict[int, bool]  # gbif id -> speciesKey present, Cantharellus rows only
    taxon_rank: dict[int, str]  # gbif id -> taxonRank, Cantharellus rows only
    genus_keys_seen: dict[str, set[int]] = field(default_factory=dict)


def read_box(zip_path: Path, genus_names: tuple[str, ...]) -> BoxRead:
    """The loadable rows in T1's PNW box, with J6's and J5's extra fields."""
    loader = OccurrenceLoader()
    species_key: dict[int, bool] = {}
    taxon_rank: dict[int, str] = {}
    seen: dict[str, set[int]] = {g: set() for g in genus_names}
    canth = str(CANTHARELLUS_GENUS_KEY)

    def rows(handle) -> Iterator[dict[str, str]]:
        first = True
        for row in read_occurrence_rows(handle):
            if first:
                missing = missing_columns(row.keys()) + [c for c in EXTRA_COLUMNS if c not in row]
                if missing:
                    raise CountRefused(f"occurrence.txt lacks columns {missing}")
                first = False
            genus_key = row.get("genusKey", "").strip()
            name = row.get("genus", "").strip()
            if name in seen and genus_key:
                seen[name].add(int(genus_key))
            if genus_key == canth:
                try:
                    gid = int(row.get("gbifID", "").strip())
                except ValueError:
                    gid = None  # the loader counts this row as unloadable
                if gid is not None:
                    species_key[gid] = bool(row.get("speciesKey", "").strip())
                    taxon_rank[gid] = row.get("taxonRank", "").strip().upper()
            yield row

    records = []
    with zipfile.ZipFile(zip_path) as archive, archive.open("occurrence.txt") as raw:
        handle = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        for record in loader.load(rows(handle)):
            box = box_of(record.latitude, record.longitude)
            if box is not None and box.name == "pnw":
                records.append(record)
    return BoxRead(
        records,
        loader.rows_read,
        dict(loader.unloadable.most_common()),
        species_key,
        taxon_rank,
        seen,
    )


def resolve_genus_keys(seen: Mapping[str, set[int]]) -> dict[str, int]:
    """Each J5 name's one genus key, from the zip's own columns; refuses an ambiguous name."""
    bad = {g: sorted(k) for g, k in seen.items() if len(k) != 1}
    if bad:
        raise CountRefused(f"J5 genus names without exactly one genusKey in the zip: {bad}")
    keys = {g: next(iter(k)) for g, k in seen.items()}
    if CANTHARELLUS_GENUS_KEY in keys.values():
        raise CountRefused("a J5 genus resolved to Cantharellus's key")
    return keys


def t1_extra_units(summary_json: Path, stored: int) -> int:
    """How many units T1 dropped for want of weather (sea units), from T1's own summary."""
    drops = json.loads(summary_json.read_text())["weather_units_dropped"]
    kept = drops["kept_land_point_own"] + drops["kept_land_point_neighbour_RECORD_822"]
    if kept != stored:
        raise CountRefused(f"{summary_json.name}: kept {kept} units, but its npz holds {stored}")
    return int(drops["units_before"]) - kept


def has_species(gbif_id: int, box: BoxRead, rule: str) -> bool:
    if rule == "speciesKey":
        return box.species_key.get(gbif_id, False)
    if rule == "taxonRank":
        return box.taxon_rank.get(gbif_id, "") in SPECIES_OR_BELOW
    raise ValueError(f"unknown J6 rule {rule!r}")


def jump_records(
    survivors: list[Record],
    t1: tu.T1Units,
    genus_keys: Mapping[str, int],
    box: BoxRead,
    species_rule: str,
) -> list[jp.JumpRecord]:
    """J1 to J6's fields for Cantharellus and the six J5 genera among the survivors."""
    wanted = set(genus_keys.values()) | {CANTHARELLUS_GENUS_KEY}
    year_of_unit = dict(zip(t1.unit.tolist(), t1.year.tolist(), strict=True))
    out = []
    for r in survivors:
        if r.genus_key not in wanted:
            continue
        cw = cell_week_of(r)
        unit = tu.unit_id(cw.cell, cw.week.monday())
        out.append(
            jp.JumpRecord(
                year=r.event_date.year,
                observer=observer_of(r),
                dataset=r.dataset_key,
                iso_week=iso_week_of(r.event_date).week,
                cell=cw.cell.id,
                unit=unit,
                genus_key=r.genus_key,
                has_species=has_species(r.gbif_id, box, species_rule),
                unit_year=year_of_unit.get(unit),
            )
        )
    return out


@dataclass
class ListCount:
    name: str
    steps: list[dict]
    survivors: int
    units: int
    extra_units: int
    lichen: tu.LichenAttach


def count_list(
    name: str, box: BoxRead, fits_dir: Path
) -> tuple[ListCount, list[Record], tu.T1Units]:
    stem, expected_total = design.T1_LISTS[name]
    steps, keep = list_steps(name)
    pipeline = Pipeline(steps)
    survivors = pipeline.run(r for r in box.records if keep(r))
    t1 = tu.read_t1_units(fits_dir / f"{stem}.npz")
    extra = t1_extra_units(fits_dir / f"{stem}.json", len(t1))
    recounted = tu.recount_units(survivors, CANTHARELLUS_GENUS_KEY)
    tu.check_same_units(t1, recounted, extra, expected_total)
    lichen = tu.attach_lichens(t1, survivors)
    steps_out = [
        {"step": c.step, "before": c.before, "dropped": c.dropped, "after": c.after}
        for c in pipeline.counts
    ]
    return ListCount(name, steps_out, len(survivors), len(t1), extra, lichen), survivors, t1


def _jsonable(x):
    if isinstance(x, float) and not math.isfinite(x):
        return str(x)
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, list | tuple | set):
        return [_jsonable(v) for v in (sorted(x) if isinstance(x, set) else x)]
    return x


def run_count(
    zip_path: Path,
    expected_sha256: str,
    fits_dir: Path,
    out_dir: Path,
    species_rule: str = "speciesKey",
    log: Callable[[str], None] = lambda _m: None,
) -> dict:
    """The whole count. Writes lichen_<list>.npz and count_summary.json to out_dir."""
    design.require_ruled("count")
    started = time.monotonic()
    actual = sha256_file(zip_path)
    if actual != expected_sha256:
        raise CountRefused(f"zip sha256 {actual} differs from {expected_sha256}")
    log("zip sha256 checked")
    box = read_box(zip_path, jp.PROPOSED_GENERA)
    log(f"{box.rows_read} rows read, {len(box.records)} in the PNW box")
    genus_keys = resolve_genus_keys(box.genus_keys_seen)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary: dict = {
        "zip": str(zip_path),
        "zip_sha256": actual,
        "rows_read": box.rows_read,
        "unloadable": box.unloadable,
        "records_in_pnw_box": len(box.records),
        "j5_genus_keys": genus_keys,
        "j6_rule": species_rule,
        "lists": {},
    }
    headline: tuple[list[Record], tu.T1Units] | None = None
    for name in design.T1_LISTS:
        counted, survivors, t1 = count_list(name, box, fits_dir)
        lichen = counted.lichen
        np.savez_compressed(
            out_dir / f"lichen_{name}.npz",
            unit=t1.unit,
            lichen_y=lichen.positive,
            lichen_outings=lichen.outings,
            lichen_records=lichen.records,
        )
        summary["lists"][name] = {
            "steps": counted.steps,
            "survivors": counted.survivors,
            "units": counted.units,
            "units_identical_to_t1": True,
            "extra_units_t1_dropped_for_weather": counted.extra_units,
            "lichen_positive_units": int(lichen.positive.sum()),
            "lichen_records_in_units": int(lichen.records.sum()),
            "lichen_outings_in_units": int(lichen.outings.sum()),
            "lichen_records_outside_units": lichen.outside_units,
        }
        log(f"{name}: units identical to T1's ({counted.units}), lichens attached")
        if name == design.HEADLINE_LIST:
            headline = (survivors, t1)
        else:
            del survivors
    assert headline is not None
    survivors, t1 = headline
    records = jump_records(survivors, t1, genus_keys, box, species_rule)
    units_by_year = dict(Counter(t1.year.tolist()))
    tallies = jp.tally(
        records, units_by_year, CANTHARELLUS_GENUS_KEY, jp.proposed_reading(genus_keys)
    )
    verdict = jp.read_jump(tallies)
    summary["jump"] = {
        "label": verdict.label,
        "reasons": list(verdict.reasons),
        "reading": dataclasses.asdict(tallies.reading),
        "tallies": _jsonable(
            {k: v for k, v in dataclasses.asdict(tallies).items() if k != "reading"}
        ),
        "note": "reporting data cannot prove a surge on its own (plan section 2)",
    }
    summary["seconds"] = round(time.monotonic() - started, 1)
    summary["peak_rss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    (out_dir / "count_summary.json").write_text(json.dumps(_jsonable(summary), indent=2) + "\n")
    return summary

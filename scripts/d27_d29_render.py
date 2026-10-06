"""Render the D27, D28 and D29 outputs as Markdown tables for the completion report.

Usage:
  uv run python scripts/d27_d29_render.py <tables directory> <datasets .json> [<more .json>...]

The tables directory is scripts/d27_d28_tables.py's output. Prints to stdout. No "probability" or
"chance" in any table (dispatch; D58): the test column is headed "p-value".
"""

import json
import sys
from pathlib import Path

REGIONS = ("pnw", "east", "outside_t1_boxes")
RULES = (
    "drop_all",
    "keep_all",
    "per_dataset",
    "per_dataset_plus_small",
    "per_dataset_plus_too_few",
)


def fmt_p(value: float | None) -> str:
    if value is None:
        return "n/a"
    if value == 0.0:
        return "< 1e-300"
    if value < 0.001:
        return f"{value:.1e}"
    return f"{value:.3f}"


def d28(tables: Path) -> None:
    a = json.loads((tables / "assessment.json").read_text(encoding="utf-8"))
    tested = sum(1 for d in a["datasets"] if d["level_each"] is not None)
    level = next((d["level_each"] for d in a["datasets"] if d["level_each"] is not None), None)
    print(
        f"Reference share 1/30 = {a['reference_share']:.5f}; calendar share 12/365.2425 = "
        f"{a['calendar_share_shown_not_used']:.5f} (shown, not used). Minimum {a['min_date_only']} "
        f"date-only records. {tested} datasets tested, so each is tested at "
        f"{a['family_level']} / {tested} = {level:.5f}. Clear excess also needs the interval's "
        f"lower end at {a['clear_excess_lower_end']:.5f} (2/30) or more.\n"
    )
    print(
        "| Dataset | Loaded | Date-only | On the 1st | Share | × 1/30 | × calendar | 95% interval "
        "| p-value | Excess on the 1st | Verdict |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for d in a["datasets"]:
        if d["date_only"]:
            lo, hi = d["interval_95"]
            share = f"{d['share']:.4f}"
            r30 = f"{d['ratio_to_1_in_30']:.2f}"
            rcal = f"{d['ratio_to_calendar_share']:.2f}"
            interval = f"{lo:.4f} to {hi:.4f}"
        else:
            share = r30 = rcal = interval = "n/a"
        print(
            f"| {d['title']} | {d['loaded']:,} | {d['date_only']:,} "
            f"| {d['date_only_on_the_1st']:,} "
            f"| {share} | {r30} | {rcal} | {interval} | {fmt_p(d['p_value_one_sided'])} "
            f"| {d['excess_on_the_1st']:+,.1f} | {d['verdict']} |"
        )
    print()


def passes(tables: Path) -> dict[str, dict]:
    out = {}
    for path in sorted(tables.glob("pass_*.json")):
        out[path.stem.removeprefix("pass_")] = json.loads(path.read_text(encoding="utf-8"))
    return out


def d27_and_rules(tables: Path) -> None:
    runs = json.loads((tables / "runs.json").read_text(encoding="utf-8"))
    got = passes(tables)
    for list_name, title in (("t1", "T1 list"), ("r6", "R6 audit list")):
        print(f"#### {title}: survivors by date rule, both keys\n")
        print(
            "| Rule | Date step drops | Reach the duplicate step | Event key: total "
            "| PNW | East | Outside | Observer key: total | PNW | East | Outside |"
        )
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for rule in RULES:
            label = f"{list_name}_{rule}"
            if label not in got:
                print(f"| {rule} | {runs['passes'].get(label, 'not run')} |||||||||| ")
                continue
            p = got[label]
            date_step = next(s for s in p["steps"] if "default" in s["step"])
            cells = [f"{date_step['dropped']:,}", f"{p['duplicate_step_reads']['records']:,}"]
            for key in ("event", "observer"):
                s = p["survivors"][key]
                cells.append(f"{s['total']:,}")
                cells.extend(f"{s['by_region'].get(r, 0):,}" for r in REGIONS)
            print(f"| {rule} | " + " | ".join(cells) + " |")
        print()


def d29(paths: list[Path]) -> None:
    for path in paths:
        d = json.loads(path.read_text(encoding="utf-8"))
        print(f"#### {d['download_key']} (DOI {d['doi']}), `{path}`\n")
        print(
            f"Rows counted {d['rows_counted']:,} "
            f"(DOI record {d['total_records_in_doi_record']:,}); "
            f"datasets counted {d['datasets_counted']} (DOI record "
            f"{d['number_of_datasets_in_doi_record']}, "
            f"GBIF's list {d['gbif_download_datasets_listed']})."
            f" GBIF list read {d['gbif_download_datasets_list_read_utc']}.\n"
        )
        total = d["rows_counted"]
        print("| Record's own licence field | Records | Share |\n|---|---|---|")
        for lic, n in d["records_by_own_license_field"].items():
            print(f"| {lic} | {n:,} | {n / total:.1%} |")
        print()
        print(
            "| Dataset | Licence per GBIF API | Licence in the zip | Records | GBIF's count "
            "| By record licence |"
        )
        print("|---|---|---|---|---|---|")
        for x in d["datasets"]:
            split = ", ".join(f"{k} {v:,}" for k, v in x["records_by_own_license_field"].items())
            print(
                f"| {x['title']} | {x['license_per_gbif_api']} "
                f"| {x.get('license_in_zip') or 'n/a'} "
                f"| {x['records_counted_in_download']:,} | {x['records_per_gbif_download_list']:,} "
                f"| {split} |"
            )
        print()


def main(tables: Path, dataset_lists: list[Path]) -> None:
    print("### D28: day-of-month table, by dataset\n")
    d28(tables)
    print("### D27 and D28: survivors by list, rule and key\n")
    d27_and_rules(tables)
    print("### D29: dataset lists\n")
    d29(dataset_lists)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]])

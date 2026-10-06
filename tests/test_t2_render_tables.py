"""scripts/t2_render_tables.py refuses a count CSV it cannot render honestly (D26 review, F4).

The year-by-region tables loop over the known regions only, so a CSV written before the D26 rename
(region label rest_of_north_america) would print 0 for outside_t1_boxes there, silently.
"""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "t2_render_tables.py"


def _render_module():
    spec = importlib.util.spec_from_file_location("t2_render_tables", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_output(out_dir: Path, region: str) -> None:
    (out_dir / "counts_by_stage_group_region_year.csv").write_text(
        "stage,group,region,year,records\n"
        f"source,all_fungi,pnw,2020,3\nsource,all_fungi,{region},2020,5\n",
        encoding="utf-8",
    )
    (out_dir / "counts_by_license.csv").write_text(
        "stage,group,license,datasetKey,records\n", encoding="utf-8"
    )
    summary = {
        "rows_read": 8,
        "unloadable_rows": {},
        "source_count": 8,
        "survivors": 8,
        "steps": [],
        "event_date_shapes_of_rows_read": {},
        "information_withheld_distinct_prefixes": 0,
        "information_withheld_prefixes_of_rows_read": {},
        "data_generalizations_distinct_prefixes": 0,
        "data_generalizations_prefixes_of_rows_read": {},
    }
    (out_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")


def test_a_region_the_renderer_does_not_know_is_refused_by_name(tmp_path, capsys):
    _write_output(tmp_path, "rest_of_north_america")
    with pytest.raises(SystemExit, match="rest_of_north_america"):
        _render_module().main(tmp_path)
    assert "| Year |" not in capsys.readouterr().out, "nothing is rendered before the refusal"


def test_known_regions_render_with_their_counts_in_the_year_table(tmp_path, capsys):
    _write_output(tmp_path, "outside_t1_boxes")
    _render_module().main(tmp_path)
    out = capsys.readouterr().out
    assert "| 2020 | 3 | 0 | 0 | 0 | 5 | 0 |" in out

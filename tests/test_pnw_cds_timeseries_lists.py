"""scripts/pnw_cds_timeseries.py --lists: the 5,000 m list's points added for D33 (3) (planner,
after Forager RECORD -861), with the default (the 1,000 m list alone) unchanged. Synthetic record
lists only; no request is made."""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import pnw_cds_timeseries as ts  # noqa: E402

from forager_forecast.t1_design import CANTHARELLUS_GENUS_KEY  # noqa: E402

FIELDS = ["gbif_id", "taxon_key", "genus_key", "latitude", "longitude", "event_date", "license"]


def write_list(path: Path, cells: list[tuple[int, int]], first_id: int) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        for k, (la, lo) in enumerate(cells):
            w.writerow(
                {
                    "gbif_id": first_id + k,
                    "taxon_key": 1,
                    "genus_key": CANTHARELLUS_GENUS_KEY,
                    "latitude": la / 10,
                    "longitude": lo / 10,
                    "event_date": "2020-06-10",
                    "license": "CC0_1_0",
                }
            )


def records(tmp_path: Path) -> tuple[Path, set, set, set]:
    small = [(450 + i, -1230) for i in range(14)]
    extra = [(470, -1215), (471, -1215)]
    write_list(tmp_path / "t1_1000m.csv", small, 1)
    write_list(tmp_path / "t1_5000m.csv", small + extra, 100)
    has = set(small) | set(extra)
    return tmp_path, has, set(small), set(extra)


def test_the_default_pulls_the_1000m_list_alone(tmp_path):
    rec, has, small, extra = records(tmp_path)
    pts, keep = ts.points_needed(rec, has)
    assert set(pts) == small
    assert keep <= small and len(keep) > 0


def test_naming_the_5000m_list_adds_its_points(tmp_path):
    rec, has, small, extra = records(tmp_path)
    pts, keep = ts.points_needed(rec, has, ("t1_1000m", "t1_5000m"))
    assert set(pts) == small | extra
    assert keep == ts.points_needed(rec, has)[1]


def test_a_cell_without_land_reads_its_neighbour(tmp_path):
    rec, has, small, extra = records(tmp_path)
    has = has - {(470, -1215)}
    assert ts.list_points(rec, has, ("t1_5000m",)) == small | {(471, -1215)}


def test_the_command_line_default_is_the_1000m_list():
    import inspect  # noqa: PLC0415

    src = inspect.getsource(ts.main)
    assert 'default="t1_1000m"' in src
    assert inspect.signature(ts.points_needed).parameters["lists"].default == ("t1_1000m",)

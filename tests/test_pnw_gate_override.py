"""scripts/pnw_gate_override.py: going on past the land-route gate only on the owner's override
(Forager RECORD -854), with the gate itself unchanged. Driven through the command the run scripts
call; synthetic equivalence results shaped like the 2026-10-11 runs."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import pnw_equivalence as eq  # noqa: E402
import pnw_gate_override as go  # noqa: E402
import pnw_t1_fit as fit  # noqa: E402

# The offset counts both 2026-10-11 runs wrote (equivalence.json, hourly_land_route).
RUN_COUNTS = {
    "t2m": {-1: [762, 6912], 0: [6911, 6912], 1: [675, 6912]},
    "stl1": {-1: [2356, 6912], 0: [6912, 6912], 1: [2218, 6912]},
    "swvl1": {-1: [4149, 6912], 0: [6912, 6912], 1: [4133, 6912]},
}
HOUR = {
    "variable": "t2m",
    "cell": "493_-1250",
    "land_point": [493, -1250],
    "hour_utc": "2025-12-12T11:00",
    "store": 5.424951171875023,
    "open_meteo": 5.5,
}
NOT_BEFORE = "2026-10-11T14:00:00+00:00"


def equivalence(counts=RUN_COUNTS, spans_complete=True) -> dict:
    land = eq.land_route_pass(counts)
    return {
        "written_utc": "2026-10-11T14:19:15+00:00",
        "hourly_land_route": {
            "by_variable": {
                v: {"matched_compared_by_offset_hours": {str(o): c[o] for o in c}}
                for v, c in counts.items()
            },
            "pass": land,
        },
        "gate": {"spans_complete": spans_complete, "pass": land and spans_complete is not False},
    }


def failures(hours=(HOUR,), counts=RUN_COUNTS) -> dict:
    return {
        "offset0_matched_compared": {v: c[0] for v, c in counts.items()},
        "failing_hours": list(hours),
    }


def run(tmp_path, eq_result, fail_list, *extra) -> tuple[int, dict | None, str]:
    e, f, r = tmp_path / "eq.json", tmp_path / "fail.json", tmp_path / "record.json"
    e.write_text(json.dumps(eq_result))
    if fail_list is not None:
        f.write_text(json.dumps(fail_list))
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "pnw_gate_override.py"), str(e), str(f), str(r),
         "--not-before", NOT_BEFORE, *extra],
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    return proc.returncode, (json.loads(r.read_text()) if r.exists() else None), proc.stdout


def test_the_gate_still_fails_on_the_runs_counts():
    assert eq.land_route_pass(RUN_COUNTS) is False
    assert (eq.HOURLY_TOL, eq.EPS) == ({"t2m": 0.075, "stl1": 0.075, "swvl1": 0.001}, 1e-6)


def test_a_fail_with_no_override_stops_with_exit_3(tmp_path):
    code, record, _ = run(tmp_path, equivalence(), failures())
    assert code == 3
    assert record["proceed"] is False and record["gate_pass"] is False
    assert record["override"] == "none"


def test_a_fail_with_the_override_goes_on_and_records_the_hour(tmp_path):
    code, record, out = run(
        tmp_path, equivalence(), failures(), "--override", "Forager RECORD -854"
    )
    assert code == 0 and record["proceed"] is True
    assert record["gate_pass"] is False and record["land_route_pass"] is False
    assert record["override_given"] == "Forager RECORD -854"
    assert record["override"].startswith("used: Forager RECORD -854")
    assert record["failing_hours"] == [HOUR]
    assert record["hourly_by_variable"]["t2m"]["matched_compared_by_offset_hours"]["0"] == [
        6911,
        6912,
    ]
    assert "gate pass False" in out


def test_an_override_when_the_gate_passes_is_recorded_unused(tmp_path):
    passing = {**RUN_COUNTS, "t2m": {-1: [762, 6912], 0: [6912, 6912], 1: [675, 6912]}}
    code, record, _ = run(
        tmp_path, equivalence(passing), failures((), passing), "--override", "Forager RECORD -854"
    )
    assert code == 0 and record["gate_pass"] is True
    assert record["override"] == "unused: the gate passed"


@pytest.mark.parametrize(
    ("eq_result", "fail_list", "override", "stop"),
    [
        (equivalence(), failures(), "RECORD -854", "is not"),
        (equivalence(spans_complete=False), failures(), go.OVERRIDE, "required spans"),
        (equivalence(), failures((HOUR, {**HOUR, "hour_utc": "2025-12-12T12:00"})), go.OVERRIDE,
         "differ"),
        (equivalence(), failures(({**HOUR, "variable": "stl1"},)), go.OVERRIDE, "differ"),
        (equivalence(), None, go.OVERRIDE, "no failing-hours list"),
    ],
)  # fmt: skip
def test_the_override_covers_only_the_hour_it_was_given_for(
    tmp_path, eq_result, fail_list, override, stop
):
    code, record, _ = run(tmp_path, eq_result, fail_list, "--override", override)
    assert code == 3 and record["proceed"] is False
    assert stop in record["stop"]


def test_an_equivalence_result_older_than_this_run_stops(tmp_path):
    old = {**equivalence(), "written_utc": "2026-10-11T13:00:00+00:00"}
    code, record, _ = run(tmp_path, old, failures(), "--override", go.OVERRIDE)
    assert code == 3 and record is None


def test_the_fit_carries_a_go_record_and_refuses_a_stop_record(tmp_path):
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"proceed": True, "override": "used: Forager RECORD -854"}))
    assert fit.load_gate_record(p)["override"].startswith("used")
    p.write_text(json.dumps({"proceed": False, "stop": "gate failed"}))
    with pytest.raises(SystemExit, match="says stop"):
        fit.load_gate_record(p)
    with pytest.raises(SystemExit, match="does not exist"):
        fit.load_gate_record(tmp_path / "missing.json")
    assert fit.load_gate_record(None) is None

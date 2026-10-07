"""T6b sectioned runner (D114): stop time, pause file, resume, redo of a damaged unit, groups."""

import functools
import hashlib
import json
from datetime import datetime, timedelta

from forager_forecast.t6b_run import done_units, next_stop, read_lines, run_section


def _work(unit, out_dir, pause_after=None, pause_file=None):
    path = out_dir / f"{unit}.out"
    partial = path.with_name(path.name + ".partial")
    partial.write_text(f"result of {unit}\n")
    partial.rename(path)
    if pause_after == unit and pause_file is not None:
        pause_file.write_text("stop")
    return {"files": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}}


UNITS = [f"u{k}" for k in range(6)]


def test_a_pause_file_stops_the_section_after_the_tile_in_hand_and_the_next_resumes(tmp_path):
    manifest, pause = tmp_path / "manifest.jsonl", tmp_path / "PAUSE"
    work = functools.partial(_work, out_dir=tmp_path, pause_after="u1", pause_file=pause)
    first = run_section(UNITS, work, manifest, tmp_path, until=None, pause_file=pause)
    assert first["units_done_now"] == 2 and first["units_remaining"] == 4
    assert first["stopped"].startswith("pause file")
    assert done_units(manifest, tmp_path) == {"u0", "u1"}
    pause.unlink()
    second = run_section(UNITS, functools.partial(_work, out_dir=tmp_path), manifest, tmp_path,
                         until=None, pause_file=pause)  # fmt: skip
    assert second["units_done_before"] == 2 and second["units_done_now"] == 4
    assert second["units_remaining"] == 0 and second["stopped"] == "all units done"
    ran = [e["unit"] for e in read_lines(manifest) if e["kind"] == "unit"]
    assert ran == UNITS  # nothing ran twice


def test_a_stop_time_already_passed_starts_nothing(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    past = datetime.now() - timedelta(minutes=1)
    s = run_section(UNITS, functools.partial(_work, out_dir=tmp_path), manifest, tmp_path,
                    until=past, pause_file=tmp_path / "PAUSE")  # fmt: skip
    assert s["units_done_now"] == 0 and s["stopped"].startswith("stop time")


def test_the_stop_time_is_checked_before_each_tile(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    ticks = iter([datetime(2026, 1, 1, 0, 0), datetime(2026, 1, 1, 0, 1), datetime(2026, 1, 1, 9)])
    s = run_section(UNITS, functools.partial(_work, out_dir=tmp_path), manifest, tmp_path,
                    until=datetime(2026, 1, 1, 8), pause_file=tmp_path / "PAUSE",
                    clock=lambda: next(ticks))  # fmt: skip
    assert s["units_done_now"] == 2


def test_an_interrupted_or_damaged_tile_is_run_again(tmp_path):
    manifest, pause = tmp_path / "manifest.jsonl", tmp_path / "PAUSE"
    run_section(UNITS[:3], functools.partial(_work, out_dir=tmp_path), manifest, tmp_path,
                until=None, pause_file=pause)  # fmt: skip
    (tmp_path / "u1.out").write_text("damaged\n")  # a file that no longer matches its line
    (tmp_path / "u3.out.partial").write_text("half")  # a crash mid-tile: no line, no whole file
    assert done_units(manifest, tmp_path) == {"u0", "u2"}
    s = run_section(UNITS, functools.partial(_work, out_dir=tmp_path), manifest, tmp_path,
                    until=None, pause_file=pause)  # fmt: skip
    assert s["units_done_now"] == 4  # u1 again, then u3, u4, u5
    lines = [e for e in read_lines(manifest) if e["kind"] == "unit"]
    assert [e["unit"] for e in lines if e["redone"]] == ["u1"]
    assert (tmp_path / "u1.out").read_text() == "result of u1\n"


def _group(unit):
    return "g0" if unit in ("u0", "u1", "u2") else "g1"


def test_a_group_is_prepared_once_before_its_first_tile_and_cleaned_after_its_last(tmp_path):
    manifest, pause = tmp_path / "manifest.jsonl", tmp_path / "PAUSE"
    events = []
    work = functools.partial(_work, out_dir=tmp_path, pause_after="u1", pause_file=pause)
    run_section(UNITS, work, manifest, tmp_path, until=None, pause_file=pause, group_of=_group,
                prepare=lambda g: events.append(("prepare", g)),
                cleanup=lambda g: events.append(("cleanup", g)))  # fmt: skip
    assert events == [("prepare", "g0")]  # paused inside g0: not cleaned up yet
    pause.unlink()
    run_section(UNITS, functools.partial(_work, out_dir=tmp_path), manifest, tmp_path,
                until=None, pause_file=pause, group_of=_group,
                prepare=lambda g: events.append(("prepare", g)),
                cleanup=lambda g: events.append(("cleanup", g)))  # fmt: skip
    assert events == [("prepare", "g0"), ("prepare", "g0"), ("cleanup", "g0"),
                      ("prepare", "g1"), ("cleanup", "g1")]  # fmt: skip
    kinds = [e["kind"] for e in read_lines(manifest)]
    assert kinds.count("prepare") == 3 and kinds.count("cleanup") == 2


def test_two_workers_finish_every_tile_once(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    s = run_section(UNITS, functools.partial(_work, out_dir=tmp_path), manifest, tmp_path,
                    until=None, pause_file=tmp_path / "PAUSE", workers=2)  # fmt: skip
    assert s["units_done_now"] == 6
    assert sorted(e["unit"] for e in read_lines(manifest) if e["kind"] == "unit") == UNITS
    assert json.loads((tmp_path / "manifest.jsonl").read_text().splitlines()[-1])["kind"] == (
        "section"
    )


def test_until_is_the_next_occurrence_of_the_local_time():
    now = datetime(2026, 10, 7, 23, 0)
    assert next_stop("07:00", now) == datetime(2026, 10, 8, 7, 0)
    assert next_stop("23:30", now) == datetime(2026, 10, 7, 23, 30)

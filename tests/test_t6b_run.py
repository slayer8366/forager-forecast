"""T6b sectioned runner (D114): stop time, pause file, resume, redo of a damaged unit, groups."""

import functools
import hashlib
import json
from datetime import datetime, timedelta

import pytest

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


def test_a_prepare_that_asks_to_stop_ends_the_section_before_its_tiles(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    s = run_section(UNITS, functools.partial(_work, out_dir=tmp_path), manifest, tmp_path,
                    until=None, pause_file=tmp_path / "PAUSE", group_of=_group,
                    prepare=lambda g: {"stop_section": "download not finished"})  # fmt: skip
    assert s["units_done_now"] == 0 and s["stopped"] == "download not finished"


# Planner's call after night section 2 (RECORD -641): network errors retry with backoff, a tile
# that still fails is deferred and the section carries on; anything else still stops it.


def _flaky(unit, out_dir, fail_times=0, error="url", fail_unit=None):
    """Fails ``fail_times`` times (counted in a file) for ``fail_unit`` (or every unit)."""
    import urllib.error

    if fail_unit is None or unit == fail_unit:
        counter = out_dir / f"{unit}.attempts"
        n = int(counter.read_text()) if counter.exists() else 0
        counter.write_text(str(n + 1))
        if n < fail_times:
            if error == "url":
                raise urllib.error.URLError("Temporary failure in name resolution")
            if error == "http503":
                raise urllib.error.HTTPError("u", 503, "Service Unavailable", {}, None)
            if error == "http404":
                raise urllib.error.HTTPError("u", 404, "Not Found", {}, None)
            raise ValueError("a real bug")
    return _work(unit, out_dir)


def _section(tmp_path, work, units=UNITS, delays=(0, 0, 0), **kw):
    return run_section(units, work, tmp_path / "manifest.jsonl", tmp_path, until=None,
                       pause_file=tmp_path / "PAUSE", retry_delays=delays,
                       sleep=lambda s: None, **kw)  # fmt: skip


def test_a_network_error_is_retried_and_the_tile_then_succeeds(tmp_path):
    s = _section(tmp_path, functools.partial(_flaky, out_dir=tmp_path, fail_times=2,
                                             fail_unit="u1"))  # fmt: skip
    assert s["units_ok"] == 6 and s["units_deferred"] == 0
    line = [e for e in read_lines(tmp_path / "manifest.jsonl") if e.get("unit") == "u1"][0]
    assert line["status"] == "ok" and line["attempts"] == 3
    assert len(line["network_errors"]) == 2


def test_a_server_error_is_a_network_error_and_a_client_error_is_not(tmp_path):
    s = _section(tmp_path, functools.partial(_flaky, out_dir=tmp_path, fail_times=1,
                                             error="http503", fail_unit="u0"))  # fmt: skip
    assert s["units_ok"] == 6

    other = tmp_path / "x"
    other.mkdir()
    # A client error is not retried: since D122 it fails that unit, on its first attempt.
    s = _section(other, functools.partial(_flaky, out_dir=other, fail_times=1, error="http404",
                                          fail_unit="u0"))  # fmt: skip
    line = [e for e in read_lines(other / "manifest.jsonl") if e.get("unit") == "u0"][0]
    assert line["status"] == "failed" and line["attempts"] == 1
    assert line["error"].startswith("HTTPError") and s["units_deferred"] == 0


def test_a_tile_that_keeps_failing_is_deferred_and_the_section_carries_on(tmp_path):
    s = _section(tmp_path, functools.partial(_flaky, out_dir=tmp_path, fail_times=99,
                                             fail_unit="u2"))  # fmt: skip
    assert s["units_ok"] == 5 and s["units_deferred"] == 1 and s["units_remaining"] == 1
    lines = [e for e in read_lines(tmp_path / "manifest.jsonl") if e["kind"] == "unit"]
    deferred = [e for e in lines if e["status"] == "deferred"]
    assert [e["unit"] for e in deferred] == ["u2"] and "name resolution" in deferred[0]["error"]
    assert done_units(tmp_path / "manifest.jsonl", tmp_path) == set(UNITS) - {"u2"}
    # The next section takes the deferred tile first.
    s2 = _section(tmp_path, functools.partial(_flaky, out_dir=tmp_path))
    assert s2["units_ok"] == 1 and s2["units_remaining"] == 0
    assert [e["unit"] for e in read_lines(tmp_path / "manifest.jsonl")
            if e["kind"] == "unit"][-1] == "u2"  # fmt: skip


def test_the_next_section_retries_deferred_tiles_before_new_ones(tmp_path):
    _section(tmp_path, functools.partial(_flaky, out_dir=tmp_path, fail_times=99, fail_unit="u4"),
             units=UNITS[:5])  # fmt: skip
    _section(tmp_path, functools.partial(_flaky, out_dir=tmp_path))
    order = [e["unit"] for e in read_lines(tmp_path / "manifest.jsonl") if e["kind"] == "unit"]
    assert order == ["u0", "u1", "u2", "u3", "u4", "u4", "u5"]


# D122 (Forager RECORD -805, replacing the -642 call "non-network errors still stop it"): a unit
# whose work raises anything else fails on its own. Its line says "failed" with the message, the
# section carries on, and the unit is not done, so the next section tries it again.


@pytest.mark.parametrize("workers", [1, 2])
def test_a_non_network_error_fails_that_unit_and_the_section_carries_on(tmp_path, workers):
    work = functools.partial(_flaky, out_dir=tmp_path, fail_times=1, error="bug", fail_unit="u1")
    s = _section(tmp_path, work, workers=workers)
    assert s["units_ok"] == 5 and s["units_failed"] == 1 and s["units_deferred"] == 0
    assert s["units_remaining"] == 1 and "1 failed" in s["stopped"]
    lines = [e for e in read_lines(tmp_path / "manifest.jsonl") if e["kind"] == "unit"]
    failed = [e for e in lines if e["status"] == "failed"]
    assert [e["unit"] for e in failed] == ["u1"]
    assert failed[0]["error"] == "ValueError: a real bug" and failed[0]["files"] == {}
    assert "a real bug" in failed[0]["traceback"]
    assert done_units(tmp_path / "manifest.jsonl", tmp_path) == set(UNITS) - {"u1"}
    s2 = _section(tmp_path, functools.partial(_flaky, out_dir=tmp_path))
    assert s2["units_ok"] == 1 and s2["units_remaining"] == 0


def test_retries_stop_at_the_stop_time(tmp_path):
    waits = []
    t0 = datetime(2026, 1, 1, 0, 0)
    s = run_section(["u0"], functools.partial(_flaky, out_dir=tmp_path, fail_times=99),
                    tmp_path / "manifest.jsonl", tmp_path,
                    until=t0 + timedelta(minutes=3), pause_file=tmp_path / "PAUSE",
                    retry_delays=(30, 120, 300, 900), sleep=waits.append,
                    clock=lambda: t0)  # fmt: skip
    # 30 s and 120 s fit before the stop time; 300 s would pass it, so the tile is deferred.
    assert waits == [30, 120] and s["units_deferred"] == 1


def test_two_workers_defer_a_failing_tile_and_finish_the_rest(tmp_path):
    s = _section(tmp_path, functools.partial(_flaky, out_dir=tmp_path, fail_times=99,
                                             fail_unit="u3"), workers=2)  # fmt: skip
    assert s["units_ok"] == 5 and s["units_deferred"] == 1


def test_a_gdal_read_error_counts_as_network_only_when_it_is_one():
    from rasterio.errors import RasterioIOError

    from forager_forecast.t6b_run import is_network_error

    assert is_network_error(RasterioIOError("CURL error: Could not resolve host: files.isric.org"))
    assert is_network_error(RasterioIOError("/vsicurl/https://x/y.vrt: HTTP response code: 502"))
    assert not is_network_error(RasterioIOError("y.tif: not recognized as a supported file format"))
    assert not is_network_error(ValueError("cannot convert float NaN to integer"))

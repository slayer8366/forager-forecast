"""The flash drive's path is one setting (dispatch 2026-10-25-t6b-rebuild-check, item 1).

The drive holding T6b's store was reformatted (forecast RECORD 2026-09-28-2053, -2056) and now
mounts by its label at /run/media/zynergy-labs/forecast-data. Every script that runs reads the
drive's path from ``forager_forecast.drive``; no script or module under src/ names a mount itself.
"""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
OLD_UUID = "2ebd084f-5fdd-4730-8cef-96b267723190"
SETTING = ROOT / "src" / "forager_forecast" / "drive.py"
# Every script that read the old mount at t6b-progress-save 621421b (git grep for its UUID).
SCRIPTS = ("t6b_run", "t6b_fetch_sources", "t6b_fetch_scanfi_layers", "pnw_build", "pnw_checks")


def test_the_setting_is_the_new_drive_mount():
    from forager_forecast.drive import DRIVE

    assert DRIVE == Path("/run/media/zynergy-labs/forecast-data")


def test_no_code_that_runs_names_the_old_drive_or_any_mount_but_the_setting():
    hits = []
    for path in sorted([*(ROOT / "scripts").rglob("*"), *(ROOT / "src").rglob("*.py")]):
        if not path.is_file() or path == SETTING or "__pycache__" in path.parts:
            continue
        text = path.read_text(errors="replace")
        if OLD_UUID in text or "/run/media/" in text:
            hits.append(str(path.relative_to(ROOT)))
    assert hits == []


@pytest.mark.parametrize("name", SCRIPTS)
def test_each_script_takes_the_drive_from_the_setting(name):
    from forager_forecast.drive import DRIVE

    spec = importlib.util.spec_from_file_location(f"{name}_drive_check", ROOT / "scripts" /
                                                  f"{name}.py")  # fmt: skip
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.DRIVE == DRIVE
    if hasattr(mod, "T6B"):
        assert mod.T6B == DRIVE / "t6b"

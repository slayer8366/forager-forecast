"""A month the store delivers as a zip of several NetCDF files (variables split by expver
structure, seen for 2026-08) is merged into the one hourly file the route aggregates. No network."""

import sys
import zipfile
from pathlib import Path

import h5py
import numpy as np
import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pnw_split_delivery import merge_zip  # noqa: E402

T0 = 1785542400  # 2026-08-01T00:00Z


def _member(path: Path, hours: int, variables: dict, t0: int = T0) -> None:
    with h5py.File(path, "w") as h:
        h["valid_time"] = np.arange(t0, t0 + 3600 * hours, 3600, dtype=np.int64)
        h["valid_time"].attrs["units"] = np.bytes_("seconds since 1970-01-01")
        h["latitude"] = np.array([47.1, 47.0])
        h["longitude"] = np.array([-123.0, -122.9])
        for k, v in variables.items():
            h[k] = v


def _zip(tmp_path: Path, members: dict) -> Path:
    z = tmp_path / "month.zip"
    with zipfile.ZipFile(z, "w") as out:
        for name, path in members.items():
            out.write(path, name)
    return z


def test_split_members_merge_into_one_file_with_every_variable(tmp_path):
    rng = np.random.default_rng(5)
    shape = (48, 2, 2)
    soil = {"swvl1": rng.uniform(0.1, 0.4, shape), "stl1": rng.normal(284, 3, shape)}
    air = {"t2m": rng.normal(285, 4, shape)}
    _member(tmp_path / "a.nc", 48, soil)
    _member(tmp_path / "b.nc", 48, air)
    out = tmp_path / "merged.nc"
    members = merge_zip(_zip(tmp_path, {"data_0.nc": tmp_path / "a.nc",
                                        "data_1.nc": tmp_path / "b.nc"}), out)  # fmt: skip
    assert sorted(members) == ["data_0.nc", "data_1.nc"]
    with h5py.File(out) as h:
        assert h["valid_time"].attrs["units"].decode() == "seconds since 1970-01-01"
        for k, v in {**soil, **air}.items():
            np.testing.assert_array_equal(h[k][:], v)


def test_members_on_different_hours_are_refused(tmp_path):
    shape = (48, 2, 2)
    _member(tmp_path / "a.nc", 48, {"stl1": np.zeros(shape), "swvl1": np.zeros(shape)})
    _member(tmp_path / "b.nc", 48, {"t2m": np.zeros(shape)}, t0=T0 + 3600)
    z = _zip(tmp_path, {"data_0.nc": tmp_path / "a.nc", "data_1.nc": tmp_path / "b.nc"})
    with pytest.raises(SystemExit, match="hours"):
        merge_zip(z, tmp_path / "merged.nc")


def test_a_variable_missing_from_every_member_is_refused(tmp_path):
    shape = (48, 2, 2)
    _member(tmp_path / "a.nc", 48, {"stl1": np.zeros(shape)})
    _member(tmp_path / "b.nc", 48, {"t2m": np.zeros(shape)})
    z = _zip(tmp_path, {"data_0.nc": tmp_path / "a.nc", "data_1.nc": tmp_path / "b.nc"})
    with pytest.raises(SystemExit, match="swvl1"):
        merge_zip(z, tmp_path / "merged.nc")

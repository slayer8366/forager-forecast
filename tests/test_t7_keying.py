"""T7 items 1 and 3: master cell to weather cell (V11's path as code), and static effort."""

import csv
import math

import numpy as np
import pytest
from pyproj import Transformer

from forager_forecast.cells import Cell, cell_for
from forager_forecast.effort import EffortSurface, NoEffortValue, frame_weeks
from forager_forecast.grid import CELL_SIZE_M, GEOGRAPHIC_CRS, GRID_CRS, GridWindow
from forager_forecast.t6b_mask import cell_lonlat
from forager_forecast.t7.keying import (
    pack,
    pack_cell,
    static_effort,
    unpack,
    weather_cells,
    weather_cells_for_window,
)


def _window_at(lon, lat, n=3):
    x, y = Transformer.from_crs(GEOGRAPHIC_CRS, GRID_CRS, always_xy=True).transform(lon, lat)
    left = int(math.floor(x / CELL_SIZE_M)) * CELL_SIZE_M
    top = int(math.floor(y / CELL_SIZE_M)) * CELL_SIZE_M + CELL_SIZE_M
    return GridWindow(left, top - n * CELL_SIZE_M, left + n * CELL_SIZE_M, top)


def test_exact_decimal_ties_go_toward_plus_infinity_as_cell_for_does():
    # D63, D64: 47.05 and -123.05 are decimal ties; float rounding of x * 10 gets them wrong.
    lon = np.array([-123.05, -122.45, -123.0499999, 10.25])
    lat = np.array([47.05, 45.25, 47.0500001, -0.05])
    lat_t, lon_t = weather_cells(lon, lat)
    expected = [cell_for(a, o) for a, o in zip(lat, lon, strict=True)]
    assert list(zip(lat_t.tolist(), lon_t.tolist(), strict=True)) == [
        (c.lat_tenths, c.lon_tenths) for c in expected
    ]
    assert (int(lat_t[0]), int(lon_t[0])) == (471, -1230)
    assert (int(lat_t[1]), int(lon_t[1])) == (453, -1224)


def test_every_master_cell_of_a_window_keys_like_cell_for_on_its_centre():
    window = _window_at(-122.5, 45.5)
    lat_t, lon_t = weather_cells_for_window(window)
    assert lat_t.shape == (3, 3)
    lon, lat = cell_lonlat(window)
    for r in range(3):
        for c in range(3):
            cell = cell_for(float(lat[r, c]), float(lon[r, c]))
            assert (lat_t[r, c], lon_t[r, c]) == (cell.lat_tenths, cell.lon_tenths)
    assert {(int(a), int(o)) for a, o in zip(lat_t.ravel(), lon_t.ravel(), strict=True)} == {
        (455, -1225)
    }


def test_random_points_agree_with_cell_for():
    rng = np.random.default_rng(20260918)
    digits = rng.integers(1, 7, 3000)
    lon = np.array(
        [round(v, int(d)) for v, d in zip(rng.uniform(-125, -111, 3000), digits, strict=True)]
    )
    lat = np.array(
        [round(v, int(d)) for v, d in zip(rng.uniform(40, 49, 3000), digits, strict=True)]
    )
    lat_t, lon_t = weather_cells(lon, lat)
    for i in range(3000):
        c = cell_for(float(lat[i]), float(lon[i]))
        assert (lat_t[i], lon_t[i]) == (c.lat_tenths, c.lon_tenths), (lat[i], lon[i])


def test_pack_round_trips_and_is_distinct():
    lat_t = np.array([400, 400, 490, -50])
    lon_t = np.array([-1250, -1249, -1110, 1799])
    keys = pack(lat_t, lon_t)
    assert len(set(keys.tolist())) == 4
    back = unpack(keys)
    assert back[0].tolist() == lat_t.tolist() and back[1].tolist() == lon_t.tolist()
    assert pack_cell(Cell(400, -1249)) == int(keys[1])


def _surface(tmp_path):
    folder = tmp_path / "t6"
    folder.mkdir()
    with (folder / "cell_level.csv").open("w", newline="") as h:
        w = csv.writer(h)
        w.writerow(("cell_id", "lat_tenths", "lon_tenths", "band", "all_fungi", "lichen"))
        w.writerow(("455_-1225", 455, -1225, 450, "2.0", "1.0"))
        w.writerow(("456_-1225", 456, -1225, 450, "0.5", "1.0"))
    with (folder / "year_level.csv").open("w", newline="") as h:
        w = csv.writer(h)
        w.writerow(("year", "all_fungi", "lichen", "effort"))
        for y in range(2015, 2026):
            w.writerow((y, "1", "1", str(1.0 + (y - 2015) / 10)))
    with (folder / "season.csv").open("w", newline="") as h:
        w = csv.writer(h)
        w.writerow(("band", "slot", "iso_week", "all_fungi", "lichen", "effort"))
        for s in range(52):
            w.writerow((450, s, s + 1, "1", "1", str(0.5 + (s % 4) / 4)))
    with (folder / "day_type.csv").open("w", newline="") as h:
        w = csv.writer(h)
        w.writerow(("day_type", "days", "all_fungi_per_day", "lichen_per_day"))
        w.writerow(("weekend", 2, "0.3", "0.1"))
        w.writerow(("weekday", 5, "0.1", "0.1"))
    return EffortSurface.read(folder)


def test_static_effort_sums_the_surface_over_the_frame_weeks_and_refuses_outside(tmp_path):
    surface = _surface(tmp_path)
    inside, other, outside = Cell(455, -1225), Cell(456, -1225), Cell(300, -1000)
    result = static_effort(surface, [inside, other, outside])
    expected = sum(surface.effort(inside, w)[0] for w in frame_weeks())
    assert len(frame_weeks()) == 573
    assert result.total[inside] == pytest.approx(expected, rel=1e-12)
    assert result.total[other] == pytest.approx(expected / 4, rel=1e-12)
    assert result.log(inside) == pytest.approx(math.log(expected), rel=1e-12)
    assert outside not in result.total and result.refused == (outside,)
    with pytest.raises(NoEffortValue):
        result.log(outside)
    assert result.keys().tolist() == sorted([pack_cell(inside), pack_cell(other)])

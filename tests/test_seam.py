"""Border-seam transects (T5's Verify), on the plan stated in the verify report, section 4."""

import math

import numpy as np
import pytest
import rasterio
from pyproj import Geod
from rasterio.transform import from_origin

from forager_forecast.grid import CELL_SIZE_M, GRID_CRS
from forager_forecast.seam import (
    BORDER_LATITUDE,
    N_TRANSECTS,
    SAMPLES_PER_SIDE,
    WINDOWS_PER_SIDE,
    run_transects,
    sample_offsets_m,
    transect_longitudes,
    transect_steps,
    verdict,
    window_means,
)
from forager_forecast.t4_layer import LonLatBox, master_window

GEOD = Geod(ellps="WGS84")


def test_25_transects_5_km_apart_along_the_parallel_from_121_west():
    lons = transect_longitudes()
    assert len(lons) == N_TRANSECTS == 25
    assert lons[0] == -121.0
    assert lons[-1] == pytest.approx(-122.640, abs=0.001)
    # Ground distance between neighbours along 49 N is 5 km (short chords: geodesic ~ arc).
    for a, b in zip(lons, lons[1:], strict=False):
        _, _, d = GEOD.inv(a, BORDER_LATITUDE, b, BORDER_LATITUDE)
        assert d == pytest.approx(5000.0, rel=1e-4)


def test_samples_start_125_m_from_the_border_every_250_m_to_20_km():
    offsets = sample_offsets_m()
    assert len(offsets) == SAMPLES_PER_SIDE == 80
    assert offsets[0] == 125.0
    assert offsets[-1] == 125.0 + 250.0 * 79
    assert np.all(np.diff(offsets) == 250.0)


def test_a_window_is_the_mean_of_four_samples_and_missing_if_any_is_missing():
    values = np.arange(80, dtype=float)
    values[5] = np.nan
    means = window_means(values)
    assert len(means) == WINDOWS_PER_SIDE == 20
    assert means[0] == pytest.approx(1.5)
    assert np.isnan(means[1])
    assert means[2] == pytest.approx(9.5)


def test_steps_are_canada_minus_us_at_the_border_and_neighbours_inside_each_country():
    south = np.full(80, 0.2)
    north = np.full(80, 0.5)
    south[4:8] = 0.3  # US window 1
    border, within_us, within_ca = transect_steps(north, south)
    assert border == pytest.approx(0.3)
    assert len(within_us) == len(within_ca) == 19
    assert within_us[0] == pytest.approx(0.2 - 0.3)
    assert within_us[1] == pytest.approx(0.3 - 0.2)
    assert np.allclose(within_ca, 0.0)


def test_the_verdict_names_a_step_larger_than_the_variation_inside_both_countries():
    rng = np.random.default_rng(1)
    within_us = rng.normal(0, 0.02, (25, 19))
    within_ca = rng.normal(0, 0.02, (25, 19))
    big = verdict(np.full(25, 0.2), within_us, within_ca)
    assert big["artifact"] is True
    assert big["border_median_abs"] == pytest.approx(0.2)
    assert big["ratio"] > 5
    lo, hi = big["border_mean_signed_ci95"]
    assert lo == pytest.approx(0.2) and hi == pytest.approx(0.2)
    assert big["n_transects"] == 25


def test_with_no_step_the_verdict_fires_about_one_time_in_twenty_or_less():
    # The threshold is the 95th percentile of the null (medians of one within-country step per
    # transect, drawn at random), taken on the side with the larger one. Under no step, at most
    # about 5% of draws should be called artifacts.
    rng = np.random.default_rng(7)
    fired = 0
    trials = 200
    for _ in range(trials):
        within_us = rng.normal(0, 0.03, (25, 19))
        within_ca = rng.normal(0, 0.03, (25, 19))
        border = rng.normal(0, 0.03, 25)
        fired += verdict(border, within_us, within_ca, resamples=400)["artifact"]
    assert fired / trials <= 0.08


def test_a_transect_with_no_valid_border_window_is_left_out_and_counted():
    within = np.zeros((3, 19))
    result = verdict(np.array([0.1, np.nan, 0.1]), within, within)
    assert result["n_transects"] == 2


def _write_master(path, box, value_north, value_south):
    window = master_window(box)
    transform = from_origin(window.left, window.top, CELL_SIZE_M, CELL_SIZE_M)
    xs = window.left + (np.arange(window.width) + 0.5) * CELL_SIZE_M
    ys = window.top - (np.arange(window.height) + 0.5) * CELL_SIZE_M
    gx, gy = np.meshgrid(xs, ys)
    from pyproj import Transformer

    lon, lat = Transformer.from_crs(GRID_CRS, "EPSG:4269", always_xy=True).transform(gx, gy)
    band = np.where(lat >= BORDER_LATITUDE, value_north(lat, lon), value_south(lat, lon))
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=window.width,
        height=window.height,
        count=1,
        dtype="float32",
        crs=GRID_CRS,
        transform=transform,
        nodata=float("nan"),
    ) as dst:
        dst.write(band.astype("float32"), 1)
        dst.set_band_description(1, "share_Pseudotsuga")


BOX = LonLatBox(south=48.70, north=49.30, west=-122.80, east=-120.95)


def test_transects_through_a_master_raster_find_a_planted_step(tmp_path):
    path = tmp_path / "master.tif"
    # A smooth north-south gradient plus a 0.15 jump at the border.
    _write_master(
        path,
        BOX,
        lambda lat, lon: 0.5 + 0.1 * (lat - 49) + 0.15,
        lambda lat, lon: 0.5 + 0.1 * (lat - 49),
    )
    results = run_transects(path, ["share_Pseudotsuga"])
    r = results["share_Pseudotsuga"]
    assert r["artifact"] is True
    assert r["border_median_abs"] == pytest.approx(0.15, abs=0.01)
    assert r["n_transects"] == 25


def test_transects_through_a_uniform_master_raster_find_no_step(tmp_path):
    path = tmp_path / "master.tif"
    f = lambda lat, lon: np.full_like(lat, 0.4)  # noqa: E731
    _write_master(path, BOX, f, f)
    r = run_transects(path, ["share_Pseudotsuga"])["share_Pseudotsuga"]
    assert r["artifact"] is False
    assert r["border_median_abs"] == pytest.approx(0.0, abs=1e-6)
    assert math.isfinite(r["within_us_median_abs"])

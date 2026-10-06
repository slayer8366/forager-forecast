"""T5's Verify: transects across the British Columbia and Washington border on the master grid.

The plan was stated before any value was read (docs/audits/2026-10-06-t5-verify-report.md,
section 4, with the verdict rule as amended in section 7 of that report):

- 25 meridian transects, from 121.0 W westward every 5 km of ground along 49 N.
- 80 samples per side, 125 m + 250 m j (j = 0..79) north and south of 49 N along the meridian,
  each reading the master cell that holds it.
- 1 km windows of four samples, missing if any sample is missing.
- Border step, Canada minus US: W0(north) - W0(south). Within-country steps: W_k - W_k+1,
  k = 0..18, on each side.
- Verdict: B = median over transects of |border step|. The null for each side is the median over
  the same transects (those with a border step, D90) of one |within step| per transect, drawn at
  random (seed 20260918, D31); the threshold is the larger side's 95th percentile. B above it is
  a step larger than the variation inside each country, and is written up as a known artifact.
  Before D90 the null used every transect with a within-country step.
"""

import math
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Geod

from forager_forecast.grid import CELL_SIZE_M, GridWindow, cell_for_lonlat

BORDER_LATITUDE = 49.0
EAST_LONGITUDE = -121.0
N_TRANSECTS = 25
TRANSECT_SPACING_M = 5000.0
SAMPLES_PER_SIDE = 80
FIRST_OFFSET_M = 125.0
SAMPLE_STEP_M = 250.0
WINDOW_SAMPLES = 4
WINDOWS_PER_SIDE = SAMPLES_PER_SIDE // WINDOW_SAMPLES
SEED = 20260918
NULL_QUANTILE = 95.0

_GEOD = Geod(ellps="WGS84")


def transect_longitudes() -> list[float]:
    """Meridians 5 km apart along the 49 N parallel (WGS84 parallel radius), from 121 W west."""
    a = _GEOD.a
    e2 = _GEOD.es
    phi = math.radians(BORDER_LATITUDE)
    parallel_radius = a / math.sqrt(1 - e2 * math.sin(phi) ** 2) * math.cos(phi)
    step_deg = math.degrees(TRANSECT_SPACING_M / parallel_radius)
    return [EAST_LONGITUDE - k * step_deg for k in range(N_TRANSECTS)]


def sample_offsets_m() -> np.ndarray:
    return FIRST_OFFSET_M + SAMPLE_STEP_M * np.arange(SAMPLES_PER_SIDE)


def sample_latitudes(longitude: float) -> tuple[np.ndarray, np.ndarray]:
    """(north, south) sample latitudes along the meridian, geodesic distances from 49 N."""
    d = sample_offsets_m()
    n = len(d)
    lon = np.full(n, longitude)
    lat0 = np.full(n, BORDER_LATITUDE)
    _, north, _ = _GEOD.fwd(lon, lat0, np.zeros(n), d)
    _, south, _ = _GEOD.fwd(lon, lat0, np.full(n, 180.0), d)
    return np.asarray(north), np.asarray(south)


def window_means(values: np.ndarray) -> np.ndarray:
    v = np.asarray(values, dtype="float64").reshape(WINDOWS_PER_SIDE, WINDOW_SAMPLES)
    return v.mean(axis=1)  # NaN propagates: a window with any missing sample is missing


def transect_steps(north: np.ndarray, south: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    wn = window_means(north)
    ws = window_means(south)
    return float(wn[0] - ws[0]), ws[:-1] - ws[1:], wn[:-1] - wn[1:]


def _null_threshold(within: np.ndarray, rng: np.random.Generator, resamples: int) -> float:
    within = np.abs(np.asarray(within, dtype="float64"))
    rows = [row[np.isfinite(row)] for row in within]
    rows = [row for row in rows if len(row)]
    if not rows:
        return float("nan")
    draws = np.empty(resamples)
    for r in range(resamples):
        draws[r] = np.median([row[rng.integers(len(row))] for row in rows])
    return float(np.percentile(draws, NULL_QUANTILE))


def verdict(border, within_us, within_ca, resamples: int = 10000) -> dict:
    border = np.asarray(border, dtype="float64")
    ok = np.isfinite(border)
    b = border[ok]
    rng = np.random.default_rng(SEED)
    wus = np.abs(np.asarray(within_us, dtype="float64"))
    wca = np.abs(np.asarray(within_ca, dtype="float64"))
    # D90: the null uses the same transects as B (matched counts), not every transect with a
    # within-country step. The filed rule (verify report section 7) used all of them.
    matched_us = wus[ok] if wus.ndim == 2 else wus
    matched_ca = wca[ok] if wca.ndim == 2 else wca
    threshold_us = _null_threshold(matched_us, rng, resamples)
    threshold_ca = _null_threshold(matched_ca, rng, resamples)
    threshold = max(threshold_us, threshold_ca)
    big = float(np.median(np.abs(b))) if len(b) else float("nan")
    v_us = float(np.nanmedian(wus)) if np.isfinite(wus).any() else float("nan")
    v_ca = float(np.nanmedian(wca)) if np.isfinite(wca).any() else float("nan")
    if len(b):
        boot = rng.choice(b, size=(resamples, len(b)), replace=True).mean(axis=1)
        ci = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
    else:
        ci = [float("nan"), float("nan")]
    denom = max(v_us, v_ca)
    return {
        "n_transects": int(len(b)),
        "border_median_abs": big,
        "border_mean_signed": float(b.mean()) if len(b) else float("nan"),
        "border_mean_signed_ci95": ci,
        "within_us_median_abs": v_us,
        "within_ca_median_abs": v_ca,
        "within_us_p95_abs": float(np.nanpercentile(wus, 95)) if np.isfinite(wus).any() else None,
        "within_ca_p95_abs": float(np.nanpercentile(wca, 95)) if np.isfinite(wca).any() else None,
        "null_rows_us": int(sum(np.isfinite(row).any() for row in matched_us)),
        "null_rows_ca": int(sum(np.isfinite(row).any() for row in matched_ca)),
        "null_threshold_us": threshold_us,
        "null_threshold_ca": threshold_ca,
        "threshold": threshold,
        "ratio": big / denom if denom > 0 else float("inf") if big > 0 else 0.0,
        "artifact": bool(len(b) and math.isfinite(threshold) and big > threshold),
    }


def _sampler(path: Path):
    ds = rasterio.open(path)
    t = ds.transform
    left, top = int(round(t.c)), int(round(t.f))
    window = GridWindow(left, top - ds.height * CELL_SIZE_M, left + ds.width * CELL_SIZE_M, top)
    return ds, window


def run_transects(master_path: Path, band_names: list[str]) -> dict:
    """Sample every named band of a master-grid GeoTIFF along the transects; verdict per band."""
    ds, window = _sampler(Path(master_path))
    with ds:
        names = list(ds.descriptions)
        data = {name: ds.read(names.index(name) + 1).astype("float64") for name in band_names}
    lons = transect_longitudes()
    results = {}
    for name in band_names:
        band = data[name]

        def read(lon, lats, band=band):
            out = np.full(len(lats), np.nan)
            for i, lat in enumerate(lats):
                try:
                    r, c = window.pixel_of_cell(cell_for_lonlat(lon, float(lat)))
                except IndexError:
                    continue
                out[i] = band[r, c]
            return out

        border, w_us, w_ca = [], [], []
        for lon in lons:
            north_lat, south_lat = sample_latitudes(lon)
            b, wu, wc = transect_steps(read(lon, north_lat), read(lon, south_lat))
            border.append(b)
            w_us.append(wu)
            w_ca.append(wc)
        result = verdict(np.array(border), np.array(w_us), np.array(w_ca))
        result["border_steps"] = [None if not math.isfinite(x) else x for x in border]
        result["transect_longitudes"] = lons
        results[name] = result
    return results

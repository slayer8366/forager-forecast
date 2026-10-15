"""Rain gap between Open-Meteo era5_seamless and the store's ERA5 rain (Forager RECORD -828).

Run:  uv run python scripts/rain_gap_analysis.py --store <cds dir> --om <feature-check dir>
          --out <json>

Reads only what is on disk, makes no request:
- the store's hourly ERA5 total_precipitation, `hourly-era5-precip-2019-2020.nc` (metres per hour,
  stamped at the end of the hour it accumulates; the builder's convention, confirmed against the
  daily-sum product at pnw-pilot-t1 267e3ad: UTC day d = stamps d 01:00 to d+1 00:00);
- Open-Meteo bodies from the scoring branch's feature check: daily `precipitation_sum` for 6 cells
  over 2019-07-09 to 2019-10-06, and hourly `precipitation` for one of them (47.8, -121.2) over
  2019-07-08 to 2019-10-07.

Each Open-Meteo cell is compared with the store's 0.25 degree point nearest the cell centre
(cells.quarter_cell_for, D46), which the feature check found to match better than any neighbour.

Variants of the store's daily total, each compared with Open-Meteo's daily total:
  S1  store convention (stamps 01..24), exact            = the training value
  S0  stamps 00..23, exact                               = hour-boundary offset only
  S1q store convention, each hour rounded to 0.1 mm      = quantisation only
  S0q stamps 00..23, each hour rounded to 0.1 mm         = both
  S0t stamps 00..23, each hour 0 below 0.1 mm else rounded to 0.1 mm (the rule observed hour by
      hour at the one cell with Open-Meteo hourly; tested here on all six cells' daily totals)
  S1t the same rule, store convention
And for the one cell with Open-Meteo hourly: Open-Meteo hourly summed over stamps 00..23 and
01..24, against Open-Meteo's own daily total and the store's.
"""

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import h5py
import numpy as np

from forager_forecast.cells import quarter_cell_for

ROUND_MM = 0.1


def store_hourly(path: Path):
    with h5py.File(path) as h:
        stamps = h["valid_time"][:].astype(np.int64)
        lat = np.round(h["latitude"][:] * 4).astype(int)
        lon = np.round(h["longitude"][:] * 4).astype(int)
        tp = h["tp"][:].astype(np.float64) * 1000.0  # mm per hour
    return stamps, lat, lon, tp


def series_at(stamps, lat, lon, tp, lat_q, lon_q):
    i = int(np.where(lat == lat_q)[0][0])
    j = int(np.where(lon == lon_q)[0][0])
    return {int(s): float(v) for s, v in zip(stamps, tp[:, i, j], strict=True)}


def epoch(day: date, hour: int) -> int:
    return int(datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp()) + hour * 3600


def open_meteo_like(v: float) -> float:
    """What Open-Meteo's hourly value was observed to be for a store value v (mm): 0 below 0.1 mm,
    else v rounded to 0.1 mm. Fitted on one cell's 2,208 hours (all equal); see the report."""
    return 0.0 if v < 0.1 else float(np.round(v / ROUND_MM) * ROUND_MM)


def day_sum(hourly: dict[int, float], day: date, first_hour: int, rounding) -> float:
    vals = [hourly[epoch(day, h)] for h in range(first_hour, first_hour + 24)]
    if rounding == "threshold":
        vals = [open_meteo_like(v) for v in vals]
    elif rounding:
        vals = [np.round(v / ROUND_MM) * ROUND_MM for v in vals]
    return float(sum(vals))


def stats(a: np.ndarray, b: np.ndarray) -> dict:
    """b against a (Open-Meteo): differences b - a."""
    d = b - a
    return {
        "days": int(len(d)),
        "max_abs_mm": round(float(np.max(np.abs(d))), 3),
        "mean_abs_mm": round(float(np.mean(np.abs(d))), 4),
        "days_within_0_05mm": int(np.sum(np.abs(d) <= 0.05 + 1e-9)),
        "total_a_mm": round(float(a.sum()), 2),
        "total_b_mm": round(float(b.sum()), 2),
        "total_gap_pct_of_b": round(float((b.sum() - a.sum()) / b.sum() * 100), 2)
        if b.sum()
        else None,
        "days_a_zero_b_positive": int(np.sum((a == 0) & (b > 0))),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", type=Path, required=True)
    ap.add_argument("--om", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    stamps, lat, lon, tp = store_hourly(a.store / "hourly-era5-precip-2019-2020.nc")
    body = json.loads((a.om / "open-meteo-2019-10-07.json").read_text())
    result = {"cells": {}, "pooled": {}}
    pooled = {k: ([], []) for k in ("S1", "S0", "S1q", "S0q", "S0t", "S1t")}
    for loc in body:
        q = quarter_cell_for(loc["latitude"], loc["longitude"])
        hourly = series_at(stamps, lat, lon, tp, q.lat_quarters, q.lon_quarters)
        days = [date.fromisoformat(t) for t in loc["daily"]["time"]]
        om = np.array(loc["daily"]["precipitation_sum"], dtype=float)
        variants = {
            "S1": np.array([day_sum(hourly, d, 1, False) for d in days]),
            "S0": np.array([day_sum(hourly, d, 0, False) for d in days]),
            "S1q": np.array([day_sum(hourly, d, 1, True) for d in days]),
            "S0q": np.array([day_sum(hourly, d, 0, True) for d in days]),
            "S0t": np.array([day_sum(hourly, d, 0, "threshold") for d in days]),
            "S1t": np.array([day_sum(hourly, d, 1, "threshold") for d in days]),
        }
        key = f"{loc['latitude']:.1f},{loc['longitude']:.1f} (q{q.lat_quarters}_{q.lon_quarters})"
        result["cells"][key] = {k: stats(om, v) for k, v in variants.items()}
        for k, v in variants.items():
            pooled[k][0].append(om)
            pooled[k][1].append(v)
    for k, (oms, vs) in pooled.items():
        result["pooled"][k] = stats(np.concatenate(oms), np.concatenate(vs))

    # Open-Meteo hourly at one cell.
    h = json.loads((a.om / "om-hourly-precip-478_-1212.json").read_text())
    om_h = {
        int(datetime.fromisoformat(t).replace(tzinfo=UTC).timestamp()): float(v)
        for t, v in zip(h["hourly"]["time"], h["hourly"]["precipitation"], strict=True)
        if v is not None
    }
    cell = next(x for x in body if abs(x["latitude"] - 47.8) < 1e-3)
    days = [date.fromisoformat(t) for t in cell["daily"]["time"]]
    om_daily = np.array(cell["daily"]["precipitation_sum"], dtype=float)
    q = quarter_cell_for(47.8, -121.2)
    st = series_at(stamps, lat, lon, tp, q.lat_quarters, q.lon_quarters)
    om00 = np.array([day_sum(om_h, d, 0, False) for d in days])
    om01 = np.array([day_sum(om_h, d, 1, False) for d in days])
    store1 = np.array([day_sum(st, d, 1, False) for d in days])
    # Hour by hour: Open-Meteo's hourly value against the store's at the same stamp.
    common = sorted(set(om_h) & set(st) & {epoch(d, hh) for d in days for hh in range(1, 25)})
    o = np.array([om_h[s] for s in common])
    s_exact = np.array([st[s] for s in common])
    s_round = np.round(s_exact / ROUND_MM) * ROUND_MM
    lag = {}
    for shift in (-1, 0, 1):
        pairs = [(om_h[s], st[s + shift * 3600]) for s in common if s + shift * 3600 in st]
        x, y = np.array(pairs).T
        lag[str(shift)] = {
            "max_abs_mm": round(float(np.max(np.abs(x - y))), 4),
            "mean_abs_mm": round(float(np.mean(np.abs(x - y))), 5),
        }
    every = sorted(set(om_h) & set(st))
    rule = np.array([open_meteo_like(st[x]) for x in every])
    om_all = np.array([om_h[x] for x in every])
    result["threshold_rule_hour_by_hour"] = {
        "rule": "0 below 0.1 mm, else the store's hourly value rounded to 0.1 mm",
        "hours": len(every),
        "equal": int(np.sum(np.abs(om_all - rule) < 1e-6)),
        "store_total_mm": round(float(sum(st[x] for x in every)), 2),
        "hours_store_between_0_and_0_1": int(sum(1 for x in every if 0 < st[x] < 0.1)),
        "rain_in_those_hours_mm": round(float(sum(st[x] for x in every if 0 < st[x] < 0.1)), 2),
        "om_zero_in_those_hours": int(sum(1 for x in every if 0 < st[x] < 0.1 and om_h[x] == 0)),
        "alternatives_equal": {
            str(t): int(
                np.sum(
                    np.abs(
                        om_all
                        - np.array(
                            [
                                0.0 if st[x] < t else np.round(st[x] / ROUND_MM) * ROUND_MM
                                for x in every
                            ]
                        )
                    )
                    < 1e-6
                )
            )
            for t in (0.05, 0.08, 0.09, 0.11)
        },
    }
    result["open_meteo_hourly_47.8_-121.2"] = {
        "om_daily_vs_om_hourly_00_23": stats(om_daily, om00),
        "om_daily_vs_om_hourly_01_24": stats(om_daily, om01),
        "store_daily_vs_om_hourly_01_24": stats(om01, store1),
        "store_daily_vs_om_hourly_00_23": stats(om00, store1),
        "hours_compared": len(common),
        "hourly_store_shift_vs_om": lag,
        "hourly_om_equals_store_rounded_0_1": int(np.sum(np.abs(o - s_round) < 1e-6)),
        "hourly_om_minus_store_exact_total_mm": round(float(o.sum() - s_exact.sum()), 2),
        "hourly_om_minus_store_rounded_total_mm": round(float(o.sum() - s_round.sum()), 2),
        "hours_store_positive_below_0_05": int(np.sum((s_exact > 0) & (s_exact < 0.05))),
        "rain_in_those_hours_mm": round(float(s_exact[(s_exact > 0) & (s_exact < 0.05)].sum()), 2),
        "hours_om_zero_store_positive": int(np.sum((o == 0) & (s_exact > 0))),
        "om_hourly_decimals_seen": sorted({len(f"{v:.3f}".rstrip("0").split(".")[1]) for v in o}),
    }
    a.out.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

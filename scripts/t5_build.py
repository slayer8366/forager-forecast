"""T5 end to end on real data: SCANFI window fetch, TreeMap cut, master grid, transects.

Usage (from the repository root, data/t5 pointing at the flash drive):
    uv run --frozen python scripts/t5_build.py STEP [BUILD]
STEP is fetch-scanfi, fetch-scanfi-total, cut-treemap, build, or transects. BUILD names the
build: d92 (default: TreeMap canopy, SCANFI's own total, D88 and D92), treemap_canopy (D88 with
the ten-class Canadian total) or tree_list (the first build). An optional scale=S (repeatable)
limits build to those surrogate width scales, so each scale can run as its own process and hold
only one strip in memory (Amendment 3 re-run, after an out-of-memory kill). Transects always
use the current verdict rule (D90); the build's layers are read from its own folder. Inputs and
outputs live under data/t5; request records are copied to docs/pulls/ by hand after a fetch.
"""

import json
import sys
import time
from pathlib import Path

from forager_forecast.crown_cover import BANDS
from forager_forecast.seam import run_transects
from forager_forecast.t5_layer import (
    SCANFI_TOTAL_LAYER,
    STRIP,
    SURROGATE_SCALES,
    build_master,
    cut_treemap,
    fetch_scanfi,
)

DATA = Path("data/t5")
NATIVE = DATA / "native"
TREEMAP = DATA / "treemap2023"
TESTED = ["share_Pseudotsuga", "share_conifer", "share_broadleaf", "total_cover_pct"]


BUILDS = {
    "d92": ("treemap_canopy", "scanfi_att_closure"),
    "treemap_canopy": ("treemap_canopy", "ten_class_sum"),
    "tree_list": ("tree_list", "ten_class_sum"),
}
BUILD = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] in BUILDS else "d92"
US_TOTAL, CA_TOTAL = BUILDS[BUILD]
ONLY_SCALES = tuple(float(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("scale="))


def out_dir(scale: float) -> Path:
    return DATA / f"master_{BUILD}_scale_{scale}"


def main(steps: list[str]) -> None:
    steps = [s for s in steps if s not in BUILDS and not s.startswith("scale=")]
    if not DATA.resolve().is_dir():
        raise SystemExit(f"{DATA} does not resolve to a directory (is the flash drive mounted?)")
    for step in steps:
        started = time.perf_counter()
        if step == "fetch-scanfi":
            print(fetch_scanfi(NATIVE, STRIP))
        elif step == "fetch-scanfi-total":
            print(
                fetch_scanfi(
                    NATIVE, STRIP, layers=(SCANFI_TOTAL_LAYER,),
                    request_name="scanfi_total_request.json",
                )
            )  # fmt: skip
        elif step == "cut-treemap":
            print(
                cut_treemap(
                    NATIVE, STRIP, TREEMAP / "TreeMap2023_CONUS.tif", TREEMAP / "RDS-2026-0038.zip"
                )
            )
        elif step == "build":
            for scale in ONLY_SCALES or SURROGATE_SCALES:
                if scale not in SURROGATE_SCALES:
                    raise SystemExit(f"scale {scale} is not one of {SURROGATE_SCALES}")
                summary = build_master(
                    NATIVE,
                    out_dir(scale),
                    STRIP,
                    surrogate_width_scale=scale,
                    us_total=US_TOTAL,
                    ca_total=CA_TOTAL,
                )
                print(scale, json.dumps(summary["cells_with_share"]))
        elif step == "transects":
            results = {}
            for scale in SURROGATE_SCALES:
                bands = TESTED if scale == 1.0 else TESTED[:3]
                results[str(scale)] = run_transects(out_dir(scale) / "host_trees_strip.tif", bands)
            results["untestable"] = {
                f"share_{b}": "not available on the Canadian side (D85)"
                for b in BANDS
                if b not in ("Pseudotsuga", "conifer", "broadleaf")
            }
            (DATA / f"transects_{BUILD}_d90.json").write_text(json.dumps(results, indent=2) + "\n")
            for band, r in results["1.0"].items():
                print(band, {k: r[k] for k in ("n_transects", "border_median_abs", "threshold",
                                                "ratio", "artifact")})  # fmt: skip
        else:
            raise SystemExit(f"unknown step {step}")
        print(f"{step}: {time.perf_counter() - started:.1f} s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])

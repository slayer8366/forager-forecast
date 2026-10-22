"""T8's fits, one part per run, under the owner's second word (plan section 9, item 3; D133 (8)).
The work is forager_forecast.t8.fit. Never beside t6b-night: it must have finished or be paused.

Run, only once the owner's word to fit is relayed and every fit reading is ruled
(design.require_ruled refuses otherwise), one part at a time, the bar first:

    systemd-run --user --unit=t8-fit-<design>-<part> -p MemoryMax=3G -p MemorySwapMax=0 \\
        -p Nice=10 --working-directory=$PWD .venv/bin/python scripts/t8_fit.py \\
        --design t1_1000m --part bar --count ~/Zynergy/forecast-data/t8/count \\
        --out ~/Zynergy/forecast-data/t8/fit

Parts: bar, forecast, alone, challenger (after bar), ecoregion; the sensitivity designs t1_5000m and
t1_1000m_cc run "bar" only, labelled no verdict (design.PENDING M-sensitivity, proposed). Each
design reads the weather file T1 itself recorded, and T6's track per M-sensitivity-effort
(proposed): "cc" for t1_1000m_cc, "all" otherwise. Refuses with uncommitted tracked files, and
refuses to write a part that already has output.
"""

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from forager_forecast import effort as ef
from forager_forecast import t1_model as tm
from forager_forecast.t8 import design
from forager_forecast.t8 import effort_term as et
from forager_forecast.t8 import fit as tf

REPO = Path(__file__).resolve().parents[1]
PILOT = Path.home() / "Zynergy/forecast-data-pnw-pilot"
COUNTS = Path.home() / "Zynergy/forecast-data/t6-counts"
T6_AUDIT = REPO / "docs/audits/2026-10-06-t6-fit"
GRID_FILE = REPO / "docs/audits/2026-10-10-pnw-pilot-t1/tuning_grid.json"
CEC_RECORD = REPO / "docs/pulls/t6b-cec-terrestrial-ecoregions-l3.request.json"
CEC_ZIP = Path(
    "/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b/sources/"
    "cec_ecoregions_l3.zip"
)
SCRATCH = Path("/mnt/work/scratch/t8-fit")


def log(msg: str) -> None:
    print(f"{datetime.now(UTC).isoformat(timespec='seconds')} {msg}", flush=True)


def code_state() -> tuple[str, str]:
    def git(*a: str) -> str:
        return subprocess.run(
            ["git", *a], capture_output=True, text=True, check=True, cwd=REPO
        ).stdout.strip()

    return git("rev-parse", "HEAD"), git("status", "--porcelain", "--untracked-files=no")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", choices=list(design.T1_LISTS), required=True)
    ap.add_argument("--part", choices=list(tf.PARTS), required=True)
    ap.add_argument("--count", type=Path, required=True, help="the count's output folder")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--threads", type=int, default=4)
    args = ap.parse_args()
    commit, dirty = code_state()
    if dirty:
        raise SystemExit(f"tracked files are uncommitted; commit before fitting:\n{dirty}")
    if args.design != design.HEADLINE_LIST and args.part != "bar":
        raise SystemExit("the sensitivity designs run the bar part only (M-sensitivity)")
    if (args.out / f"{args.design}_{args.part}.json").exists():
        raise SystemExit(f"{args.design} {args.part} already has output in {args.out}")
    stem = design.T1_LISTS[args.design][0]
    t1_summary = json.loads((PILOT / "fits" / f"{stem}.json").read_text())
    track = "cc" if args.design == "t1_1000m_cc" else "all"
    results = T6_AUDIT / f"{track}_results.json"
    prep = tf.prepare(
        args.design,
        PILOT / "fits" / f"{stem}.npz",
        args.count / f"lichen_{args.design}.npz",
        Path(t1_summary["weather_npz"]),
        COUNTS,
        track,
        results,
        log,
    )
    kwargs: dict = {}
    if args.part == "challenger":
        configs = tm.tuning_configurations()
        if json.loads(GRID_FILE.read_text())["configurations"] != configs:
            raise SystemExit("the committed tuning grid differs from tuning_configurations()")

        def fitter(config, train_x, train_y, test_x):
            return tm.fit_predict(config, train_x, train_y, test_x, args.threads)

        kwargs = {"fitter": fitter, "configs": configs}
    elif args.part == "ecoregion":
        cec_sha = json.loads(CEC_RECORD.read_text())["sha256"]
        blocks, shared = tf.unit_blocks(prep, CEC_ZIP, cec_sha, SCRATCH / "cec")
        log(f"ecoregions: {len(set(blocks.tolist()))} blocks, {shared} centres claimed twice")
        final = et.parse_config(json.loads(results.read_text())["final_configuration"])
        fungi = et.read_counts(COUNTS, f"{track}_fungi.npz")
        lichen = et.read_counts(COUNTS, f"{track}_lichen.npz")
        effort = et.all_years_effort(fungi, lichen, final, prep.t1.cells, prep.t1.mondays)
        kwargs = {"blocks": blocks, "block_effort": effort}
    result = tf.run_part(args.part, prep, args.out, log=log, **kwargs)
    path = args.out / f"{args.design}_{args.part}.json"
    data = json.loads(path.read_text())
    data["commit"] = commit
    data["years"] = list(ef.YEARS)
    path.write_text(json.dumps(data, indent=2, default=float) + "\n")
    log(f"{args.design} {args.part} done in {result['seconds']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())

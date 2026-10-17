"""T7 part C: the saprotroph group's presences that would enter a fit, per level III block, beside
the mycorrhizal main group's, read through the fit's own table assembly (``scripts/t7_fit.py``
``Data``: P4's cell codes and T6's effort frame, D147's population) on the 2026-10-17 fit's work
dir. Read only: no model is trained, nothing is written outside this folder. A record of what
ran, not part of any run.

Usage: python entering_by_block.py <repo root>   (writes entering_by_block.json beside itself)

For each group: presences entering, genera counting alone and the pool under D144 rule 4 on that
population (D147), presences per block, and which forested blocks (D139, 15% cut) reach the
30-presence minimum (D139) for their own score."""

import json
import sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "scripts"))
import t7_fit as tf  # noqa: E402

from forager_forecast.t7 import folds as fd  # noqa: E402
from forager_forecast.t7.presences import POOLED  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = Path("/mnt/work/Zynergy/forecast-data/t7/fit")
GROUPS = {
    "mycorrhizal main (V9)": tf.V9 / "presences_main.csv",
    "saprotroph main": Path("/mnt/work/Zynergy/forecast-data/t7/v9c/presences_saprotroph_main.csv"),
    "saprotroph side": Path("/mnt/work/Zynergy/forecast-data/t7/v9c/presences_saprotroph_side.csv"),
}
out: dict = {"work": str(WORK), "minimum_per_block": fd.MIN_PRESENCES_INFORMATIVE,
             "forested_cut": fd.FORESTED_CUT, "groups": {}}  # fmt: skip
for name, path in GROUPS.items():
    d = tf.Data(WORK, path)
    forested_all, in_fit, forested, _ = tf.forested_selection(d)
    names = {e["code"]: f"{e['level3']} {e['name']}" for e in d.meta["level3_table"]}
    pres_blocks = d.blocks[d.y == 1]
    per_block = {int(b): int((pres_blocks == b).sum()) for b in sorted(in_fit | forested_all)}
    gw = d.genus_weights
    alone = sorted(u for u in gw.presences_per_unit if u != POOLED)
    informative = fd.informative_blocks(d.blocks, d.y)
    out["groups"][name] = {
        "file": str(path),
        "presence_outcomes": d.presence_outcomes,
        "presences_entering": int(d.n_presences),
        "genera_counting_alone": len(alone),
        "presences_per_genus_counting_alone": {u: gw.presences_per_unit[u] for u in alone},
        "genera_pooled": len([g for g, u in gw.unit_of.items() if u == POOLED]),
        "presences_in_pool": gw.presences_per_unit.get(POOLED, 0),
        "per_block": {
            names[b]: {"presences": n, "forested": b in forested_all, "in_fit": b in in_fit}
            for b, n in per_block.items()
        },  # fmt: skip
        "forested_blocks_in_box": len(forested_all),
        "forested_blocks_in_fit": len(forested),
        "forested_blocks_reaching_minimum": sorted(names[b] for b in forested & informative),
        "blocks_reaching_minimum": len(informative),
    }
    print(name, d.n_presences, len(alone), len(forested & informative), "/", len(forested),
          flush=True)  # fmt: skip
    del d
(HERE / "entering_by_block.json").write_text(json.dumps(out, indent=1) + "\n")

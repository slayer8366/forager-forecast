"""P10b (D145) applied once, by hand, to the figures recomputed from the 2026-10-17 fit's cache
(`figures_from_cache.json`, written by `scripts/t7_fit.py figures`). A record of what ran, not part
of any run: P10b is not wired into the fit. Condition 3 (the host-specific contrast) needs part C's
comparison group, which is not built, and no independent data exist yet (condition 4), so both are
passed as None. Writes `p10b_on_existing_run.json` beside itself."""

import json
from pathlib import Path

from forager_forecast.t7.metrics import Difference, p10b

HERE = Path(__file__).resolve().parent
fig = json.loads((HERE / "figures_from_cache.json").read_text())["main"]


def as_difference(d: dict) -> Difference:
    return Difference(d["point"], d["low"], d["high"], d["resamples"])


c1 = as_difference(fig["block_clustered"]["all"]["B"])
c2 = as_difference(fig["within_weather_cell"]["full_minus_A"])
v = p10b(block_clustered_full_minus_b=c1, within_cell_full_minus_a=c2,
         host_specific_contrast=None, independent_data=None)  # fmt: skip
out = {
    "condition_1_full_minus_B_block_clustered_all_blocks": fig["block_clustered"]["all"]["B"],
    "condition_2_full_minus_A_within_weather_cell": fig["within_weather_cell"]["full_minus_A"],
    "condition_3_host_specific_contrast": "not supplied: part C's group is not built",
    "condition_4_independent_data": "not supplied: no independent data (part D not done)",
    "conditions": {"1": v.block_clustered_over_b, "2": v.within_cell_over_a,
                   "3": v.host_specific_contrast, "4": v.independent_data},  # fmt: skip
    "verdict": v.verdict,
    "passes": v.passes,
}
(HERE / "p10b_on_existing_run.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))

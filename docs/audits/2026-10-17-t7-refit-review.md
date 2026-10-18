# T7 re-fit review 1 (D18): the PNW habitat map under P10b, read by Sorrel Tally

Sorrel Tally (independent reviewer), review 1 of two, on a model other than the coder's. Written 2026-10-18 UTC for the planner (Rowan Waymark).

- **Dispatch:** `docs/dispatch/2026-10-17-t7-refit-review.md` (branch `t7-strengthen-plan`, 83f0258). The owner's go, verbatim (Forager RECORD -1232): "Go ahead and start the reviews."
- **Under review:** branch `t7-refit` at `da1f207`: `docs/audits/2026-10-17-t7-refit-report.md` and `docs/audits/2026-10-17-t7-refit/`; the run's outputs in `/mnt/work/Zynergy/forecast-data/t7/refit/`.
- **This review's branch:** `t7-refit-review`, cut from `t7-refit` at `da1f207`. Evidence folder: `docs/audits/2026-10-17-t7-refit-review/`. Review 2 was not read.
- **Flags:** READ means a file or the code says so; COMPUTED means a script in the evidence folder produced it; INFERRED means my reasoning.
- **Nothing was shown or published.** Rendered images are in the evidence folder for the planner and owner only.

## Mechanism prediction (written before any figure was computed; scored at the end)

Written 2026-10-18T03:22Z, after reading the dispatch, the coder's report and `fit_report.json`, the code, and the decision rows, and before running any script.

1. **Reproduction.** All four P10b figures, their intervals, and the beside figures (P10, base minus B, within-cell AUCs, the saprotroph and *Laetiporus* gains) reproduce exactly from the cache with my own AUC and resampling code, given the same seed and draw order. The verdict (fail on 2 and 3) is confirmed.
2. **Condition 1 and the selection.** Without any band selection, condition 1 is base minus B: +0.0016 with a block interval including zero. It fails. A leave-one-block-out selection (candidates re-chosen on the other 23 blocks' held-out predictions) will not pick the same three bands for every block: *Lithocarpus*'s lower bound (+0.00008) is thin, and *Larix*'s (−0.000004) is on the other side of zero by a hair. So the nested estimate of condition 1 will sit between base minus B and the reported +0.0038, and its interval will include zero. I expect to say: condition 1 would not pass without the selection.
3. **Road access.** The interaction groups, the monotone direction, the held median and the exclusion from the area of applicability are implemented as D156 states. Within one weather cell, the negated road distance alone will rank pairs at about A's 0.648 (within 0.01), so A's within-cell AUC is the road band and nothing else. Condition 2's collapse is that: once road distance is known, the habitat bands add nothing inside a cell, and even cost a little. Holding access on the map does not remove habitat signal from the ranking, because the raw score is additive in the held group (P6 passed); what it does is settle, at fit time, which of the two correlated inputs gets the within-cell gradient, and the monotone constraint pushes that toward access. The map's top tenth moved away from roads, so the ranking was not pulled toward them.
4. **Condition 3.** The saprotroph gain (+0.0021) and *Laetiporus* gain (+0.0141) reproduce. The evidence does not support "mycorrhizal" in a label: a wood-rot genus gains three times as much from the same bands.
5. **Condition 4.** The filters are as D158 states. The pass is mostly geography, not habitat: 4,666 of 6,026 kept specimens are in four western blocks (Puget Lowland, Coastal Range, Cascades, North Cascades), and the background is matched on road band but drawn from the whole box. Scoring by the point value instead of the circle mean will give a similar figure (within 0.03). Drawing the matched background from the specimen's own level III block will drop AUC minus 0.5 well below the reported +0.196, to under +0.10, with an interval including zero. Specimens from 2000 on will score about the same as older ones. The interior figure (390 specimens, −0.157 to +0.240) is not usable as a verdict either way.
6. **The map.** Interior mountain conifer forest ranks highest; the Canadian side is a flat masked band with a hard edge at the border; cells outside the area of applicability are few and scattered. Against 2026-10-16 the picture is close (rank 0.91), with the top tenth shifted toward the Cascades and away from the Columbia Plateau's edges.

(The sections below are filled in as the review runs.)

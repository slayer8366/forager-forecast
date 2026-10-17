# Independent review (D18) of the T7 PNW fit

Reviewer: an independent agent session started by the Forager planner (Rowan Waymark). Dispatch:
`docs/dispatch/2026-10-16-t7-fit-review.md` at `d911bf2`. Reviewed: branch `t7-build` at `b5c3d26`
(report) and `17bb84e` (evidence), code at `41f9c79`. Written 2026-10-17 UTC (evening of 2026-10-16
Pacific).

Flags: READ means a file says so (file and line given). COMPUTED means my own code, in
`docs/audits/2026-10-16-t7-fit-review/`, printed it. INFERRED means my reasoning.

## Prediction (mechanism, reviewer), written before computing anything

Written after reading the dispatch, the fit report and `src/forager_forecast/t7/model.py`, before
running any code.

1. **Habitat or effort.** `model.py` keeps `log_effort` in its own interaction group, so every fitted
   model is additive: habitat part plus effort part. The map at the held effort is the habitat part
   plus a constant, and model A at the held effort is a constant everywhere. So the dispatch's
   "effort-only map" can only mean A at each cell's own effort, the effort surface itself. I predict
   the habitat part correlates positively but only moderately with the effort surface (Spearman about
   0.3 to 0.5 over shaded cells inside T6's frame), because the habitat bands partly proxy for reachable,
   low-elevation, west-side forest that people search. Where they differ most: remote high forest
   (Cascade crest, Idaho Batholith, north Rockies) shaded high by habitat with low effort, and
   urban/valley lowlands (Willamette, Puget) with high effort but middling habitat. The pooled AUCs and
   the weather-cell intervals reproduce to rounding; block intervals include zero.
2. **Mycorrhizal-specific.** The habitat inputs carry a general "forest that people report fungi in"
   signal plus host-specific parts. *Laetiporus* gains more because its effort-only baseline is weaker
   (0.844) and broadleaf/oak shares carry real host signal for it. I predict the evidence supports
   "forest-associated fungal reporting" at most, not "mycorrhizal habitat", and that the comparison
   correlation reproduces near 0.23.
3. **Weight fix.** With the comparison group's weights summing to 2 over about 500,000 points, the
   per-point hessian is about 1e-6, so a 1,000-point leaf's hessian sum is about 1e-3 times
   p(1-p), under `min_sum_hessian_in_leaf` (1e-3): no split, so B equals A. For the main group (total
   about 90) a leaf's hessian clears the floor, so it splits, but `lambda_l2 = 10` is large against
   hessian sums of order 1 to 20, so leaf values shrink hard and the unfixed main fit is much more
   heavily regularised. Rescaling by a constant changes no share, threshold or sample, and leaves the
   weighted AUC unchanged. I predict the main group's sign of full minus A survives the unfixed weights
   but the margin changes, and I cannot predict its direction with confidence. The revert check fails
   with the "fit split at all" or the allclose assertion.
4. **D18 checks.** V9 counts reproduce exactly; 26 level III blocks with study cells is right and 25
   is a headline slip, as the report says.
5. **The map.** High along the west-side Cascades and Coast Range and the Puget lowland, low in the
   Columbia Plateau and basin and range. Artefacts I expect to look for: a hard edge at 49°N (Canada,
   code 3), possible seams at T6b's 256-tile edges and the `us_half` tiles, and blocky texture from the
   coarse soil pH layer.

(Findings follow below.)

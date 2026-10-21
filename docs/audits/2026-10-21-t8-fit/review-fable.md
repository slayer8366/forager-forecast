# T8 review: Sorrel Tally, on Fable

Filed by the forecast planner (Alder Bearing), 2026-10-21, in summary. The dispatch is
`docs/dispatch/2026-10-21-t8-review.md`. This is a faithful condensation of the reviewer's final message, made
because that message lives only in a session transcript. Scratch is in /mnt/work/scratch/t8-review-fable/
(recompute.py, probe2.py, probe3.py and their .out files). All checksums pass. One recomputation read an input,
T1's weather npz, to recompute W1 to W4, and the reviewer disclosed it.

**Verdict unchanged.** Every figure in headline-bar.md and results.md matches the stored outputs to the digit.
Findings 1 and 2 weaken only the reading of C1 and C2. Even with both corrected in weather's favour, the
challenger still fails C1 to C3, and the main model still fails C1 and C3.

## Findings

1. **Medium.** C2's point estimate is carried by one fold's extrapolation. The 2021 fold contributes +3.545 to
   the weather model's +1.513 excess squared error; every other fold nets −2.03, so weather helped there.
   - The damage is 7 units with p_main 0.32 to 0.57 against p_no_weather 0.04 to 0.08, all negative. They are
     at 485_-1244, 486_-1244, 485_-1245, 485_-1243 and 493_-1249, in ISO weeks 45 to 49 of 2021.
   - The cause, computed: W2 (56-day rain) there is 1,279 to 1,324 mm, above the 2021 fold's training maximum
     of 1,162 mm. Natural splines run linearly beyond their boundary knots (models.py:73-87). This is model
     form as fixed by plan §6 and D133 (6), not a bug.
   - Excluding 2021 now is forbidden, so the verdict stands.
   - **results.md omits the per-year table and the AUC and reliability items that plan §7 lists.** 2021's
     skill against no-weather is −0.0318; every other informative year lies between −0.0009 and +0.0038. AUC:
     main 0.751, no-weather 0.743, T1 calendar 0.792. Recommendation: add these, with a sentence on 2021.
2. **Medium (a reading).** C1 measures model form. No-weather alone against T1 is −0.00969 [−0.01558,
   −0.00388]. T1's calendar is LightGBM on doy_sin, doy_cos, latitude and longitude, so it can fit season ×
   place interactions, which the additive calendar can't. The challenger's C1 is +0.00236 [−0.00075,
   +0.00582]. The write-up should say that C1's gap is form.
3. **Low.** 132 of 199 swapped-weather models beat no-weather: median swap Brier 0.020786, against 0.020809
   for no-weather and 0.020838 for the main model. What the measures add is climatology, and the year's own
   weather is, if anything, worse than a random year's. This supports the W4 reading.
4. **Low.** The ecoregion "none" block is the shoreline. 131 of its 177 cells are T1's "neighbour" cells (RECORD
   -822, own ERA5-Land point is water), and 131 of T1's 163 neighbour cells fall in it. The 46 own-point cells
   are at Puget Sound inlets, Lake Washington, Juan de Fuca and Victoria. [I] The cell centres are in water,
   which the terrestrial polygons don't cover (ecoregions.py:81-102); not checked against a coastline file.
   The block is coherent (58 units per cell, against 26 overall), so its +0.0048 reads as a coastal row.
5. **Low.** A stale comment: jump.py:85-87 says the genus keys come from GBIF's API. The code
   (count.py:174-189) resolves them from the zip, with Amanita pinned (D135).
6. **Note.** Two memory figures exist for the bar run: 915 MB (systemd) and 882 MB (peak_rss_mb). Say which is
   quoted.

## The five questions

- **Q1:** no departure from the plan or D133 to D137. Checked with file and line in design.py, weather.py,
  bar.py, t1_model.py, effort_term.py, run.py, models.py, fit.py, scripts/t8_fit.py and jump.py.
  `git diff 49862a1 c48be9f -- src` is the D137 change only, which is inactive for t1_1000m and cc.
- **Q2:** confirmed by recomputation, with intervals reproduced exactly. Also matching: forecast, the
  2015–2023 line, the challenger, 5,000 m, cc and the alone table.
- **Q3:** no leak. Week alignment is right. The swaps are real (199 distinct Briers). The issues unfair to
  weather are findings 1 and 2. Against weather: chanterelle outings in effort, and a swap null below
  no-weather, so C3 is a hard bar.
- **Q4:** faithful where present; the per-year table, AUC and reliability are missing.
- **Q5:** the count's figures and the "undetermined" label follow from D134 and D135.

**Not checked:** the swap refits, the effort surfaces' values, the CEC point-in-polygon step, the count's pass
over the zip, a coastline file, the test suite, and RECORD -2036 to -2038.

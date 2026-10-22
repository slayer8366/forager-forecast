# T8 review: Sorrel Tally, on Sonnet

Filed by the forecast planner (Alder Bearing), 2026-10-21, in summary. The dispatch is
`docs/dispatch/2026-10-21-t8-review.md`. This is a faithful condensation of the reviewer's final message, made
because that message lives only in a session transcript. The reviewer's scratch scripts are in
/mnt/work/scratch/t8-review-sonnet/. Marking: [R] read, [C] computed, [I] inferred.

**Bottom line:** nothing found changes the headline verdict (FAIL). C1 to C4 were recomputed from the stored
predictions, and they match to every printed digit. No leak, misaligned week or fake swap was found. Each of
C1, C2 and C3 fails on its own, so the verdict holds even without C4, whose interval's lower bound is
+0.0003. All checksums pass.

## Findings, ranked

1. **Medium (wording).** C2's loss comes from 20 units in one year. [C]
   - All 20 are in 2021, in the weeks of Oct 18 to Dec 6, on the Olympic Peninsula and the coast. None is
     positive. Their mean weather-model prediction is 0.33, against 0.054 for no-weather; the weather model's
     maximum is 0.57.
   - Those 20 add +2.45 to the weather model's loss. The other 52,698 units are 0.93 better than no-weather.
   - [I] The likely cause is that unpenalised natural splines extrapolate linearly beyond the training range
     (models.py:7-10, 92-106, 141-151) on an extreme 2021 season. The weather values were not read.
   - The design was fixed in advance (D136), so changing it now would be a post-hoc search. C1 fails either
     way: no-weather alone is −0.0097 against T1.
   - Suggested wording: "this fixed unpenalised-spline design failed", not "weather has no signal".
2. **Medium (wording).** C1 mostly measures model class. No-weather alone scores −0.00969 against T1's tree
   calendar, and weather adds −0.00138. The challenger is the like-for-like comparison: C1 +0.0024
   [−0.0008, +0.0058], C2 +0.0013 [−0.0006, +0.0032]. This is as the plan specifies, not a code departure.
3. **Low (omission).** results.md does not name the better model by Brier, which plan section 6 asks for.
   The challenger JSON gives `better_by_brier` "challenger" at 0.020561, against 0.020838 for the main
   model and 0.020609 for T1's calendar. The challenger's C1 interval still includes zero.
4. **Low.** The ecoregion "none" block: 10,254 units (19.45%), 197 positives, in 177 cells. 65% of those units
   have T1 land_point "neighbour", against 16% overall. The cells lie at 42.0 to 49.5 N and 125.0 to 122.3 W,
   and the busiest look water-centred near Victoria, Vancouver and the San Juans. [I] The likely cause is
   cell centres over water or coastal slivers. 46 cells with their own land points are still "none", and
   could be sliver gaps. This is by design (ecoregions.py:98-101). The block is not an ecoregion.
5. **Low.** The W4 reading is supported. The cell bootstrap treats years as exchangeable, so the swap test is
   the stronger one; W4 is also one of four unadjusted looks. 132 of 199 swaps beat no-weather, so seasonal
   shape is present that 3 harmonics miss. That means the bar isn't unfairly hard on that point.
6. **Low (caveats).**
   - Held-out effort is interpolated, and 2025 uses 2024's level.
   - Training effort includes that year's chanterelle outings. D136 rules this, and both models share it.
   - An empty recordedBy becomes one observer per dataset (effort.py:111-114), which could undercount J1
     and J2.
   - Cantharellus records are counted by calendar year, while J5 counts by ISO year (jump.py:233-240).
   - Nobody has checked whether the 2024–25 jump is partly a change in how coordinate uncertainty is
     reported.

## The five questions

- **Q1, code against the plan:** no departure found. Cited design.py:33-54, 66-77, 85-88; bar.py:104-141;
  fit.py:46-50, 78-86, 117-132; models.py:79-97, 276-296; weather.py:174-188.
- **Q2, the headline:** confirmed. C1 −0.011082 [−0.017618, −0.005030]; C2 −0.001379 [−0.004049,
  +0.000856]; C3 173 of 199, p = 0.870; C4 +0.0021506 [+0.000266, +0.003935]. The other parts' figures
  match their JSON.
- **Q3, fairness:** no leak. A swap is a real swap. Finding 1 is the only issue unfair to weather, and it is
  a property of the design.
- **Q4, the no-verdict reports:** faithful, with findings 3 and 4 to add.
- **Q5, the count:** the figures and the "undetermined" label follow from D134 and D135.

**Could not check:** the tests (not run), the raw weather arrays, the CEC polygons, D26's zip, T6's
chosen_per_fold procedure, and the 5,000 m and cc predictions (their JSON only was read).

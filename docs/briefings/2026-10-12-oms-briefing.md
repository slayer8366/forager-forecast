# Briefing for the Oregon Mycological Society meeting, Monday 2026-10-12

## The card (one page; everything behind it is in the appendix below, with sources)

**The result, in plain words.** We built a pilot for chanterelles in western Oregon, western
Washington and the southern tip of British Columbia. A model that reads the weather was tested
against a seasonal calendar that knows only the date and the place. Each of the eleven years from
2015 to 2025 was held back in turn and used as the test, so the model was always scored on a year it
had not been trained on. **The weather model did no better than the calendar, and if anything very
slightly worse.** So the pilot has not shown that the weather helps, yet.

**What the score means.** The score compares each model's average error, week by week and cell by
cell (a cell is a square of map about 11 km across). Zero would mean as good as the calendar; above
zero, better; below zero, worse. The weather model's average error was about 0.35% larger than the
calendar's (score −0.0035, with a 95% range of −0.0066 to −0.0001). The gap is small enough that the
safe reading is "no better", not "the weather makes it worse". Chanterelles were reported in about 2
in every 100 of the cell-weeks tested.

**Who checked it.** The figures were rechecked by an "independent review": a second automated
reviewer, working separately from the builder with its own code, which reproduced every headline
figure it checked. No outside scientist has reviewed the model.

**What the pilot is still worth.** The whole chain ran end to end on the Pacific Northwest, which is
what the pilot was for, before committing to the continent. The test did its job: it caught a model
that did not beat the calendar.

**Before showing the page.** Check the live page on Monday morning before leaving.
- It opens on the soil pH layer. The forecast is under "Sighting chance (pilot)" in the layer list.
- If the weather model has been published by the meeting, that layer shows it, with the line "Pilot,
  not yet validated. Its figures were checked by an independent review. Shown whether or not it
  beats the seasonal calendar." If not, it still shows the calendar, with the note "Calendar model:
  day of year and place only."
- Either way it shows the week of 5 October, not this week.
- The page's intro says "the weekly chance of chanterelles being found". It changes to "being
  reported" with the next data update, and its guide's "Not validated and not reviewed" changes to
  "Not validated. Its figures were checked by an independent review." Until that update is live, the
  page says the old words.

**Say.**
- "A pilot, not validated." "It's about reports: the chance chanterelles get reported from an area in
  a week when people reported some fungus there."
- "Tested on years it hadn't seen, the weather model did no better than the seasonal calendar."
- "The figures were rechecked by a second automated reviewer; no outside scientist has reviewed it."

**Don't say.**
- Not "it works", "it predicts" or "it beat the calendar". Not "nearly", and not "the weather makes
  it worse".
- Not "validated", and not "reviewed" as if by a scientist.
- Not "the forecast" without "pilot". Not "where mushrooms are", not whether they are fruiting, and
  nothing about the odds of a person finding mushrooms.
- No percentage for a spot on the map.
- Not "this week" (it is the week of 5 October), and not "Oregon and Washington" without the edges:
  the coast to the Cascade crest, from the California border to southern British Columbia.
- Not that it uses live weather. It uses the weather archive.

**Questions worth asking the society** (full wording and sources in the appendix).
1. Are Douglas-fir, hemlock, spruce, fir and pine the right host trees for chanterelles in Oregon and
   Washington? Is any missing, or should any count for less?
2. How often are false chanterelles and jack-o'-lanterns reported as chanterelles? Would a member
   check record photos?
3. Lichen reports are used to measure how much people are out looking, because lichens show all
   year. Does that make sense to a mycologist, or is there a better group?
4. Morels are planned for spring 2027 as two models. What should the two be? What does the society
   know about burn morels against natural morels?
5. Which months would a sighting chance have to get right to be useful to members?

---

# Appendix: the evidence behind the card

Everything below is the briefing as it stood, kept for its figures and sources, with the fixes
recorded in the dated notes.

For the owner to bring. Written 2026-10-09 by the PNW coder session (Forager RECORD -772), branch
`t6b-pnw-monday`. Plain language; every figure names where it comes from. An independent read of
this briefing was filed on 2026-10-11 (`docs/audits/2026-10-11-oms-briefing-review.md`, `d4917b8`);
its findings are applied (Forager RECORD -878).

**Updated 2026-10-10** (about 20:30 UTC) by a planning writer on Forager RECORD -828 ("Update the OMS
briefing"), branch `pnw-pilot-plans`: "In one paragraph", "What exists today" and "What the PNW images
show" brought up to date, a section on the pilot map added, and "What not to say" extended. The
pilot's result is not in yet. Every place it goes is marked **TO FILL**, for the planner to fill once
the builder reports. Do not bring this file with a TO FILL left in it.

**Updated again 2026-10-10** (about 23:00 UTC) on Forager RECORD -839 ("Yes on the live input map"):
the Canadian host trees are in, so "What exists today" (the Canada row) and "What the PNW images
show" (counts, hemlock in Canada, the 49 N seam) now read the completed mosaic. One **TO FILL**
added: whether the redrawn map is live.

**Updated 2026-10-11** (about 20:05 UTC) by a writer on the planner's dispatch
`docs/dispatch/2026-10-11-oms-briefing-fill.md`: every blank in "How the pilot's result will be
stated" is filled from the builder's final fits, the independent review's pass 2 and Forager RECORD
-854, -855, -861 and -863, with a sources list there. The result: the weather model did not beat
the calendar. Two lines are pending by design: the 5,000 m run, and what the map shows on Monday.
Some earlier lines in this file were written before the result and the review (for example "not
reviewed" under "What it does not show"); they are left as written, for the owner to rule on.

**Updated 2026-10-11** (about 20:10 UTC) on Forager RECORD -875 ("Update them to match the record
(Recommended)"): the nine lines listed under the previous note are brought up to date with the
record, facts only. "In one paragraph", the gate under "What the system will be", two rows of "What
exists today", the pilot map's notes, the D33 (5) rule, the rain-gap line, the sources line and four
lines of "What not to say" changed; each names its source in place.

**Updated 2026-10-11** (about 20:40 UTC) on Forager RECORD -878, after the independent read of this
briefing (`docs/audits/2026-10-11-oms-briefing-review.md`, `d4917b8`): a one-page card added on top,
with the result in plain words, what the score means, what to say and not say, and the questions;
everything else moved below it as this appendix. Fixes from that read, each sourced in place: the
review's coverage ("every headline figure it checked"; the CC run not reviewed), the 0.982 rain
ratio's sample, the stale lines (this header, the table date, the weather row, the per-year
instruction), the map's state on Monday written for either outcome, the cell count, the status line
quoted whole, the inferred part of the rounding explanation, the review's blocking item as written,
"no better than the calendar", the random-date design's year-by-year lean, one weather service
described generically, the page opening on soil pH, the page's coming "being reported", and what
"independent review" means. "How the pilot's result will be stated" is renamed "The pilot's result".

## In one paragraph

The system will give a weekly **sighting chance** for a group of mushrooms in a weather cell, an area
about 11 km across (SPEC.md). It does not do that for the continent yet. What exists: soil acidity
across the United States and Canada at 250 m; host trees for every US cell; a measure of where and
when people report fungi at all; and, since 2026-10-10, a **pilot** for chanterelles in western
Oregon and Washington, shown on the map at `/Forager/forecast/` and labelled a pilot, not validated.
The model that also reads the weather was fitted on 2026-10-11 and was the pilot's real test: on
years it was not fitted to, it did very slightly worse than a calendar that knows only the date and
the place (see "The pilot's result"; an independent review reproduced every headline figure it
checked). The "independent review" is a second automated reviewer, working separately from the
builder with its own code; no outside scientist has reviewed the model (D18;
`docs/audits/2026-10-11-oms-briefing-review.md`, finding 2). The owner ruled that the demo shows it, labelled as not beating the calendar (Forager
RECORD -861). Until scoring publishes it, the map shows the calendar.

## What the system will be

- **The number.** "The chance the group is reported in a weather cell and week, given that at least
  one fungal observation of any kind was made there that week" (SPEC.md R3, D12). It is about
  reports, because reports are the data. It is not the chance that mushrooms are present, and the
  250 m shading inside a cell will only rank places, with no percent (D12).
- **The gate.** A region is shown only after the model beats a seasonal calendar, one that knows
  only the date and the region, on years it was not fitted to (D5, R2). The owner's words when this
  was confirmed: "We must maintain rigorous quality standards at all times" (D18). If no region
  beats the calendar, that result is written up as the outcome (SPEC.md, phase 1 done). For the
  PNW pilot only, the owner bent this for a labelled demo: it is shown whether or not it beats the
  calendar, with the map saying which (Forager RECORD -814). The weather model did not beat it, and
  the demo shows it labelled that way (-861). Nothing is published as validated.
- **The order.** Chanterelles first, chicken of the woods beside them as a control, morels for
  spring 2027 as two models, then king boletes; matsutake is on hold (START_HERE.md).
- **The parts.** Habitat (soil, host trees), a weather trigger, and an observation model for where
  people look, with one joint model kept as a challenger (D2).

## What exists today

Rows as of 2026-10-10, about 20:30 UTC, except the weather history, pilot map and weather model rows,
which were updated on 2026-10-11.

| Piece | State | Where it is recorded |
|---|---|---|
| Records of fungi, US and Canada, 2015 to 2025 | One GBIF download, 2,493,578 records (DOI 10.15468/dl.8jxmeb), filtered and counted | D26, `docs/audits/2026-10-06-d26-completion-report.md` |
| Are there enough chanterelle records? | Enough to test, thin early. In the pilot box, on that download, 1,235 usable chanterelle records over 11 years; 2015 to 2018 hold 3, 8, 12 and 29 of them | `docs/audits/2026-10-10-pnw-pilot-t1-report.md`, records table and by-year line (branch `pnw-pilot-t1`); D33 (1) |
| Where people look | An effort surface from all fungal records, with a weekend effect of 1.50 (interval 1.48 to 1.52) | T6, D101 to D109 |
| Soil pH, 0 to 30 cm, 250 m | Done for the whole study area | T4, T6b (D80, D81, D74) |
| Host trees, 250 m, United States | **Done** on the evening of 2026-10-09: all 2,015 tiles that hold only US cells, plus the US half of all 92 tiles that straddle the border | Forager RECORD -802 ("trees 2015/2015, trees-us-half 92/92"); D119 |
| Host trees, 250 m, Canada | **Done for the Pacific Northwest box** on 2026-10-10: the Canadian source (SCANFI v2) read for the 8 tiles inside the box plus the 2 border tiles the seam check needs; all 102,543 Canadian cells in the box (southern Vancouver Island, the Gulf Islands, Delta) computed, none pending. The rest of Canada waits until the pilot map is done | Forager RECORD -815, -835, -838; `docs/audits/2026-10-10-t6b-pnw-run/seam-after-10-tiles/` (branch `t6b-pnw-scanfi`) |
| Weather history for the pilot | Downloaded for training from the Copernicus Climate Data Store (ERA5-Land and ERA5) for 40 to 49.5 N, 111 to 125 W; the fits ran on 2026-10-11. The rain route was checked against the store's own daily totals for 2019: all 192,355 values equal. The map week's window weather (July to 4 October 2026) is on the data drive for scoring; the 34 points for the 5,000 m run have not been requested (row updated 2026-10-11) | Forager RECORD -812, -826, -827, -863; D24; builder's report (`pnw-pilot-t1` `f73b800`) lines 288-298 and 374-381; `forecast-data-pnw-pilot/cds/hourly-era5land-2026-{07..10}` observed 2026-10-11 |
| The pilot map | **Live** at https://zynergy-labs.com/Forager/forecast/ since 2026-10-10, 18:59 UTC: the calendar model for chanterelles (see the next section), until scoring publishes the weather model (row updated 2026-10-11) | Forager RECORD -825 (zynergy-site PR #8), -861 |
| The weather model for the pilot | **Fitted 2026-10-11** on all years, 2015 to 2025, and independently reviewed: it did not beat the calendar (see "The pilot's result"). Scoring for the map is pending (row updated 2026-10-11) | builder's report `docs/audits/2026-10-10-pnw-pilot-t1-report.md` (`pnw-pilot-t1` `f73b800`, lines 288-298); review pass 2 (`pnw-pilot-t1-review` `79b8b17`); Forager RECORD -861 |
| Habitat model, calibration, nightly job (T7 to T11) | Not started. A plan for the habitat model on the pilot box is written, not yet run | `docs/dispatch/2026-10-11-t7-pnw-pilot-habitat.md`; TASKS.md |

## The pilot map

**Where:** https://zynergy-labs.com/Forager/forecast/, the layer "Sighting chance (pilot)" (Forager
RECORD -825). The page opens on the soil pH layer; the forecast appears only after choosing
"Sighting chance (pilot)" in the layer list (Forager RECORD -858; the page's intro). The intro now
reads "the weekly chance of chanterelles being found"; it changes to "being reported" with the next
data update, and the page guide's "Not validated and not reviewed" changes to "Not validated. Its
figures were checked by an independent review." Both go in one site change with this week's data,
merged on the owner's word (Forager RECORD -878).

**Why a pilot.** The owner chose to try the whole chain on the Pacific Northwest before committing to
the continent: "The PNW can be our pilot run so we know how it works before we commit to the entire
country" (Forager RECORD -807).

**What it shows.**
- A **sighting chance** for chanterelles per weather cell of 0.1° (about 11 km by 8 km here), for the
  box 42 to 49.5 N, 121 to 125 W (T1's box, `t1_design.py:35`): the coast and the Cascades from the
  Klamath Mountains to southern British Columbia. 2,387 cells are drawn (the live data file, read
  2026-10-10). This changes with the next data update: the calendar re-published with the coastal
  rule has 2,618 cells (Forager RECORD -833).
- The **week of 5 October 2026** (ISO week 2026-W41), not this week. It was chosen because the
  weather archive held every day through 4 October (Forager RECORD -818).
- What the number means, in D12's words: "the chance the group is reported in a weather cell and
  week, given at least one fungal observation of any kind there that week."
- **Today it is the calendar.** The map's own note: "Calendar model: day of year and place only. It
  knows nothing about this year's weather." When scoring publishes the weather model, it replaces
  the calendar on the map, as a data update under the owner's approval in Forager RECORD -817,
  labelled as not beating the calendar (-861).
- Today the banner says pilot, not validated, not reviewed. With the weather model, the status line
  reads, in the owner's wording: "Pilot, not yet validated. Its figures were checked by an
  independent review. Shown whether or not it beats the seasonal calendar." The result line reads:
  "Tested on years it wasn't trained on (2015 to 2025, one year left out at a time), it did very
  slightly worse than the seasonal calendar alone. Brier skill −0.0035 (95% range −0.0066 to
  −0.0001). An independent review reproduced these figures." (Forager RECORD -863). The owner asked
  for it to be shown whether or not it beats the calendar, with the map saying which (Forager
  RECORD -814, confirmed in -824).

**What it does not show.**
- Not whether chanterelles are fruiting, and not where they are. It is about reports from a cell in a
  week where people reported some fungus.
- No spot within a cell. There is no 250 m habitat shading on the pilot yet (that is T7).
- No region has passed the gate. Under D5 nothing is published as validated, and the map lists no
  passed region.
- Nothing outside the box, and no other mushroom group.
- Not validated. It is reviewed: the independent review (D18) filed pass 2 on 2026-10-11, and every
  figure it set out to recompute reproduces (`pnw-pilot-t1-review` `79b8b17`, "## Pass 2"; Forager
  RECORD -861). That review is a second automated reviewer working separately from the builder, not
  an outside scientist (D18).
- Weather for the weeks ahead. The pilot reads the Copernicus history for both training and the map
  (Forager RECORD -819). A weekly live version needs its own weather route. Two rain figures, from
  different samples, describe the difference between the other weather service and the Copernicus
  store; they are not one figure:
  - **4 to 8% lower**: the other service's rain totals against the store's daily sums, at every one
    of 6 cells over the 90 days to Monday 2019-10-07 (for example 249.3 against 268.2 mm) (Forager
    RECORD -819). Explained on summer 2019 (6 cells, 540 cell-days) as an hour offset plus a cut of
    every hour under 0.1 mm, the cut being the whole level gap; winter, snow and the newest weeks
    untested, and what the live route does about it is not decided (-833).
  - **0.982** (1,251.7 mm against 1,274.4 mm, about 2% lower): the summed rain over D24's 252 daily
    rain values (36 one-week spans), run with the pilot's fits (builder's report, lines 278-286;
    `docs/audits/2026-10-11-oms-briefing-review.md`, finding 4).

## The pilot's result

The test is T1's design (D13, D33), run on the pilot box: a model that reads weather windows against
the calendar model, scored on years each fit did not see, one year held out at a time. The headline is
one pooled figure, not an average of years (D33 (2)). Rule, fixed before any fit (D33 (5)): if the
interval includes zero, the verdict is "not shown", and the region stays off the published map.
The pilot's interval is wholly below zero, which the review reads as a stronger failure to beat the
calendar (review pass 2, item 3). The gap is small: with 20,000 resamples, 1.6% of draws reach zero
or above (review line 787), so the safe reading is "no better than the calendar". No region is published as validated. The labelled demo still
shows the weather model, marked as not beating the calendar, under the owner's rulings in Forager
RECORD -814 and -861.

**The headline** (filled 2026-10-11; sources [S1] to [S12] are listed at the end of this section):
- Brier skill of the weather model against the calendar, pooled over every held-out cell-week, 2015
  to 2025: **−0.004** (−0.0035 to four places). 52,718 cell-weeks, 1,138 of them with a chanterelle
  report, in 2,024 cells [S1, S2, S3].
- Its 95% interval, from a bootstrap clustered by cell: **−0.0066 to −0.0001** (the builder's run,
  with the seed fixed before the fit) [S1, S2]. The independent review's own resampling gives
  −0.0068 to −0.0002, and none of its 50 seeds reaches zero [S4].
- Verdict under D33 (5): **the whole interval is below zero.** So this is not "not shown": on years
  it was not fitted to, the weather model scored worse than the calendar. The difference is small;
  the upper end of the interval is 0.0001 from zero, and with 20,000 resamples 1.6% of draws reach
  zero or above, so the safe reading is "no better than the calendar, and if anything slightly
  worse" [S1, S4]. D33 (5) names only the case of an
  interval that includes zero; by the reviewer's reading of D5, a wholly negative one means the
  model has not passed the gate for the PNW, and no region is published as validated [S4].
- In one plain sentence for the room: **Tested on eleven years one at a time, each time on a year it
  had not been trained on, the model that reads the weather did very slightly worse than a calendar
  that knows only the date and the place, so it has not shown that the weather helps.**
- What the pilot is still worth, from the same sources: the whole chain ran end to end on the
  Pacific Northwest, which is what the owner set the pilot up to learn before committing to the
  continent (Forager RECORD -807); an independent review reproduced every headline figure it
  checked, with its own code [S4]; and the test caught a model that did not beat the calendar, as it was built to.

**Per held-out year** [S2, S3, S5]:

| Year held out | Positive cell-weeks | Brier skill against the calendar | Informative? |
|---|---|---|---|
| 2015 | 3 | +0.0173 | no |
| 2016 | 7 | −0.0125 | no |
| 2017 | 12 | −0.0202 | no |
| 2018 | 27 | −0.0189 | no |
| 2019 | 72 | −0.0093 | yes |
| 2020 | 107 | +0.0015 | yes |
| 2021 | 115 | +0.0027 | yes |
| 2022 | 89 | +0.0048 | yes |
| 2023 | 97 | +0.0080 | yes |
| 2024 | 300 | −0.0063 | yes |
| 2025 | 309 | −0.0080 | yes |

A year with fewer than 30 positive cell-weeks is marked uninformative (D33 (2)). From the final
fits, 2015 to 2018 are under 30. The weather model did better in 4 of the 7
informative years; the two years with the most reports, 2024 and 2025, hold 609 of the 1,138 and
favour the calendar, and they carry the pooled figure [S5]. Positive counts here are after 468
sea-point cell-weeks were dropped, 1 of them positive, so 2024 reads 300, not the draft's 301 [S1,
S6].

**The secondary comparison:** the same test with random dates as the "no report" side, as
D13 requires beside the main design. Brier skill against the calendar: **−0.002** (−0.0022),
interval **−0.0075 to 0.0031**: "not shown", since the interval includes zero (16,042 cell-weeks,
1,234 positive, 504 cells) [S3, S7]. It is a comparison only: a calendar also beats random dates, so this design
flatters any model (D13). The two designs agree that neither shows skill for the weather. Year by
year this design leans the other way: the weather model does better in 5 of its 7 informative years,
including 2024 (+0.0200) and 2025 (+0.0250), and its AUC is higher, 0.804 against 0.793
(`fits/secondary_t1_1000m_comparison.json`, folds; builder's report line 321).

**Also to report, each as one line:**
- The weather data check against a second weather service's archive of the same reanalysis (D24), reported, not used as the gate for the pilot
  (Forager RECORD -819): **day by day, 30 of 1,008 compared values differed beyond tolerance, all of
  them rain, so 30 of the 252 rain values (summed rain over those 252 values 1,251.7 mm against
  1,274.4 mm, a ratio of 0.982); hour by hour, the land
  check failed on one hour of 6,912 (air temperature, one cell, 2025-12-12 11:00 UTC, about
  0.00005 °C past its bound), and the owner ruled to fit past it with the failure kept on record
  (Forager RECORD -854, -855). The reviewer found a rounding explanation that fits every hour
  checked: on the store's time-series route it reproduces the other service's value on all 13,824
  temperature hours; on the gridded route, where the failing hour's value came from, on 2,110 of
  2,112 hours each for two variables, the misses all at a rounding midpoint. Part of it is inferred,
  not observed: how the other service stores its values, and what it reads them from** [S8, S9;
  review lines 694-712].
- The 5,000 m sensitivity run (D33 (3)): **pending. It stopped because 22 of its cell-weeks lack
  weather; the 34 missing points have not been requested yet, and wait behind the scoring
  pull** [S10].
- The run on CC0 and CC BY records only (D33 (4)): **"not shown": skill −0.0006, interval −0.0058 to
  0.0049, on 9,640 cell-weeks with only 102 positive; only one year (2024) has 30 or more. Not
  reviewed: it ran after the review filed** [S3, S11; builder's report line 357].
- The parallel review (D18), a second automated reviewer working separately from the builder:
  **filed (pass 2, 2026-10-11). Every figure it set out to recompute reproduces. Its blocking item
  (B4): under its reading of D5, the full model may not be published for the PNW, and what to show
  instead is the owner's call. The owner then ruled to show it on the demo, labelled as not beating
  the calendar (Forager RECORD -861). It also found the extra runs had stopped without saying so
  (S11)** [S4; review lines 920-927].
- What the map shows on Monday: **if scoring has published the weather model by the meeting, the
  map shows it, labelled as not beating the seasonal calendar, with the status line "Pilot, not yet
  validated. Its figures were checked by an independent review. Shown whether or not it beats the
  seasonal calendar." If not, the map still shows the calendar. Check the live banner on Monday
  morning before leaving.** At 2026-10-11 about 20:30 UTC it had not published (Forager RECORD
  -861, -863) [S12].

Source for every figure above: listed below. The builder's report at `f73b800` still says "IN
PROGRESS" at its head and has no section named "Result"; its section "Primary design, all years,
2015 to 2025: the T1 result" (line 288) gives these figures, the review reproduced them, and Forager
RECORD -861 and -863 treat them as the result (updated 2026-10-11, RECORD -875).

**Sources for the filled lines** (read 2026-10-11, about 20:00 UTC; "re-derived" means recomputed
here from the held-out predictions with a small script, "quoted" means taken as written):
- [S1] Builder's report, `docs/audits/2026-10-10-pnw-pilot-t1-report.md` on `pnw-pilot-t1` at
  `f73b800`, lines 288-298 (units, Brier, skill, interval, "worse"). Quoted.
- [S2] `~/Zynergy/forecast-data-pnw-pilot/fits/primary_t1_1000m_comparison.json`: skill
  −0.0035360, interval [−0.006569, −0.000100], verdict "worse", label "T1 result", folds. Quoted.
- [S3] Held-out predictions `fits/{primary_t1_1000m, secondary_t1_1000m,
  primary_t1_1000m_cc}_{calendar,full}.npz`: pooled skill −0.003536, −0.002213 and −0.000613, the
  unit, positive and cell counts, and every per-year skill and positive count. Re-derived. The
  intervals were not re-derived here.
- [S4] Independent review, `docs/audits/2026-10-10-pnw-pilot-t1-review.md` on
  `pnw-pilot-t1-review` at `79b8b17`, "## Pass 2": item 3, lines 766-817 (headline table at
  779-780, seeds at 785-787, the D5 reading at 795-800, B4 at 804); verdict, lines 914-948.
  Quoted.
- [S5] Builder's report lines 300-312 (per-year table); review lines 819-845 (per-fold table,
  4 of 7, 609 of 1,138). Quoted, and checked against [S3].
- [S6] Builder's report lines 106-113 (the draft's 53,186 units, 1,139 positive, 2024 at 301) and
  lines 290-291 (468 sea-point units dropped, 1 positive). Quoted.
- [S7] Builder's report lines 317-321; review lines 848-857 (reviewer's interval −0.0074 to
  0.0033). Quoted.
- [S8] Builder's report lines 278-286 (the daily comparison); review item 1, lines 667-739
  (gate counts at 678, the failing hour at 682-686, 13,824 hours at 707-708, daily recount at
  720). Quoted.
- [S9] Forager RECORD -854 (the owner's "Option 1") and -855 (30 of 1,008, correcting "20"),
  `RECORD.md` on `records-after-173`. -862 corrects -854's route gap from 0.00016 K to 0.00024 K
  hour by hour; neither figure is used above. Quoted.
- [S10] Builder's report lines 335-345 (the stop) and 374-381 (34 points, no request made);
  `~/Zynergy/forecast-data-pnw-pilot/` holds `d33_3.sh` and no D33 (3) fit log or comparison.
  Quoted; the data folder was observed.
- [S11] Builder's report lines 357-372; `fits/primary_t1_1000m_cc_comparison.json`. Quoted, and
  the point estimate checked against [S3].
- [S12] Forager RECORD -861 and -863. `pnw-pilot-scoring` at `d3ae769` has pulled the week's
  window weather and has not published the weather model; its report still records only the
  calendar floor as published. Observed.

## What the PNW images show, and what they do not

Where to see them: the map at https://zynergy-labs.com/Forager/forecast/, live since 2026-10-09
(Forager RECORD -788), and four labelled images on the data drive under `forecast-data/pnw/images/`.
Figures from `docs/audits/2026-10-10-t6b-pnw-run/seam-after-10-tiles/mosaic-and-seam.out.txt`
(branch `t6b-pnw-scanfi`, the mosaic with Canada filled) unless named otherwise. The map's input
layers were redrawn from that mosaic with Canada filled on 2026-10-10 (Forager RECORD -839,
zynergy-site branch `input-map-canada`), and went live on 2026-10-10 at 22:34 UTC (zynergy-site PR #9,
merge 68d8ae0f, Forager RECORD -840). The four images on the drive were drawn
on 2026-10-09, before any Canadian trees, and were not redrawn; the mosaic they were drawn from is
kept on the drive as `forecast-data/pnw/mosaic-2026-10-09/`.

**The area.** The box 40 to 49 N, 111 to 125 W: Washington, Oregon, Idaho, western Montana,
northern California, northern Nevada and northwestern Utah, cut at 49 N. 16,674,133 cells of 250 m are in the study area there, 16,571,590
of them in the United States. This is a bigger box than the pilot's sighting-chance layer, which
covers 42 to 49.5 N, 121 to 125 W.

**What is shown.**
- **Soil pH**, top 30 cm, from SoilGrids 2.0: a value in 16,248,227 cells. The rest are water or
  places SoilGrids leaves blank.
- **Tree canopy cover** from TreeMap 2023 (US Forest Service) and, in Canada, SCANFI v2's own
  total crown closure (D92): a value in 16,477,605 cells.
- **Douglas-fir and hemlock**, each as a share of the tree canopy, where canopy cover is at least
  10% (D89): Douglas-fir defined in 7,087,659 cells, hemlock in 6,991,082. These two were chosen
  because Pilz et al. 2003 name them first among the PNW chanterelle hosts, and because Douglas-fir
  showed no step across 49 N in T5's test (D90), as did the conifer and broadleaf totals. The
  Canadian source cannot tell hemlock apart from other conifers (D85), so hemlock reads "not
  available" in Canada, never zero; on the map it is blank there, and the legend and tap say why.

**What is not shown, or not yet.**
- **No chance of anything on these layers.** The colours are inputs a model will use. The sighting
  chance is the separate pilot layer above.
- **Hemlock in Canada.** Not available (D85): 102,543 Canadian cells on southern Vancouver Island,
  the Gulf Islands and Delta: tree cover and Douglas-fir are drawn there, hemlock is not.
- **Every US cell in the box has its tile.** Three coastal border tiles were held back for a few
  hours on a coastline question, and the owner settled it (D120); they are filled in.
- **How strongly any of this predicts mushrooms.** That is what the model has to show, against a
  calendar, before anything is published (D5).

**Checks run on these tiles** (`docs/audits/2026-10-09-pnw-monday/`, rules committed before any
value was read):
- **Tile edges.** Recomputed across tile edges, trees and soil agree exactly: 29 tree windows
  (117,760 cells) and 10 soil windows (40,960 cells).
- **The fixed check cells.** The 2 of the project's 10 that fall in the box, one on the Oregon
  coast and one by the border in the Selkirks, match an independent recompute within tolerance,
  soil and trees.
- **The 49 N seam.** Re-run on 2026-10-10 with Canada filled, on all 25 transects (Forager RECORD
  -838; `docs/audits/2026-10-10-t6b-pnw-run/seam-after-10-tiles/seam.out.json`, branch
  `t6b-pnw-scanfi`): total cover shows a step at the border that the test reads as an artifact of
  the two sources (23 transects with a border step); the Douglas-fir, conifer and broadleaf shares
  show no step (7 transects each). The same verdicts as T5 (D90).

## Questions worth asking

1. **Host genera.** The model takes the PNW chanterelle hosts from Pilz et al. 2003 (PNW-GTR-576,
   p. 19): "In the Pacific Northwest, chanterelles generally associate with Douglas-fir, hemlock,
   spruce, fir, and pine" (`docs/audits/2026-10-06-t5-verify-report.md`, section 3). Is that the
   right list for Oregon and Washington? Is any host missing,
   or should any of these count for less?
2. **Look-alikes in the records.** False chanterelle (*Hygrophoropsis aurantiaca*) and
   jack-o'-lantern (*Omphalotus*) are the likely wrong identifications among genus-level chanterelle
   records (SPEC.md, Unverified). The plan is a hand check of 200 record photos (T2), not done yet.
   How often does the society see these misreported as chanterelles, and would a member check
   photos?
3. **The lichen benchmark.** Effort, meaning how much people look, is measured partly from lichen
   records, because lichens are visible all year (D103). Lichen reports spike in one week at the end
   of April, likely the City Nature Challenge (unverified), so that week must be handled before any
   spring group (D109). Does a lichen-based measure of who is out looking make sense to a
   mycologist? Is there a better always-visible group?
4. **Morels before spring 2027.** Morels are planned as two models (START_HERE.md), and post-fire
   morels cluster below 7 m, which no 250 m grid can see (SPEC.md, out of scope). What should the
   two be? What does the society know about burn morels against natural morels in Oregon?
5. **Which weeks matter.** Which months would a sighting chance have to get right to be useful to
   members?

## What not to say

- Not "the forecast" without "pilot", and not "where mushrooms are". The owner's title for the demo
  page is "Forager mushroom forecast: Pacific Northwest pilot" (Forager RECORD -858). The soil and
  tree layers are "Model inputs … Not a forecast on their own" (the page wording in -860).
- No percentage for any spot. The 250 m layers carry no percent (D12).
- **On the pilot:**
  - Not "it works", "it predicts" or "it beat the calendar" unless the filled-in interval is wholly
    above zero. If it includes zero, say "not shown yet": the test could not tell the weather model
    from the calendar on this many records. If it is wholly below zero, as the PNW pilot's is, say
    so plainly: on years it had not seen, the weather model did no better than the seasonal
    calendar, and if anything very slightly worse (the owner's banner wording, Forager RECORD -863,
    says "very slightly worse"). Not "nearly", not "not shown yet", and not "the weather makes it
    worse": the gap is small (review line 787).
  - Not "validated". The gate is not passed. "Reviewed" only in the banner's sense: "Its figures
    were checked by an independent review" (Forager RECORD -863); the review filed pass 2 on
    2026-10-11. It was a second automated reviewer, not an outside scientist.
  - No calendar-only figure as if it were the pilot's result. The headline compares two models; a
    score for one model alone says little.
  - Not "this week". The pilot shows the week of 5 October.
  - Not "Oregon and Washington" for the pilot layer without the box: 42 to 49.5 N, 121 to 125 W,
    east only as far as 121 W, near the Cascade crest, plus the southern tip of British Columbia.
  - Not that it uses live weather or a second weather service's archive. It reads the Copernicus history (Forager RECORD
    -819).
  - Not the wording D12 rules out for the number, nor any phrasing about the odds of a person
    finding mushrooms. The number is a sighting chance, about reports. The page's intro says "being
    found" until the next data update changes it to "being reported" (Forager RECORD -878).
  - Only the figures in "The pilot's result", with their sources. The two lines
    marked pending there (the 5,000 m run, the map on Monday) have no figure to quote yet.

# Does the weather tell us when chanterelles turn up in the Pacific Northwest? What two tests found

**Status: DRAFT for the owner to read.** It isn't published, merged or linked from anywhere. Publishing it is
a point of no return and needs the owner's word (Forager RECORD -1030).
**Written by:** the forecast planner (Alder Bearing), 2026-10-21 (Pacific). Intent: forecast RECORD
2026-09-28-2043, which follows the owner's "(a) Write-up first (Recommended)" (-2042).
**Branch:** `pnw-finding-writeup`, cut from `t8-build` at a8c2c49, where every T8 figure below lives.

Every figure is cited to the file it was read from. Anything not checked against a file says so.

---

## In short

We asked whether recent weather (rain, soil moisture and soil temperature) tells you, better than the
time of year alone, in which weeks and places chanterelles get reported in the Pacific Northwest. We tested
it twice, the second time more strictly, with every rule fixed before any result was read.

**Both times the answer was no.** On years the models had never seen, adding the weather did not beat
the calendar. In the first test it did slightly worse. In the second it failed all four conditions it had to
pass. Two independent reviews recomputed the second result and confirmed it.

**What this does not say:** it does not say weather has no effect on chanterelles. It says that *this
fixed design* (one model shape, four weather measures chosen in advance, on these public records) showed
no weather gain. The reviewers found specific reasons the design may have missed one (below).

**What follows:** nothing weather-based is published for the Pacific Northwest. There is no third weather
test on these records without new data and the owner's word (D133 (7)).

---

## What was asked

The forecast's number is a *sighting chance*: the chance that chanterelles are reported in a weather cell
in a given week, given that someone reported some fungus there that week (D12; SPEC R3). Its "given someone
was out looking" part is what lets it separate a good week from a busy week.

A weather forecast is worth publishing only if it beats what the calendar already tells you. The rule is
written into the spec: a region is published only if the model beats the day-of-year baseline on held-out
years, with an interval that excludes zero (SPEC R2, `docs/planning/SPEC.md:63`).

**Where:** 42.0 to 49.5 N, 125.0 to 121.0 W: western Washington and Oregon and the southern tip of
Vancouver Island (D123; `t1_design.py:35`).
**What:** 52,718 cell-weeks from 2015 to 2025, in which some fungus was reported. Chanterelles were
reported in 1,138 of them (results.md, headline). Records had to be placed to within 1,000 m (D33 (3)).
**How it was judged:** each year in turn was held out, the model was fitted on the others, and it was
scored on the year it hadn't seen. The score is Brier skill against a named baseline. Above zero means the
weather model did better.

## The first test (T1, 2026-10-10)

A weather model against a calendar-and-place model.

- **Result:** Brier skill against the calendar **−0.0035**, interval −0.0066 to −0.0001. The whole
  interval is below zero, so the weather model did *worse* on held-out years
  (`docs/audits/2026-10-10-pnw-pilot-t1-report.md:288-298`).

That was the first "no". Rather than stop, the owner chose a second, stricter test (Forager RECORD -1250,
filed here as D133).

## The second test (T8, 2026-10-21)

Every choice was written down and committed before any number was read (D133, D134, D136):

- **Four weather measures, fixed in advance, with no searching:** rain over the last 14 and 56 days, mean
  soil moisture over 7 days, and mean soil temperature over 14 days, each ending the day before the week.
- **How many people were out looking,** estimated separately for each held-out year from T6's
  observation layer, in both the weather and the no-weather model.
- **A model shape fixed in advance:** each measure enters as a smooth curve.
- **Four conditions, all required:**
  - **C1:** beat T1's calendar;
  - **C2:** beat the same model with the weather taken out;
  - **C3:** beat 199 versions given the weather of a different, random year (p ≤ 0.05);
  - **C4, the turnout guard:** the same model must *not* also "predict" lichen reports. Weather can't
    make lichens appear, so a gain there would mean it is only tracking when people go out.

**Result: it failed all four** (results.md, headline; headline-bar.md):

| Condition | Needed | Result | |
|---|---|---|---|
| C1, against the calendar | above 0 | −0.01108 [−0.01762, −0.00503] | fail |
| C2, against no weather | above 0 | −0.00138 [−0.00405, +0.00086] | fail |
| C3, against another year's weather | p ≤ 0.05 | p = 0.870 | fail |
| C4, lichen guard | not above 0 | +0.00215 [+0.00027, +0.00394] | fail |

Every part reported beside the headline pointed the same way (results.md):

- the forecast timing, with the weather ending 8 days before the week;
- the stricter 5,000 m record list;
- the commercial-safe record list;
- the 2015–2023 years alone;
- a tree-based challenger. It came closest, but cleared only C4, and its C1 interval still includes zero.

**Both independent reviews** (Sorrel Tally, on Fable and on Sonnet) recomputed C1 to C4 from the stored
predictions, matched every figure, and found no departure from the plan and no leak (review-fable.md,
review-sonnet.md).

## What the reviewers found, and why the wording matters

These don't change the verdict, since the rules were fixed beforehand, but they bear on what it means:

1. **One bad season carries C2.** In 2021, 56-day rain on the north-west Olympic coast in late autumn was
   higher than in any year the model trained on. The smooth curves ran on in a straight line past the
   training range, and the model predicted chanterelles where none were reported. Without that, weather
   did slightly *better* than no weather in the other years. Excluding 2021 afterwards is not allowed, so
   the fail stands (review-fable.md finding 1; review-sonnet.md finding 1).
2. **C1 mostly measures model shape.** The no-weather model alone already loses to T1's calendar
   (−0.00969), because T1's calendar is a tree model that can fit season and place together. Weather
   adds only −0.00138 to that (review-fable.md finding 2; review-sonnet.md finding 2).
3. **What the weather measures add looks like the usual season, not that year's weather.** 132 of the 199
   models given a random year's weather beat no weather, and the true year's weather did no better than a
   random year's (review-fable.md finding 3). Soil temperature alone helped, but about as much with a
   swapped year (results.md, "Each measure alone", p = 0.41).

So the honest sentence is: **this fixed additive design showed no weather gain** in the Pacific Northwest.
It is not: weather has no effect.

## A note on the records

Chanterelle reports in the area jumped in 2024 and 2025: 99 in 2023, then 346 and 326, with the number of
people reporting them going from 73 to 241 and 230 (`docs/audits/2026-10-20-t8-step1/count-report.md`). A
check fixed in advance tried to tell whether that was a real fruiting surge or more people reporting. It
read **undetermined**. Almost all of the rise came through one dataset, and from many new people reporting
a few each. The check changes only how the jump is described here, not the test.

## What this means for the forecast

- **No weather-based forecast for the Pacific Northwest** (SPEC R2; D133 (7)).
- **No third weather test on these records** without new data and the owner's word (D133 (7)).
- The habitat model (T7) was already stopped for the Pacific Northwest as it was posed (Forager RECORD
  -1247; not re-read for this draft).

## What could change it

These are open questions, not plans; any of them needs the owner's word:

- **New data:** records from another source, or more years.
- **A different design:** for example, curves that don't run on past the training range. It would have to
  be fixed in advance and tested on data this test didn't use, or it is a search after the fact.
- **A "usual season" map** that makes no forecast claim, which is a separate product decision
  (forecast RECORD -2042, option (b)).

## Not checked for this draft

- The 2024–25 jump might partly be a change in how location accuracy is reported (review-sonnet.md finding
  6).
- 19% of units sit in no ecoregion. Both reviewers inferred these are shoreline cells whose centres are in
  water; that was not checked against a coastline file.
- T7's stop is cited from Forager's record, not re-read.

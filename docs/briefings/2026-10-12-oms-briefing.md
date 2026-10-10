# Briefing for the Oregon Mycological Society meeting, Monday 2026-10-12

For the owner to bring. Written 2026-10-09 by the PNW coder session (Forager RECORD -772), branch
`t6b-pnw-monday`. Plain language; every figure names where it comes from. Nothing here has been
reviewed by a second agent yet (D18).

**Updated 2026-10-10** (about 20:30 UTC) by a planning writer on Forager RECORD -828 ("Update the OMS
briefing"), branch `pnw-pilot-plans`: "In one paragraph", "What exists today" and "What the PNW images
show" brought up to date, a section on the pilot map added, and "What not to say" extended. The
pilot's result is not in yet. Every place it goes is marked **TO FILL**, for the planner to fill once
the builder reports. Do not bring this file with a TO FILL left in it.

**Updated again 2026-10-10** (about 23:00 UTC) on Forager RECORD -839 ("Yes on the live input map"):
the Canadian host trees are in, so "What exists today" (the Canada row) and "What the PNW images
show" (counts, hemlock in Canada, the 49 N seam) now read the completed mosaic. One **TO FILL**
added: whether the redrawn map is live.

## In one paragraph

The system will give a weekly **sighting chance** for a group of mushrooms in a weather cell, an area
about 11 km across (SPEC.md). It does not do that for the continent yet. What exists: soil acidity
across the United States and Canada at 250 m; host trees for every US cell; a measure of where and
when people report fungi at all; and, since 2026-10-10, a **pilot** for chanterelles in western
Oregon and Washington, shown on the map at `/Forager/forecast/` and labelled unvalidated and
unreviewed. Today the pilot shows a calendar: what the date and the place alone say. A model that
also reads the weather is expected on Sunday 2026-10-11 and is the pilot's real test: does it beat
the calendar on years it was not fitted to?

## What the system will be

- **The number.** "The chance the group is reported in a weather cell and week, given that at least
  one fungal observation of any kind was made there that week" (SPEC.md R3, D12). It is about
  reports, because reports are the data. It is not the chance that mushrooms are present, and the
  250 m shading inside a cell will only rank places, with no percent (D12).
- **The gate.** A region is shown only after the model beats a seasonal calendar, one that knows
  only the date and the region, on years it was not fitted to (D5, R2). The owner's words when this
  was confirmed: "We must maintain rigorous quality standards at all times" (D18). If no region
  beats the calendar, that result is written up as the outcome (SPEC.md, phase 1 done).
- **The order.** Chanterelles first, chicken of the woods beside them as a control, morels for
  spring 2027 as two models, then king boletes; matsutake is on hold (START_HERE.md).
- **The parts.** Habitat (soil, host trees), a weather trigger, and an observation model for where
  people look, with one joint model kept as a challenger (D2).

## What exists today

As of 2026-10-10, about 20:30 UTC.

| Piece | State | Where it is recorded |
|---|---|---|
| Records of fungi, US and Canada, 2015 to 2025 | One GBIF download, 2,493,578 records (DOI 10.15468/dl.8jxmeb), filtered and counted | D26, `docs/audits/2026-10-06-d26-completion-report.md` |
| Are there enough chanterelle records? | Enough to test, thin early. In the pilot box, on that download, 1,235 usable chanterelle records over 11 years; 2015 to 2018 hold 3, 8, 12 and 29 of them | `docs/audits/2026-10-10-pnw-pilot-t1-report.md`, records table and by-year line (branch `pnw-pilot-t1`); D33 (1) |
| Where people look | An effort surface from all fungal records, with a weekend effect of 1.50 (interval 1.48 to 1.52) | T6, D101 to D109 |
| Soil pH, 0 to 30 cm, 250 m | Done for the whole study area | T4, T6b (D80, D81, D74) |
| Host trees, 250 m, United States | **Done** on the evening of 2026-10-09: all 2,015 tiles that hold only US cells, plus the US half of all 92 tiles that straddle the border | Forager RECORD -802 ("trees 2015/2015, trees-us-half 92/92"); D119 |
| Host trees, 250 m, Canada | **Done for the Pacific Northwest box** on 2026-10-10: the Canadian source (SCANFI v2) read for the 8 tiles inside the box plus the 2 border tiles the seam check needs; all 102,543 Canadian cells in the box (southern Vancouver Island, the Gulf Islands, Delta) computed, none pending. The rest of Canada waits until the pilot map is done | Forager RECORD -815, -835, -838; `docs/audits/2026-10-10-t6b-pnw-run/seam-after-10-tiles/` (branch `t6b-pnw-scanfi`) |
| Weather history for the pilot | Downloading from the Copernicus Climate Data Store (ERA5-Land and ERA5) for 40 to 49.5 N, 111 to 125 W. The rain route was checked against the store's own daily totals for 2019: all 192,355 values equal | Forager RECORD -812, -826, -827; D24 |
| The pilot map | **Live** at https://zynergy-labs.com/Forager/forecast/ since 2026-10-10, 18:59 UTC: the calendar model for chanterelles (see the next section) | Forager RECORD -825 (zynergy-site PR #8) |
| The weather model for the pilot | **Expected Sunday 2026-10-11**, about 05:00 to 06:00 PDT by the builder's estimate, if the data store keeps its pace; then scored and put on the map | Forager RECORD -827, -817 |
| Habitat model, calibration, nightly job (T7 to T11) | Not started. A plan for the habitat model on the pilot box is written, not yet run | `docs/dispatch/2026-10-11-t7-pnw-pilot-habitat.md`; TASKS.md |

## The pilot map

**Where:** https://zynergy-labs.com/Forager/forecast/, the layer "Sighting chance (pilot)" (Forager
RECORD -825).

**Why a pilot.** The owner chose to try the whole chain on the Pacific Northwest before committing to
the continent: "The PNW can be our pilot run so we know how it works before we commit to the entire
country" (Forager RECORD -807).

**What it shows.**
- A **sighting chance** for chanterelles per weather cell of 0.1° (about 11 km by 8 km here), for the
  box 42 to 49.5 N, 121 to 125 W (T1's box, `t1_design.py:35`): the coast and the Cascades from the
  Klamath Mountains to southern British Columbia. 2,387 cells are drawn (the live data file, read
  2026-10-10).
- The **week of 5 October 2026** (ISO week 2026-W41), not this week. It was chosen because the
  weather archive held every day through 4 October (Forager RECORD -818).
- What the number means, in D12's words: "the chance the group is reported in a weather cell and
  week, given at least one fungal observation of any kind there that week."
- **Today it is the calendar.** The map's own note: "Calendar model: day of year and place only. It
  knows nothing about this year's weather." When the weather model is scored, it replaces the
  calendar on the map, as a data update under the owner's approval in Forager RECORD -817.
- The banner says pilot, not validated, not reviewed. The owner asked for it to be shown whether or
  not it beats the calendar, with the map saying which (Forager RECORD -814, confirmed in -824).

**What it does not show.**
- Not whether chanterelles are fruiting, and not where they are. It is about reports from a cell in a
  week where people reported some fungus.
- No spot within a cell. There is no 250 m habitat shading on the pilot yet (that is T7).
- No region has passed the gate. Under D5 nothing is published as validated, and the map lists no
  passed region.
- Nothing outside the box, and no other mushroom group.
- Not reviewed. A second agent is reviewing the pilot's T1 work in parallel (Forager RECORD -816,
  -818).
- Weather for the weeks ahead. The pilot reads the Copernicus history for both training and the map
  (Forager RECORD -819). A weekly live version needs its own weather route, and a gap of about 4 to
  8% in rain totals between two routes to the same reanalysis is still being looked into.

## How the pilot's result will be stated

The test is T1's design (D13, D33), run on the pilot box: a model that reads weather windows against
the calendar model, scored on years each fit did not see, one year held out at a time. The headline is
one pooled figure, not an average of years (D33 (2)). Rule, fixed before any fit (D33 (5)): if the
interval includes zero, the verdict is "not shown", and the region stays off the published map.

**The headline (TO FILL):**
- Brier skill of the weather model against the calendar, pooled over every held-out cell-week, 2015
  to 2025: **TO FILL** (a single figure, three decimals).
- Its 95% interval, from a bootstrap clustered by cell: **TO FILL to TO FILL**.
- Verdict under D33 (5): **TO FILL** ("not shown" if the interval includes zero; otherwise say
  plainly which side of zero the whole interval is on).
- In one plain sentence for the room: **TO FILL**.

**Per held-out year (TO FILL):**

| Year held out | Positive cell-weeks | Brier skill against the calendar | Informative? |
|---|---|---|---|
| 2015 | TO FILL | TO FILL | TO FILL |
| 2016 | TO FILL | TO FILL | TO FILL |
| 2017 | TO FILL | TO FILL | TO FILL |
| 2018 | TO FILL | TO FILL | TO FILL |
| 2019 | TO FILL | TO FILL | TO FILL |
| 2020 | TO FILL | TO FILL | TO FILL |
| 2021 | TO FILL | TO FILL | TO FILL |
| 2022 | TO FILL | TO FILL | TO FILL |
| 2023 | TO FILL | TO FILL | TO FILL |
| 2024 | TO FILL | TO FILL | TO FILL |
| 2025 | TO FILL | TO FILL | TO FILL |

A year with fewer than 30 positive cell-weeks is marked uninformative (D33 (2)). The builder's draft
expects 2015 to 2018 to be under 30, but that count was taken before the coastal-cell ruling
(Forager RECORD -822) and is not the result; take the figures from the final report only.

**The secondary comparison (TO FILL):** the same test with random dates as the "no report" side, as
D13 requires beside the main design. Brier skill against the calendar: **TO FILL**, interval **TO
FILL to TO FILL**. It is a comparison only: a calendar also beats random dates, so this design
flatters any model (D13).

**Also to report, each as one line (TO FILL):**
- The weather data check against Open-Meteo (D24), reported, not used as the gate for the pilot
  (Forager RECORD -819): **TO FILL**.
- The 5,000 m sensitivity run (D33 (3)): **TO FILL**.
- The run on CC0 and CC BY records only (D33 (4)): **TO FILL**.
- The parallel review (D18): **TO FILL** (filed and what it found, or still running).
- What the map shows on Monday: **TO FILL** (the weather model, or still the calendar, and why).

Source for every figure above: `docs/audits/2026-10-10-pnw-pilot-t1-report.md` on `pnw-pilot-t1`,
once its "Result" section says it is the result (the draft's own rule, line 3-4).

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

- Not "the forecast", not "where mushrooms are". These are inputs, unreviewed.
- No percentage for any spot. The 250 m layers carry no percent (D12).
- **On the pilot:**
  - Not "it works", "it predicts" or "it beat the calendar" unless the filled-in interval is wholly
    above zero. If it includes zero, say "not shown yet": the test could not tell the weather model
    from the calendar on this many records.
  - Not "validated" or "reviewed". The map says neither, and both are true until the review is filed
    and the gate is passed.
  - No calendar-only figure as if it were the pilot's result. The headline compares two models; a
    score for one model alone says little.
  - Not "this week". The pilot shows the week of 5 October.
  - Not "Oregon and Washington" for the pilot layer without the box: 42 to 49.5 N, 121 to 125 W,
    east only as far as 121 W, near the Cascade crest, plus the southern tip of British Columbia.
  - Not that it uses live or Open-Meteo weather. It reads the Copernicus history (Forager RECORD
    -819).
  - Not the wording D12 rules out for the number, nor any phrasing about the odds of a person
    finding mushrooms. The number is a sighting chance, about reports.
  - No figure from a TO FILL line until the builder's final report gives it.

# Briefing for the Oregon Mycological Society meeting, Monday 2026-10-12

For the owner to bring. Written 2026-10-09 by the PNW coder session (Forager RECORD -772), branch
`t6b-pnw-monday`. Plain language; every figure names where it comes from. Nothing here has been
reviewed by a second agent yet (D18).

## In one paragraph

The system will give a weekly **sighting chance** for a group of mushrooms in a weather cell, an area
about 11 km across (SPEC.md). Today it is not a forecast. What exists are some of the inputs: soil acidity across the United States and Canada
at 250 m, host trees for much of the United States so far, and a measure of where and when people
report fungi at all. The Pacific Northwest images and the map at
`/Forager/forecast/` show two of those inputs. They say nothing about this week, and nothing about
whether mushrooms are in a given spot.

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

| Piece | State | Where it is recorded |
|---|---|---|
| Records of fungi, US and Canada, 2015 to 2025 | One GBIF download, 2,493,578 records (DOI 10.15468/dl.8jxmeb), filtered and counted | D26, `docs/audits/2026-10-06-d26-completion-report.md` |
| Are there enough chanterelle records? | "Holds" in both test boxes, thin in the PNW: 1,226 usable Cantharellus records over 11 years, and 2015 to 2018 hold 3, 8, 12 and 29 | `docs/audits/2026-09-18-t1-credentialed-run-report.md`, lines 33 to 35 |
| Where people look | An effort surface from all fungal records, with a weekend effect of 1.50 (interval 1.48 to 1.52) | T6, D101 to D109 |
| Soil pH, 0 to 30 cm, 250 m | Done for the whole study area | T4, T6b (D80, D81, D74) |
| Host trees, 250 m | US tiles under way; the Canadian side waits for its source (SCANFI) | T5, T6b (D84 to D92, D118, D119) |
| Weather pull, model fit, forecast | Not started (T1's fit, T7 to T11) | TASKS.md |

## What the PNW images show, and what they do not

Where to see them: the map at https://zynergy-labs.com/Forager/forecast/ once the owner merges the
site branch (until then the preview at
https://forager-forecast-pnw.zynergy-site.pages.dev/Forager/forecast/), and four labelled images
on the data drive under `forecast-data/pnw/images/`. Figures from
`docs/audits/2026-10-09-pnw-monday/mosaic.json` unless named otherwise.

**The area.** The box 40 to 49 N, 111 to 125 W: Washington, Oregon, Idaho, western Montana and
northern California, cut at 49 N. 16,674,133 cells of 250 m are in the study area there, 16,571,590
of them in the United States.

**What is shown.**
- **Soil pH**, top 30 cm, from SoilGrids 2.0: a value in 16,248,227 cells. The rest are water or
  places SoilGrids leaves blank.
- **Tree canopy cover** from TreeMap 2023 (US Forest Service): a value in 16,351,767 cells.
- **Douglas-fir and hemlock**, each as a share of the tree canopy, where canopy cover is at least
  10% (D89): defined in 6,975,936 cells. These two were chosen because Pilz et al. 2003 name them
  first among the PNW chanterelle hosts, and because Douglas-fir is the host layer that matched
  best across the 49 N border in T5's test (no step, D90). Hemlock in Canada cannot be told apart
  from other conifers in the Canadian source (D85), which does not matter inside this box.

**What is not shown, or not yet.**
- **No forecast and no chance of anything.** The colours are inputs a model will use.
- **Canada's trees.** Canadian cells wait for the Canadian tree data (SCANFI, D118). In the box
  that is southern Vancouver Island, the Gulf Islands and Delta, drawn light grey where computed
  tiles hold them.
- **Three border tiles, drawn dark grey: not computed yet.** At 256_-31_20, 256_-30_20 and
  256_-29_20 (the northern Olympic coast, the Salish Sea islands and the Bellingham area) the
  run's own check found coastline pixels that no country outline claims and that fall outside the
  US tree map. Deciding what those pixels count as changes a rule, so it waits for the owner. The
  three hold 25,760 US cells, 0.16% of the US cells in the box.
- **How strongly any of this predicts mushrooms.** That is what the model has to show, against a
  calendar, before anything is published (D5).

**Checks run on these tiles** (`docs/audits/2026-10-09-pnw-monday/`, rules committed before any
value was read):
- **Tile edges.** Recomputed across tile edges, trees and soil agree exactly: 29 tree windows
  (113,664 cells) and 10 soil windows (40,960 cells).
- **The fixed check cells.** The 2 of the project's 10 that fall in the box, one on the Oregon
  coast and one by the border in the Selkirks, match an independent recompute within tolerance,
  soil and trees.
- **The 49 N seam.** No verdict: the Canadian side is not computed yet.

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

# Independent read of the OMS briefing, 2026-10-11

Dispatch: `docs/dispatch/2026-10-11-oms-briefing-review.md` (pnw-pilot-plans `778468e`). Subject:
`docs/briefings/2026-10-12-oms-briefing.md`, unchanged between `9526ea4` and `778468e` (the only
file in that diff is the dispatch). The briefing was not edited. Line numbers below are the
briefing's at `9526ea4`.

Sources read: review pass 2 (`pnw-pilot-t1-review` `79b8b17`, equal to the remote); the builder's
report (`pnw-pilot-t1` `f73b800`, equal to the remote); `fits/*_comparison.json` and
`equivalence/` in `~/Zynergy/forecast-data-pnw-pilot/`; Forager `RECORD.md` on `records-after-173`
at `ee059e8d` (equal to the remote); `docs/planning/DECISIONS.md` (D5, D12, D13, D18, D33, D58);
`START_HERE.md`; the scoring report on `pnw-pilot-scoring` `d3ae769`; the live site's page,
zynergy-site `origin/main` `cb596aa`, `Forager/forecast/index.html`.

## Bottom line

The headline is right, and it is stated honestly. Every headline figure, every per-year row and
the secondary and CC-only point figures match the comparison files to the printed precision, and
every cited line range in the builder's report and the review points at the text it claims to.
The problems are elsewhere. One "every" claims more than the review covered. One rain figure is
quoted against the wrong sample. Several lines are stale. The page the owner will show disagrees
with the briefing's own "what not to say". And the briefing is hard to use in a room: the result
sits about 110 lines down, and nothing explains what "Brier skill" means.

## Findings, most important first

### 1. "An independent review reproduced every figure" claims more than the review covered

- **Line 162:** "an independent review reproduced every figure with its own code [S4]".
- **What's wrong:** the review reproduced every figure *it set out to recompute*, which is how
  line 118 and line 210 put it. Line 162 drops that limit, and three things in the briefing fall
  outside it:
  - **The CC0 and CC BY run (lines 207-209) was never reviewed.** It ran 2026-10-11 17:19 to
    17:35 UTC (builder's report `f73b800`, line 357). Review pass 2 was committed at 17:06 UTC
    (`79b8b17`) and says D33 (4) "never started" and has "no output" (review lines 860-875).
  - **The review did not recompute the store side of the rain comparison:** "The rain store side
    was **not** recomputed; it is the builder's" (review line 724).
  - **The briefing's own source note says its intervals were quoted, not re-derived** ([S3], line
    233).
- **Fix:** on line 162, write "an independent review reproduced every headline figure it
  checked". On line 207, add "not reviewed: it ran after the review filed".

### 2. "Independent review" could be heard as review by an outside scientist

- **Lines:** 42, 103-107, 118, 162, 210, 347. The same wording is in the banner the owner chose
  (RECORD -863).
- **What's wrong:** under D18 the review is "a second agent, in a separate session from the
  builder" (`DECISIONS.md:92`). That is real and useful: it wrote its own code and took nothing
  from the builder's but the prediction arrays (review lines 669, 742-744). But to a mycologist,
  "independent review" most naturally means a person with outside expertise. Nothing in the
  briefing helps the owner answer "who reviewed it?", and a wrong impression left standing in
  the room is the kind of thing that costs trust later.
- **Fix:** add one line to "What not to say": the review was a separate automated review, which
  rechecked the numbers with its own code. It was not a review by an outside scientist, and the
  model has had no outside review. The banner's wording is the owner's ruling, so this asks the
  owner whether to keep it. It does not change it.

### 3. The headline is hard to find, and its unit is never explained

- **Where:** lines 1-30 are four dated change notes. The result first appears at line 39, as part
  of a paragraph. Its full statement starts at line 145, under a heading still in the future tense,
  "How the pilot's result will be stated" (line 134).
- **What's wrong:**
  - **Nothing defines "Brier skill",** although it is the headline unit (lines 106, 146, 168,
    191, 207). A mycologist will ask what −0.0035 means.
  - **In plain terms:** the weather model's average squared error was about 0.35% larger than the
    calendar's (Brier 0.020682 against 0.020609, `primary_t1_1000m_comparison.json`). About 2.2%
    of the cell-weeks tested had a chanterelle report (1,138 of 52,718, same file).
  - **The guidance is split up.** What to say is at line 157. What not to say is at lines
    334-360, the end of the file. The owner cannot find the result, what to say and what not to
    say in under a minute.
- **Fix:**
  - Move the four change notes to the end of the file.
  - Rename the section "The pilot's result".
  - Put a short card first:
    - the plain sentence from line 157;
    - a one-line meaning of the score, such as "zero means as good as the calendar; below zero
      means worse";
    - the four or five "don't say" items.

### 4. The 0.982 rain ratio is quoted against the wrong sample

- **Line 131:** "the summed rain of D24's comparison sample, 1,008 daily values over 252 days".
- **What's wrong:** the 1,008 values are all four variables together. The rain sum covers only the
  252 rain values:
  - `equivalence/equivalence_values.json` holds 1,008 entries, 252 each of temperature,
    precipitation, soil temperature and soil moisture (counted here with a short script);
  - `rain_level` in `equivalence.json` sums the precipitation entries (1,274.39 against
    1,251.70 mm, ratio 0.98220).
- **Fix:** "the summed rain over D24's 252 daily rain values (36 one-week spans)". Line 198 has the
  same issue, though milder: "30 of 1,008 compared values" is correct, but "30 of the 252 rain
  values" says more.

### 5. Stale lines left from before 2026-10-11

- **Line 75 (weather row):** "Downloading from the Copernicus Climate Data Store…". The fits ran
  on 2026-10-11, so the training weather is all in (builder's report lines 288-298). Only the
  map window's weather and the 34 points for the 5,000 m run were still being fetched (RECORD
  -863; builder's report line 381).
- **Line 65:** "As of 2026-10-10, about 20:30 UTC" heads a table whose rows 76 and 77 are dated
  2026-10-11.
- **Line 5:** "Nothing here has been reviewed by a second agent yet (D18)". This is stale once
  this review is filed, and in the room it reads oddly beside "independently reviewed".
- **Lines 181-183:** "The builder's draft expects 2015 to 2018 to be under 30, but that count was
  taken before the coastal-cell ruling … take the figures from the final report only." This is
  an instruction to the person filling the blanks, written before the result. The parenthetical
  after it (lines 184-188) already holds the final answer.
- **Fix:** update the weather row to "Downloaded for training; the map week's window being
  fetched". Re-date the table. Drop line 5's claim, or point it to this review. Delete lines
  181-183 and keep the parenthetical as plain text.

### 6. The page the owner will show disagrees with the briefing

The live page is zynergy-site `origin/main` `cb596aa`, `Forager/forecast/index.html`.
- **Line 357** says not to use "any phrasing about the odds of a person finding mushrooms". The
  page's intro (line 46), in the owner's own wording (RECORD -858, -860), reads: "An early look at
  the weekly chance of chanterelles being found, cell by cell…". Anyone at the meeting who reads
  the page sees "being found". This is not one of D58's forbidden phrases, but the briefing tells
  the owner to avoid what the page says.
- **Line 118** says "It is reviewed". The page's static guide (line 182) says "Not validated and
  not reviewed". The banner follows the data file and will change when scoring publishes, but
  this guide text is fixed.
- **The briefing doesn't say the page opens on soil pH.** The forecast appears only after picking
  "Sighting chance (pilot)" in the layer list (page line 46). That is worth knowing before a live
  demo.
- **Fix:** add a "What the page says" note covering all three, so the owner is not caught out. The
  page wording is the owner's to change, and this review does not propose changing it.

### 7. The map's state on Monday is open, and the briefing's wording for it will be wrong either way

- **Line 213:** "pending: scoring publishes later today." Read on Monday, "later today" is wrong
  whatever has happened.
- **Line 92:** "2,387 cells are drawn". This was correct for the live file read 2026-10-10. The
  calendar floor was re-published with the coastal rule at 2,618 cells (RECORD -833; scoring
  report, addendum at 20:18 UTC), to be dropped together with the weather model. After the next
  data drop the count will change.
- **Lines 215-216:** these quote the status line without its last sentence, "Shown whether or not
  it beats the seasonal calendar." Lines 103-104 and RECORD -863 include it.
- **Fix:**
  - Replace "later today" with two prepared lines, one for each state of the map. Add a
    reminder to check the live banner on Monday morning before leaving.
  - Mark the cell count as changing with the next drop.
  - Quote the status line in full in both places.

### 8. The rounding explanation is stated as proven; the review says part of it is inferred

- **Lines 202-203:** "The reviewer showed the miss is a rounding effect: modelling the other
  service's rounding reproduces its value on all 13,824 temperature hours checked".
- **What's wrong:**
  - **The 13,824-of-13,824 match holds for the time-series route's values.** The failing hour's
    store value came from the gridded route, and on that route the model fits 2,110 of 2,112
    hours (review lines 694-702).
  - **The review marks part of the explanation as inferred,** not observed: that the other
    service stores values at 0.05 °C, and what it reads them from (review lines 711-712).
- **Fix:** "The reviewer found a rounding explanation that fits every hour checked. Part of it, how
  the other service stores values, is inferred." For the meeting, this whole line is better cut,
  since nobody in the room needs it.

### 9. B4 is described more softly than the review wrote it

- **Line 211:** "It blocks publishing the weather model as having passed".
- **What's wrong:** B4 says that under the reviewer's reading of D5, "the full model may not be
  published for the PNW", and that what to show instead is the owner's call (review lines
  920-927). The owner then ruled to show it, labelled (RECORD -861).
- **Fix:** "It blocked publishing the weather model under its reading of D5. The owner ruled to
  show it on the demo, labelled as not beating the calendar (-861)."

### 10. "Wholly below zero" is close to the line

- **Lines 152-154:** these say the interval is wholly below zero. That is correct for the fixed
  run. They also say its upper end is 0.0001 from zero, which is fair.
- **What's left out:** the review adds that with 20,000 resamples, 1.6% of draws land at or above
  zero (review line 787).
- **Why it matters in the room:** the safe claim is "no better than the calendar, and if anything
  slightly worse". The plain sentence at line 157 already says about that. The risk is a
  listener hearing "the weather makes it worse" as a finding about the biology.
- **Fix:** add half a sentence: "the gap is small enough that the safe reading is 'no better'".

### 11. "The two designs agree" hides that they disagree year by year

- **Line 194:** "The two designs agree that the weather adds no skill that can be shown."
- **What's wrong:** the sentence is true of the intervals. Under the random-date design, though,
  the picture is reversed:
  - the weather model wins 5 of 7 informative years, including 2024 (+0.0200) and 2025
    (+0.0250);
  - its AUC is higher, 0.804 against 0.793 (`secondary_t1_1000m_comparison.json`, folds; builder's
    report line 321).
- **Why it matters:** a sharp listener who hears the second design described might ask about
  this.
- **Fix:** optional. "agree that neither shows skill; the random-date design, which flatters any
  model (D13), leans the other way year by year".

### 12. Wording rule: one service is named in two places and described generically in a third

- **Lines 197 and 355:** these name a weather service by its product name.
- **Line 123:** this calls the same service "the other weather service".
- **Fix:** use the generic description in all three places. The other names in the briefing
  (Copernicus, GBIF, SoilGrids, TreeMap, SCANFI) are data sources credited as their licences
  require, so they can stay.
- **Checked:** D12 and D58 are clean. "Sighting chance" is used throughout. None of the D58 terms
  ("fruiting probability", "probability of finding", "chance of finding") appears in the briefing.
  The only use of "fruiting" is a negation at line 112 ("Not whether chanterelles are
  fruiting").

### 13. Length and jargon (usefulness)

- **Terms a mycologist won't follow without a gloss:** Brier skill; bootstrap clustered by cell;
  cell-week; ISO week; sea-point cell-weeks; D-numbers; B4; S11; CC0/CC BY; ERA5; "offset"; a
  temperature difference of 0.00005 °C.
- **Low-value sections for the meeting:**
  - the rain-gap sub-bullets (lines 121-132);
  - "Also to report" (lines 196-217);
  - the source list (lines 224-257);
  - the 250 m checks (lines 298-309).
- **What the pilot is worth (lines 160-163):** this is honest, and it is good material for the
  room.
- **Questions worth asking (lines 311-332):** this is the most useful section for a mycologist,
  and it is buried near the end.
- **Fix:** keep everything, but move the evidence (sources, D24 lines, rain gap, tile checks) to
  an appendix after "What not to say". Bring "Questions worth asking" up to sit right after the
  result card.

## What checked out

- **Headline** (lines 146-151): skill −0.0035360, interval [−0.006569, −0.000100]; 52,718 units,
  1,138 positive, 2,024 cells; the reviewer's interval [−0.006777, −0.000196]; no seed of 50
  reaching zero. All match `primary_t1_1000m_comparison.json` and review lines 779-787.
- **Per-year table** (lines 169-179): every row matches the `folds` of the comparison file. So do
  4 of 7, and 609 of 1,138 (300 + 309). 53,186 − 468 = 52,718 and 1,139 − 1 = 1,138 also check.
- **Secondary** (lines 191-193): −0.0022131, [−0.00747, 0.00306], 16,042 units, 1,234 positive,
  504 cells. Matches.
- **CC-only** (lines 207-209): −0.000613, [−0.00579, 0.00493], 9,640 units, 102 positive, only 2024
  at 30 or more. Matches.
- **D24 counts:** 30 of 1,008, all rain; 6,911 of 6,912; failing hour 0.0750488 against 0.075001,
  so about 0.00005 past the bound. All match `equivalence.json` and review lines 678-686.
- **Chanterelle records** (line 70): 1,235 records, 3, 8, 12 and 29 in 2015 to 2018. These sum and
  match the builder's report line 102.
- **Cited line ranges:** every one, in the builder's report (106-113, 278-286, 288-298, 300-312,
  317-321, 335-345, 357-372, 374-381) and the review (667-739, 766-817, 819-845, 848-857, 914-948),
  lands on the text claimed.
- **RECORD entries:** -788, -802, -807, -812, -814, -817, -818, -819, -822, -824, -825, -826,
  -827, -828, -833, -835, -838, -839, -840, -854, -855, -858, -860, -861, -862, -863 and -875 were
  read. Each says what the briefing attributes to it. The owner's quotes in -807 and -863 match
  the briefing verbatim.
- **Other checks:**
  - 16,674,133 − 16,571,590 = 102,543.
  - 2019-10-07 is a Monday.
  - The order of work matches `START_HERE.md:18-19`.
  - "Flatters any model" matches D13.
- **Fit timing:** the 5,000 m run is still pending. There is no fit log or comparison for it in
  `fits/`. The fits are dated 2026-10-11 (file times 09:28 PDT).

## What I could not check, or did not

- **The intervals:** I did not re-derive them. That needs a bootstrap, which this review avoided
  so as not to load the laptop. I quoted them from the files and the review.
- **Place names:** "Delta" among the Canadian cells (lines 74, 291) is not in the seam audit
  files I searched. RECORD -835 calls the box's Canadian cells "islands with no land seam", and
  Delta is mostly mainland. Not resolved.
- **"The rest of Canada waits until the pilot map is done"** (line 74): not checked against any
  later record.
- **Earlier-task facts:** the T4 to T6 figures (effort surface 1.50, soil and tree cell counts,
  tile-edge checks) were not traced. They predate 2026-10-11, and their lines did not change in
  the latest updates.
- **The live banner:** I did not open the live site in a browser. The page text comes from the
  repository's main branch.

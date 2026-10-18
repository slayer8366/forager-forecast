**WIP, paused (2026-10-18, at the planner's request, RECORD -1250 follow-up).** Draft complete through section 13 but not self-checked: several line citations (for example T6 report `:170-171`, review `:287`, scoring report `:441-443`) were not re-read after writing. Not ready for the owner's rulings.

# T8 plan: a second, stricter PNW test of whether weather beats the calendar (for the owner's decisions; no build)

**By:** Ash Transect (coder, `docs/process/coder-profile.md`), 2026-10-18 UTC.
**Dispatch:** `docs/dispatch/2026-10-17-t8-plan-dispatch.md` (t8-plan `b603c37`), Forager RECORD
-1248. It stopped at the premise check (section 0, `141f772`, RECORD -1249). The owner answered,
verbatim: "A: Second, stricter PNW weather test (Recommended)". The option read: "Adjust for search
effort, fewer weather measures fixed in advance, must beat the same calendar on the same weeks;
first check what drove the 2024–25 jump. Ash writes this as the T8 plan for your rulings" (RECORD
-1250).

**Status: a plan.** Nothing is authorised to build. Nothing was downloaded, counted, fitted or
published while writing it. Every numbered decision in section 12 is the owner's, and each has a
recommendation.

**Read against:** forecast main `f99dbcbf`; t8-plan `141f772`; t7-refit, t7-refit-review and
t7-refit-review-2 at the remote heads fetched 2026-10-18; t7-strengthen-plan for the layout; Forager
RECORD on records-after-173 through -1250.

**Small read-only probes made while writing** (no record or weather value was read):
- listings of `~/Zynergy/forecast-data-pnw-pilot/` (on /mnt/work) and of
  `~/Zynergy/forager-forecast-t6/data/t6/`;
- the array names inside two `.npz` files (zip listing only), one CSV header line, the head of one
  weather summary JSON, and the tail of three T1 fit logs (unit counts and run times);
- `df -h /mnt/work`;
- `systemctl --user status t6b-night` (read only).

**How claims are marked:** *read* (file and line), *computed* (arithmetic on figures already filed,
shown inline), or *inferred*.

## Ash's mechanism prediction (written before any T8 work, after reading T1's result)

- **The outcome:** T8 most likely fails. My estimate is about one chance in four that the primary
  model clears all four required conditions (section 6).
- **Why:**
  - T1's loss sits mainly in 2024 and 2025 (review `:841-842`).
  - In those years the share of eligible cell-weeks with a chanterelle report about tripled (section
    2).
  - That is a change in level from one year to the next. Neither a weather measure nor T6's effort
    surface, with its year level guessed from neighbouring years, can foresee it.
  - So both the weather model and the calendar will miss 2024 and 2025 by similar amounts, and the
    pooled interval will be wide.
  - Fewer weather measures should remove some of T1's overfitting loss and move the point estimate
    toward zero or just above it. An interval wholly above zero would need a real weather signal in
    2019 to 2023 large enough to carry the pool. T1's per-year table shows at most +0.008 there
    (review `:825-837`).
- **The jump check:** most likely "undetermined" (section 2's rule). The East box's chanterelle
  records fell from 2023 to 2024, so a change that hit chanterelle reports across the whole platform
  is less likely. But reporting data alone can't separate a real surge from a regional surge in
  interest.
- **The lichen turnout guard (C4):** a weather gain near zero for lichens.
- **What carries any weather gain:** if there is one, the 7-day soil moisture and the 14-day rain
  (W3, W1), in 2020 to 2023.

## 0. The stop, as written at `141f772` (2026-10-18 05:2x UTC)

Kept unchanged below the heading, so the record shows why the plan takes this shape. Its headings
are one level lower than in the original file.

### Why this stopped

The dispatch's Stops section reads: "a premise wrong in a way that changes T8's shape (for example,
T1 found no weather skill at all)". RECORD -1248 repeats it as an abort condition: "a premise that
changes T8's shape (such as T1 finding no weather skill)".

T1 found no weather skill in the only box it was run on. That is the named example.

### The premise, read from source

**What T8 depends on.** `docs/planning/TASKS.md:87-91`: T8 "Depends on: T1, T6". T1's entry,
`TASKS.md:41`: "Verify before building: the premise that weather adds skill over the calendar is
unconfirmed. No other model work starts until this reports." The T1 dispatch
(`docs/dispatch/2026-09-18-t1-calendar-smoke-test.md:9-14`) names the premise "weather windows add
skill over day of year alone", and adds "If the answer is no, that is a valid and useful result."

**What T1 found** (read, `docs/audits/2026-10-10-pnw-pilot-t1-report.md`, on main since the
`a79d667` merge):

| Run | Skill against the calendar | 95% interval | Verdict | Source |
|---|---|---|---|---|
| Headline: PNW box, 1,000 m list, all years | −0.0035 | −0.0066 to −0.0001 | worse | `:288-298` |
| D33 (3): 5,000 m list | −0.0080 | −0.0120 to −0.0044 | worse | `:383-410` |
| D33 (4): CC0 and CC BY records only | −0.0006 | −0.0058 to +0.0049 | not shown | `:357-372` |
| D13: random-date design (comparison only) | −0.0022 | −0.0075 to +0.0031 | not shown | `:317-321` |
| 2019 to 2025 hedge (partial, not the result) | −0.0029 | −0.0073 to +0.0011 | not shown | `:323-327` |

- **The independent review reproduced the headline** and found no bootstrap seed of 50 whose interval
  reaches zero (`docs/audits/2026-10-10-pnw-pilot-t1-review.md:785-789`, `:914-923`). Its verdict:
  "The weather model does not beat the calendar baseline" (`:916`).
- **Per year,** 4 of the 7 informative years favour weather. The two biggest years, 2024 and 2025
  (609 of 1,138 positives), favour the calendar and dominate the pooled figure (review `:825-845`).
- **The East box was never pulled or fitted.** D123 deferred it (`DECISIONS.md:17`). So "weather
  adds skill" is untested in the East and failed in the PNW. It is not untested everywhere.
- **What T1's model saw:** day of year, latitude, longitude and 32 rolling weather windows, by
  gradient-boosted trees; no effort term and no habitat (T1 dispatch `:42-60`; review `:194`). Its
  units already follow R3: only cell-weeks with at least one fungal record count (`:38-41`).

**What the owner already knew.** RECORD -861 and -863 (2026-10-11) show the owner ruled on this
result for the demo page, with the banner text "it did very slightly worse than the seasonal
calendar alone". RECORD -1027 (2026-10-15), four days later, chose "the full model for the PNW: T7
habitat, T8 trigger model, T9 calibration and the publishing gate". -1027's text does not mention
T1's result. Whether the owner weighed it when choosing is **not determinable from the record**;
it is not written down either way.

**No decision row** in `DECISIONS.md` (at main `f99dbcbf`) records a reading of T1's result for T8
(searched for "worse", "−0.0035" and "T8"; hits are D109 and D121 only, neither about T1's verdict).

### Why it changes T8's shape

TASKS.md's T8 is "search the windows with randomisation checks, fit the trigger model, fit one
joint model, and compare both on held-out years" (`:89`). Written that way, T8 assumes the weather
signal exists and asks which windows carry it. After T1, the first question is instead whether a
weather signal survives at all in the PNW once T1's way of looking is changed. That is a second test
of a premise that failed once, and it needs to be planned as one: what is different from T1, why
that difference could matter, and a bar that accounts for this being the second look at the same
records. Writing the original T8 plan would build on a premise the record says failed.

### The question for the owner

**Q1. After T1, what is T8 for?**

- **(A) A second, differently built test of the weather question in the PNW.** T8 is written as
  "does weather add anything once effort is handled properly", not "which windows trigger
  fruiting". It must say what differs from T1 (the effort surface from T6, a simpler model with
  few windows chosen before the search, possibly a group with more records), must beat T1's own
  calendar model on T1's units, and records T1's result as the reason the bar is strict. Its cost:
  a second look at records already tested raises the chance of a lucky pass, which the bar has to
  carry.
- **(B) Test the premise in the East box first,** as T1 was dispatched to do before D123 deferred
  it. It needs a weather download for the East box (a separate dispatch and the owner's go). If the
  East shows skill, T8 has a region where its premise holds; if not, the trigger idea is weak in
  both.
- **(C) Stop trigger work for now.** The PNW sequence closes with T1's negative result as its
  finding (SPEC.md:101-102: "If no ecoregion beats the calendar, that negative result is the
  deliverable"). The lessons write-up -1027 asks for goes ahead without T8 and T9.
- **(D) Something else** the owner names.

**Recommendation: (A),** for two reasons, both inferred rather than shown:
1. T1 lost by a small margin (upper end of the interval 0.0001 below zero), and 4 of its 7
   informative years went to weather. A differently built test is not hopeless.
2. The loss is concentrated in 2024 and 2025. From the review's per-year table (`:825-837`), the
   share of eligible cell-weeks with a chanterelle report was about 1.2% in 2023 (97 of 8,297) and
   about 3.2% and 2.9% in 2024 and 2025 (300 of 9,342; 309 of 10,505). Eligible cell-weeks rose
   about 13%, while chanterelle reports roughly tripled. That is computed here from the table, not
   explained. It could be a real fruiting surge, or a change in who reports chanterelles. Which
   one it is matters to every option above, and T8 under (A) should check it before any search.

(B) is the more direct test of the premise as written, but it needs a download, so it is not
(A)'s cheaper equal. (C) is honest and cheap, but it closes the question on one model of one kind.

### Premises in the dispatch, checked

- **main is at `f99dbcbf`:** holds. `origin/main` = `f99dbcbf`; t8-plan = `b603c37`, one commit (the
  dispatch) on top.
- **TASKS.md says "T7 to T11 | Not started | Not written yet":** still says so at `TASKS.md:20`.
  Stale for T7, which was fitted twice and stopped (RECORD -1247).
- **"T1 reported before any other model work":** in form, yes (T1's fits ran 2026-10-11, T7's
  later). In substance, the premise T1 tested did not hold. That is this stop.
- **The pilot's scoring uses Copernicus ERA5-Land and ERA5 hourly:** not re-checked, since the stop
  came first.

### Not done, because of the stop

The eleven items the dispatch asks the plan to settle (the question, groups, windows, effort, the
joint challenger, the bar, habitat and T9, the archive lag, data and cost, points of no return,
reviews). The T6, PNW-scoring and T7 reports were not read in full. Ash's mechanism prediction for
the plan is not written, because the plan's shape depends on Q1.

## 1. The question T8 answers

In R3's terms (`SPEC.md:66-69`): **on held-out years in the PNW, does knowing the recent weather
improve the predicted chance that chanterelles are reported in a weather cell and week, given at
least one fungal observation there that week, beyond what the calendar, the place and the search
effort already predict?**

- **Region:** T1's PNW box, 42.0 to 49.5 N, 125.0 to 121.0 W (`t1_design.py:35`, cited in D123,
  `DECISIONS.md:17`). It is not the larger pilot union box: the units must be T1's, and T1's
  weather covers T1's box (section 3).
- **Years:** 2015 to 2025, ISO weeks 2015-W02 to 2025-W52 (T1 report `:106-113`).
- **What changed from T1's question:**
  - effort enters (section 4);
  - four weather measures fixed in advance replace T1's 32 windows (section 5);
  - the comparison is against T1's own calendar predictions on T1's own weeks (section 7).
- **What did not change:** the meaning of sighting chance (D12), the leave-one-year-out design, the
  cell-clustered bootstrap, seed 20260918 (D31), and D33's handling of thin folds.
- **This is the second look at the same records.** T1 looked once and found weather "worse"
  (section 0). A second look raises the chance that something passes by luck. Sections 5 to 7 are
  built to carry that: nothing is chosen on held-out years, and a randomisation check is required.

## 2. First step: what drove the 2024–25 chanterelle jump

**The jump** (computed from the T1 review's table, `pnw-pilot-t1-review.md:825-837`): the share of
eligible cell-weeks with a chanterelle report was 1.17% in 2023 (97 of 8,297), 3.21% in 2024 (300 of
9,342) and 2.94% in 2025 (309 of 10,505). Eligible cell-weeks rose 12.6% from 2023 to 2024.

**What the already-filed tables say, with no new count** (computed from
`docs/audits/2026-10-06-d26-build/t1_frozen_0005709_counts_by_box_year_step.csv`, the superseded
T1 download 0005709, whose filtered PNW figures track D26's within a record or two, for example
2024: 345 against D26's 346, T1 report `:102`):
- **It is in the raw records, not made by the filters.** PNW chanterelle records inside the box,
  before any filter: 2023 321, 2024 941 (2.9 times), 2025 783. The share passing the 1,000 m
  uncertainty step moved only from 34% (108 of 321) to 43% (401 of 941).
- **All fungi rose far less.** In the box before filters: 2023 40,744, 2024 47,077 (+16%), 2025
  54,894.
- **It is not across the whole platform.** East-box chanterelles, inside the box: 2023 1,009, 2024
  574, 2025 548. They fell.
- **The licence-safe track shows it too.** CC0 and CC BY chanterelle positives were 4 in 2023, 30
  in 2024 and 24 in 2025 (T1 report `:371-372`). So it is not tied to one licence setting.

**What would tell a real surge from a reporting change.** Each check needs a count of records by a
field T1's stored table doesn't keep (its CSV holds `gbif_id, taxon_key, genus_key, latitude,
longitude, event_date, license` only). That is -1030's first point of no return (decision 2). The
check re-reads D26's zip in place, sha256 checked, with T1's filter steps and box. It reads **no
weather**, so it can't shape the weather test.

| Check | What it counts | Points to a reporting change | Points to a real surge |
|---|---|---|---|
| J1 | distinct observers with a chanterelle positive, per year | few new observers | many more observers |
| J2 | the share of the 2023→2024 rise from observers new in 2024 with 10 or more positives each | over half | small |
| J3 | positives by GBIF dataset, per year | one dataset other than the main one carries the rise | rise spread across datasets |
| J4 | the 2024 rise by ISO week and cell | over half in at most 3 weeks and at most 5 cells (an event) | spread over the season and the box |
| J5 | the rate per eligible cell-week for a fixed list of autumn genera: *Boletus*, *Hydnum*, *Russula*, *Lactarius*, *Suillus*, *Amanita* (mycorrhizal), *Laetiporus* (wood rot) | chanterelles alone rise | the mycorrhizal genera rise too |
| J6 | the share of chanterelle records named to species rather than genus, per year | a sharp change | no change |

**The rule for reading them, fixed now (decision 2):**
- **"Reporting-led"** if J2 is over half, or J3 shows one non-main dataset carrying over half the
  rise, or J4 finds over half the rise in at most 3 weeks and 5 cells.
- **"Surge-consistent"** if none of those hold, J1's distinct observers at least doubled, and at
  least 4 of J5's 6 mycorrhizal genera rose 1.5 times or more in rate.
- **"Undetermined"** otherwise.
- **The limit:** reporting data can't prove a surge. A real surge and a burst of public interest in
  chanterelles look alike in J1 to J5. Outside sources, such as forager-group or news reports, are
  not in this repository, and using any of them would be the owner's call.

**What the result changes:** the label on T8's write-up, and the reading of the 2015 to 2023 line,
which is reported regardless (section 7). It **does not** move the headline weeks, the measures or
the bar. Those are fixed before it runs.

## 3. The units: "the same weeks", exactly

- **The units are T1's primary design, as fitted:** 52,718 cell-weeks, 1,138 of them positive, in
  2,024 cells (T1 report `:288-291`).
  - Each unit is a 0.1° ERA5-Land cell × ISO week, from 2015-W02 to 2025-W52.
  - It is eligible if it holds at least one fungal record on the `t1_1000m` list.
  - It is positive if it holds at least one *Cantharellus* record.
  - The 468 sea units T1 dropped stay dropped.
- **Identity:** the `unit` array stored with T1's calendar predictions,
  `fits/primary_t1_1000m_calendar.npz` in the pilot data folder. That file also holds `cell`,
  `year`, `y` and `p` (probe, array names only). T8's run refuses to start if its unit set or
  outcomes differ by one unit, as `pnw_t1_compare.py` already refuses mismatched runs (review
  `:287`).
- **T1's calendar is used as stored, not refitted.** Its held-out predictions `p` (config per fold,
  log `fits/primary_t1_1000m_calendar.log`) are the reference for condition C1.
- **The folds:** the held-out year is the ISO year, as T1. Years with under 30 positives (2015 to
  2018) are marked uninformative and kept in the pool (D33 (2), `DECISIONS.md:99`).
- **2024 and 2025 (decision 3):** recommended **in** the headline, since the owner's words are
  "the same weeks". Taking them out after seeing T1's per-year table would be choosing weeks by
  result, and it would drop 609 of 1,138 positives. A **2015 to 2023 line is reported beside it,
  always, with no verdict**, fixed now, so the jump's weight can be read either way.
- **The sensitivity runs folded in by -1027 use their own T1 units:**
  - D33 (3): the 5,000 m list, 56,927 units, against `primary_t1_5000m_calendar.npz`;
  - D33 (4): CC0 and CC BY records only, 9,640 units, against `primary_t1_1000m_cc_calendar.npz`.
  Both are reported with no verdict, as in T1 (T1 report `:357-410`).

## 4. Effort: so that more people out on wet weeks can't pass as a trigger

**What R3 already does.** Only cell-weeks with at least one fungal record count (`SPEC.md:66-69`).
So "anyone out at all" is already conditioned away. What remains is *how much* searching happened,
and whether weather drives it.

**E1, the effort term (in both the effort-only and the weather model, decision 4):**
- The log of T6's expected outings for the cell and week (the weekday and weekend rows summed),
  from the surface's four parts (D106; manifest `data/t6/all/effort_manifest.json`).
- **Refitted once per held-out year, without that year.** The stored surface was fitted on all of
  2015 to 2025. Used as is, its cell and year levels would carry the held-out year's own outings
  into the test.
- **The held-out year's level is interpolated from the neighbouring years,** T6's "interpolated"
  scoring (T6 report `:91-93`, `:145`). At serve time the year's total isn't known, and T6 notes
  that "+ year" adds nothing when the total is given (`:109-112`).
- The CC track (D33 (4)) uses the CC surface (`data/t6/cc/`, D108).

**What E1 can't do.** T6's surface has no weather in it: cell × year × season × day type (D106). So
it can't absorb people going out *because* it rained. Two further pieces cover that:
- **C4, the lichen turnout guard (required, decision 8).** The same four weather measures predict a
  second outcome on the same units: "a lichen (Lecanoromycetes, D103) was reported in this
  cell-week". Lichens don't fruit after rain the way mushrooms do. If rain-driven turnout is what
  the weather picks up, it should raise lichen reports too.
  - The guard fails if the weather model beats the effort-only model for lichens with an interval
    wholly above zero.
  - D109 (`DECISIONS.md:30`) asks T8 to note two limits. The late-April event spike falls outside
    chanterelle season but inside the units. North of 50 N lichens can't separate effort from
    fruiting, but the box ends at 49.5 N.
  - **The risk, inferred:** in a strong fruiting week, mushroom hunters may photograph fewer
    lichens, so a real trigger could move lichen reports *down*. Brier gain has no sign. The guard
    could then fail on a real signal. It is strict on purpose, and the owner may make it reported
    only (decision 8).
- **E-sens (reported, no verdict).** The observed count of lichen outings in the same cell-week is
  added to both models. If weather's gain survives that, turnout is not the explanation. It is not
  servable, since the count isn't known ahead, so it can only be a check.

**T7's lesson, applied.** In T7 the access proxy, not the habitat, carried the within-cell ranking
(road distance alone 0.654, t7-refit-report `:91`). The analogue here is that effort, not weather,
could carry any gain. So the bar's key comparison (C2) is weather **over effort-only**, not over the
calendar alone.

## 5. The weather measures, the lags and the randomisation check

**No search (decision 5).** Four measures are fixed now. They are the D121 kinds "recent rain, soil
moisture, temperature" (`DECISIONS.md:19`), from the variables already on disk in `t1_pnw.npz`
(array names `precipitation`, `soil_moisture`, `soil_temperature`, `temperature`). Every window ends
on the same day, before the week (see the lags below).

| | Measure | Reason (from general knowledge, not from evidence in this repository) |
|---|---|---|
| W1 | rain summed over the last 14 days | autumn chanterelle fruiting is commonly described as following soaking rain by one to a few weeks |
| W2 | rain summed over the last 56 days | whether the summer drought has broken and the soil has wetted up over the season |
| W3 | mean soil moisture (0 to 7 cm) over the last 7 days | how wet the topsoil and litter are now; it folds in rain, drainage and drying |
| W4 | mean soil temperature (0 to 7 cm) over the last 14 days | fruiting is held back by warm late-summer soil and by cold late-autumn soil |

- **Disclosure:** I read T1's top features before choosing (T1 report `:314-315`: soil temperature
  90 days, rain 42 days, rain 3 days, soil moisture 90 days). The list is not blind. None of the
  four copies a T1 window exactly. D4 holds: windows from the literature are reasons, not
  parameters.
- **Air temperature is left out.** It moves with soil temperature, and four measures is the point.
- **Lags (decision 9):**
  - **Headline, "now-cast" timing:** windows end on the day before the week starts. That is T1's
    rule (T1 dispatch `:50`), so the second test sees what T1 saw.
  - **"Forecast" timing:** windows end 7 days before the week starts. The archive's lag is about 6
    days (section 10), so this is what a map published at the start of a week could use. It is
    reported in T8 with C1 and C2 computed. Passing it is required before anything is shown (T9).
- **The randomisation check (C3).** It asks whether the gain comes from *this year's* weather or
  only from weather in general.
  - **Shuffling:** each year's daily weather is swapped, whole, for another year's. It is the same
    swap for every cell, and no year is kept in place. Each cell's season shape and the box's
    spatial pattern stay; only "which year's weather" is broken.
  - **Draws:** 199 swaps, seed 20260918.
  - **Each swap repeats** the whole leave-one-year-out fit of the weather model and computes C2's
    statistic: the pooled held-out Brier gain of the weather model over effort-only.
  - **It passes if** the real gain is above all but at most 9 of the 199 (one-sided p ≤ 0.05,
    counting the real run).
  - **Windows that span the new year** read the swapped previous year. Chanterelle season is
    autumn, so this touches mostly off-season units. It is stated, not fixed.
  - **Per measure, reported with no verdict** (TASKS.md T8 Verify asks for each window's
    randomisation result): the same check with only that measure swapped.

## 6. The models and the joint challenger

D2 (`DECISIONS.md:130`) asks for a structured model and one joint model as challenger. With no
habitat part (section 9), the structure is calendar × effort × weather.

- **Primary, the structured "trigger" model (decision 6):**
  - a logistic model, additive on the log-odds scale, fitted on training years only;
  - day of year as a smooth cycle;
  - place as smooth terms in latitude and longitude;
  - E1;
  - W1 to W4, each as a smooth curve with 3 degrees of freedom, set now, with no tuning.
  - **Why:** about 1,100 positives (D121's reason, `DECISIONS.md:19`). Each measure's curve can be
    read and checked for sense, which T11's "top drivers" will need. The 199-swap check is
    affordable (section 11).
- **Effort-only:** the same model without W1 to W4.
- **Joint challenger:** gradient-boosted trees as in T1, with T1's grid and its 20-configuration
  budget from seed 20260918 (D31, `t1_model.py:27-30`), chosen by inner leave-one-year-out. Its
  inputs are the primary's: calendar, place, E1 and W1 to W4. Its own effort-only twin is fitted
  the same way.
- **Compared** on the same held-out years (section 3), and on held-out ecoregions (below), as
  TASKS.md T8 asks (`:89-90`).
- **The winner** is named by pooled held-out Brier, as TASKS.md asks.
  - The pass is judged on the primary.
  - The challenger counts as passing only if it clears C1 to C4 on its own, with C3 run on it at
    its fold-chosen settings. That doubles its fit time per swap (section 11).
  - Two models are two chances to pass, which is stated rather than corrected.
- **Held-out ecoregions:** leave-one-ecoregion-out over CEC level III regions in the box (D125's
  blocks, `DECISIONS.md:15`), for the primary and its effort-only twin.
  - A region with under 30 positives is marked uninformative and kept in the pool (D33 (2)
    applied, as D125 did).
  - Reported per region and pooled, **with no verdict in T8.** R2 publishes by ecoregion
    (`SPEC.md:63-64`), so it is T9's input.
  - How many level III regions fall in T1's box, and their positives, is unknown until counted.

## 7. The bar, fixed before any result

**T8 passes only if all four hold for the primary, on the headline units and timing (decision 7).**
Every interval comes from 1,000 resamples of cells, seed 20260918, pooled over all held-out
cell-weeks, as D33 (2) fixed for T1.

| | Condition | Why |
|---|---|---|
| **C1** | Brier skill against **T1's stored calendar predictions**, same units: interval wholly above zero | the owner's "must beat the same calendar on the same weeks" |
| **C2** | Brier skill against **effort-only** (same form, same units): interval wholly above zero | the gain is weather's, not effort's (T7's lesson) |
| **C3** | the randomisation check of section 5: p ≤ 0.05 over 199 swaps | the gain is this year's weather, not a pattern any weather would give |
| **C4** | lichen turnout guard: the weather model's gain over effort-only for lichens is **not** wholly above zero | more people out in wet weather isn't passing as a trigger |

**Reported beside, with no verdict, fixed now:**
- the per-year table, with years under 30 positives marked (D33 (2));
- the 2015 to 2023 line (section 3);
- forecast timing (C1 and C2 at a 7-day lag);
- the ecoregion results (section 6);
- D33 (3), the 5,000 m list, and D33 (4), CC0 and CC BY;
- the per-measure randomisation results;
- E-sens;
- the challenger and its effort-only twin;
- AUC, and the reliability table by decile, as T1 reported them.

Strictness against P10b: as with P10b, every required condition is an interval wholly above zero or
a pre-set null, with an effort-only comparison among them, set before the fit. Unlike P10b, nothing
is chosen on the held-out years. T7's condition 1 lost about half its margin to band selection on
held-out blocks (RECORD -1239, -1246).

## 8. What a "no" means, and a "yes"

- **A "no"** is a fail on any of C1 to C4.
  - The PNW write-up reports that weather didn't beat the calendar, twice, on two different
    designs (the owner, RECORD -1250). It names which condition failed and carries the jump check's
    label.
  - Under R2 no PNW ecoregion is published as a weather forecast. T9 has nothing weather-based to
    calibrate for the PNW.
  - **Recommended (decision 11):** no third PNW weather test on these records unless something new
    enters, such as new data (another region's box, a later season, an independent record source),
    on the owner's word. Each further look at the same records makes a lucky pass more likely.
- **A "yes"** (C1 to C4 pass) means weather adds to calendar and effort in the PNW at now-cast
  timing. T9 follows. Anything shown still needs the forecast-timing version to pass, R2's
  per-ecoregion test, and the owner's word (third point of no return).
- **Partial results:**
  - Now-cast passes, forecast fails: "weather helps only once the week's weather is known". That is
    a T10 question about faster weather sources, not a forecast.
  - C1 and C2 pass but C3 or C4 fails: "not shown to be this year's weather" or "possibly
    turnout". Either is a "no" for T8.

## 9. Habitat after T7, and T9's dependence

- **Habitat input (decision 10):** recommended **none.**
  - T7 stopped with no habitat claim (RECORD -1247).
  - T7's layers as a nuisance input would add the inputs that failed P10b. They would also make
    the model differ from T1's calendar in one more way than the owner named.
  - Place already enters as latitude and longitude, as in T1.
- **T9 (decision 11):** TASKS.md has "T9 Depends on: T7, T8" (`:93-94`). Recommended: for the PNW
  pilot, T9 depends on T8 only.
  - The 250 m relative-habitat shading (D12, R8) is left out of the PNW map. The weather-cell
    value is shown alone, if anything is shown.
  - That needs a decision row (the planner's, under D40), and a line in TASKS.md, which still reads
    "T7 to T11 | Not started" at `:20` (stale).
  - If T8 says "no", T9 doesn't run for the PNW.

## 10. The archive lag

- **Read:**
  - On 2026-10-10 18:23 UTC, the Open-Meteo archive with `era5_seamless` held days through
    2026-10-04 (scoring report `:46-47`).
  - On 2026-10-15 04:46 UTC, the Copernicus store's hourly products ended at 2026-10-09
    (RECORD -1035).
  - Both lags are about 6 days.
- **So:** a week's T1-style windows (ending the day before the week) are complete only about 6 days
  into the week, near its end. That is how W41 was published (RECORD -1035).
- **For T8:** the test is judged at now-cast timing (the science question), and forecast timing is
  reported beside (section 5, decision 9). Publishing would need the forecast-timing version to
  pass, or a faster weather source, which is T10's question, not T8's.

## 11. Data, cost, points of no return, reviews

**Data: no download is needed** (each read from listings):
- **records:** D26's zip, `forager-forecast-d26/data/d26/downloads/0012112-260928105237408.zip`
  (DOI 10.15468/dl.8jxmeb, licence lists filed under D29). It is re-read in place for the jump
  check and for lichen outcomes (class key 180, D103). T1's CSVs don't carry class or observer.
- **weather:** `weather/t1_pnw.npz` (94 MB) and `t1_pnw_d33_3.npz` (95 MB) in the pilot data folder.
  They cover T1's box from 2014-09 to 2025-12-31 (T1 report `:394-399`). The longest window here,
  56 days plus a 7-day lag before 2015-W02, starts in November 2014, inside that.
- **effort:** T6's surfaces in `forager-forecast-t6/data/t6/all` and `/cc` (four CSVs each), with
  T6's code to refit them per year.
- **T1's stored predictions:** `fits/primary_t1_1000m_calendar.npz`, `primary_t1_5000m_calendar.npz`
  and `primary_t1_1000m_cc_calendar.npz`.
- **ecoregions:** CEC level III, on the T6b drive per D125. **Not re-checked** while writing.
- **Licences:** nothing new. GBIF per record (D48); Copernicus CC-BY (SPEC `:127-136`).

**Disk:** /mnt/work has 1.8 GB free of 58 GB (97% used, `df` 2026-10-18). T8's outputs are small:
held-out predictions about 0.5 MB per run, and the swaps keep only their statistic. The run should
refuse to start under 1 GB free. Who frees space, if needed, is the planner's and owner's call.

**Compute** (the T1 figures read from logs; the rest inferred):
- **T1's GBM runs:** the calendar took 602 s and the full model 2,057 s for 11 folds with inner
  tuning (`fits/primary_t1_1000m_{calendar,full}.log`).
- **The jump check:** about 3 minutes (T1's record read took 170.6 s, report `:85-87`).
- **Per-year T6 refits:** minutes (T6's whole fit stage took 2 min 36 s, T6 report `:170-171`).
- **The additive primary and effort-only, 11 folds each:** minutes. **The 199 swaps:** about 1 to 4
  hours. **The lichen guard:** the same again, without swaps. **The challenger and its twin:** about
  45 minutes.
- **D33 (3) and (4):** roughly double the non-swap fits.
- **If the challenger also gets C3:** add about 199 × 45 min, which is too long. So C3 on the
  challenger runs at its per-fold settings with no inner tuning (about 199 × 5 to 10 min, 16 to 33
  hours). That is why only the primary decides the pass.
- **Shared laptop:**
  - `t6b-night` is running now and has been since 2026-10-17 08:45 PDT (systemctl status, read
    only). It is not overnight-only.
  - T8 runs beside it as T7 did, as a detached transient unit at Nice 10, under a 5 GB memory cap
    unless the dispatch gives another.
  - T8 never pauses or touches t6b.

**Order, and the owner's word at each point of no return:**
1. **The rules commit:** this plan's decisions as decision rows, with the measure list, the bar,
   the swap rule and the jump rule. Code and tests, tests first, over stubs. No real data read.
2. **The jump check counts** (J1 to J6). **First point of no return (-1030 (1)):** the owner's word
   first. Report.
3. **The unit table:** lichen outcomes and lichen outings attached to T1's units, and E1 per fold.
   That is a count of lichen presences, so it is the **first point of no return again.** It can
   share the word with step 2 (decision 12).
4. **The fits:** primary, effort-only, the swaps, the lichen guard, the challenger, the
   sensitivities. **Second point of no return (-1030 (2)):** one word for all.
5. **The report**, with every figure's source, and the mechanism prediction scored.
6. **Two independent reviews by Sorrel Tally:** one on Fable, one on Sonnet, neither on Opus, the
   coder's model (-1134). Each is forbidden to read the other, as for T7 (RECORD -1232). The planner
   compares them.
7. **Publishing:** none in T8. Anything shown is T9 and the **third point of no return.**

## 12. Decisions for the owner

1. **Which mushrooms?** Chanterelles only, the same as the first test, so the result compares like
   with like. The mycorrhizal group or chicken of the woods would have no first-test calendar to
   beat. *Recommended: chanterelles only.*
2. **The 2024–25 check.** Count, from the records already downloaded, who reported the extra
   chanterelles, from which source, in which weeks and places, and whether other autumn mushrooms
   rose too. Read it by the rule written in section 2, which is fixed before counting. The check
   looks at no weather, and its answer doesn't change the test. Counting is the first point of no
   return. *Recommended: yes, with the rule as written.*
3. **The same weeks.** Use exactly the first test's weeks, 2024–25 included, and always show a
   2015–2023 line beside it. *Recommended: yes.* Dropping the jump years now would be choosing weeks
   after seeing the result.
4. **Search effort.** Both the weather model and the no-weather model get the expected number of
   outings from the effort map (T6). It is rebuilt for each test year without that year, so the
   test doesn't peek. *Recommended: yes.*
5. **Weather measures.** Four, fixed now, no searching: rain over 14 days, rain over 56 days, soil
   wetness over 7 days, soil temperature over 14 days. *Recommended: yes.*
6. **The models.** The main model is a simple one in which each weather measure has a readable
   curve. The challenger is a tree model like the first test's. The better one is named, but only
   the main one decides pass or fail, unless the challenger passes every condition itself.
   *Recommended: yes.*
7. **The bar,** fixed before any result. All four must hold:
   - (C1) beat the first test's calendar on the same weeks, with the whole uncertainty range above
     zero;
   - (C2) beat a model that knows calendar and effort but no weather, the same way;
   - (C3) beat 199 versions with the years' weather shuffled;
   - (C4) the lichen check below.
   *Recommended: all four required.*
8. **The lichen check.** If the same weather "predicts" lichen reports too, the signal is probably
   more people out, not mushrooms, and the test fails. It is strict: in a real flush people may
   photograph fewer lichens, which could fail a real signal. *Recommended: required (stricter, as
   you chose); reported-only is the softer alternative.*
9. **Timing.** Judge the test on weather up to the day before the week, as the first test did.
   Also report the "a week late" version that a map published at the start of a week would have to
   use. That version must pass before anything is ever shown. *Recommended: yes.*
10. **Habitat.** No habitat input, since T7 made no habitat claim. *Recommended: none.*
11. **If it fails, and T9.** A second "no" is the PNW finding: no third weather test on these same
    records without new data and your word. Calibration and publishing (T9) wait on T8 alone for
    the PNW, with no 250 m habitat shading. If T8 fails, T9 doesn't run for the PNW.
    *Recommended: yes to both.*
12. **The go-points.** You'd be asked twice:
    - once to count (the 2024–25 check and attaching lichen reports to the weeks);
    - once to fit (everything in section 11 step 4).
    Nothing is shown from T8. *Recommended: two asks, as listed.*
13. **Reviews.** Two independent reviews after the fit, one on Fable and one on Sonnet, neither
    reading the other. *Recommended: yes.*

## 13. What this plan doesn't settle, premises checked, and calls beyond the dispatch

**Not settled or not determinable while writing:**
- The jump's cause (section 2 is how to find it).
- How many level III ecoregions lie in T1's box, and their positives.
- Whether lichen reports in the PNW are numerous enough per cell-week for C4 and E-sens to say
  anything. Both are unknown until counted.
- The exact run times (inferred from T1's and T6's).
- Whether the ecoregion file is where D125 says (not re-checked).
- How much T6's outings, which include chanterelle outings, leak the outcome into E1. Inferred
  small; not measured. Changing T6's outing rule (D102) would be a new ruling, not proposed here.

**Premises in the dispatch, checked:**
- **main at `f99dbcbf`:** holds.
- **TASKS.md's "T7 to T11 | Not started":** still at `:20`, stale.
- **"T1 reported before any other model work":** holds in form; its premise failed (section 0,
  RECORD -1249).
- **The pilot's scoring uses Copernicus ERA5-Land and ERA5 hourly:** consistent with the scoring
  report's republish note (`:441-443`: "This week's weather comes from the Copernicus climate
  archive"). The scoring route isn't used by T8's test.
- **"Lichens fit as T8's benchmark":** ruled in D109 (1): kept for the autumn groups, with the April
  spike and the 50 N limit written into T8's brief. Applied in section 4.

**Calls beyond the dispatch:**
- The first stop and its file (section 0).
- The jump check's classification thresholds.
- The swap design for C3.
- The lichen guard as a required condition.
- The 7-day forecast lag.
- The 1 GB free-space floor.
- Proposing the additive model as primary.
Each is offered as a recommendation in section 12, not applied.

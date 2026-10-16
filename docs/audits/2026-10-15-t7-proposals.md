# T7 "Propose before fitting": P1 to P10 for the PNW habitat map of mycorrhizal mushrooms as a group

Written 2026-10-15 (UTC, evening) by a drafting session for the Forager planner (Rowan Waymark), under
the owner's "Continue building the PNW with whatever else needs to be done" (Forager RECORD -1049) and
"Today, we get what we can done". **Documents only.** No fit, no data pull, no presence count, no merge.
No presence or observation record of any group was read, counted, tabulated or plotted in any form. The
drive was not opened. Nothing ran but `git`, `grep`, reading files in this repository and the Forager
RECORD, a five-line sum of numbers already printed in the verify report, and five public web pages.

- **Base.** Branch `t7-proposals` from forecast `origin/main` `b9127e5` (`git fetch origin` at writing:
  main unchanged). `b9127e5` holds the T7 plan (`docs/dispatch/2026-10-15-t7-mycorrhizal-habitat.md`,
  "the plan" below), the verify report (`docs/audits/2026-10-15-t7-verify-report.md`, "VR"), V15
  (`docs/audits/2026-10-15-t7-v15-prior-art.md`), the host-genera review
  (`docs/audits/2026-10-15-t6b-host-genera-review.md`, "HR") and D125 to D132.
- **Forager RECORD** read at `records-after-173` `bef3f7e1`: -1023, -1027 to -1030, -1036, -1037,
  -1044 to -1056.
- **Flags.** READ = opened in this session, cited by file:line or URL. INFERRED = my reasoning.
  UNVERIFIED = from memory, not opened. COULD NOT DETERMINE where it applies.
- **What this file is.** The plan's "Propose before fitting (the owner rules)" list (`plan:269-311`),
  drafted so the owner can rule on it. Every recommendation below is a proposal. None is in force until
  ruled; a ruling becomes a decision row (the next free number is **D133**: D132 is the last row on main,
  `DECISIONS.md:8`, and no `origin/*` branch holds a row numbered D133 or higher, checked at writing).

## The one-screen summary

| | Recommendation | Owner rules? |
|---|---|---|
| P1 | Waiting on V9 | yes, after V9 |
| P2 | Waiting on V9 | yes, after V9 |
| P3 | Background drawn at random from forest cells **inside T6's effort frame** only, 500,000 points, seed 20260918; effort enters as a covariate (no weighting) | yes |
| P4 | Train and map only US forest cells with every input defined; mask the rest with a stated reason; leave Canada out of the pilot fit; tier B out; small shares floored at 0.01; the seven new genera and `ecm_hosts` each earn a place by D129's held-out test | yes |
| P5 | LightGBM 4.7.0 (already pinned), binary presence against background, effort kept apart from every habitat input so the map's ranking does not depend on the effort level chosen | yes |
| P6 | Effort held at one box-wide value (median of frame cells); the ranking is the same at any value by P5's construction, and a test checks that | yes |
| P7 | Leave-one-block-out over level III blocks; pooled AUC, bootstrap by weather cell, seed 20260918; two comparison models; a forested-block score using a cut fixed now from layer counts (18 blocks); 30 presences minimum per block | yes |
| P8 | The area of applicability by the CAST method (importance-weighted distance in predictor space), effort excluded, threshold fixed from training data before any map is read; masked cells transparent | yes |
| P9 | Outputs on `/mnt/work`, a raw-score raster, a coded mask, a block report, a mask map and a manifest; the map shown in five unnumbered classes | yes |
| P10 | The bar: the full model beats both comparison models on pooled held-out blocks **and** on forested blocks alone, each with a bootstrap interval excluding zero | yes |

## P1. Groups, as ruled: waiting on V9

V9 is held: M1's membership list is not cleared (RECORD -1036: no licence found at source for either
fungal-lifestyle list checked), and counting presences is the owner's first point of no return (RECORD
-1030, point 1). Nothing is proposed here until V9 runs. When it does, P1 will contain, per the plan
(`plan:274-276`):

- the membership list as ruled under M1 and M2, with source, version and sha256;
- the weighting as ruled under M3 (provisionally each genus equal, RECORD -1030), with the minimum
  records per genus fixed before counting, and which genera fall under it;
- the comparison group as ruled under M4 (provisionally chicken of the woods);
- V9's counts for each: per genus, group, year, side, and level III and level I block;
- what the comparison group is meant to show: a non-mycorrhizal group whose habitat model should not
  simply reproduce the mycorrhizal one.

## P2. Presences: waiting on V9

Held for the same reason. When V9 runs, P2 will contain (`plan:277-279`, `plan:220-229`):

- the record list (R6's steps, `src/forager_forecast/records/filters.py:176`), the duplicate key and
  why, and the box test by cell centre;
- whether presences are thinned to one per 250 m cell (or another unit), and how a cell holding several
  genera counts under the ruled weighting;
- the count of presences that fall outside T6's effort frame. INFERRED from the code that this should be
  zero or close to it: R6's steps (`filters.py:176-187`) are a strict subset of T6's effort steps
  (`filters.py:193-200`: same obscured and date steps, 1,000 m against R6's 250 m), so every R6 survivor
  in one of the frame's 573 whole weeks belongs to an outing, and T6's frame is every cell with an
  outing (D101). The exceptions would be records in 2015-01-01 to 2015-01-04 in a cell with no other
  outing. It is a count to make, not a claim to rely on, and P3 depends on it.

## P3. Background, and how effort enters

**Recommendation.**
1. **Where from:** at random from the 250 m study cells that are (a) inside T6's effort frame (the
   0.1° weather cell holding the cell's centre has an outing, D101) and (b) eligible under P4 (US
   side, every input defined). No background is drawn from the other cells.
2. **How many:** 500,000 cells, without replacement, seed 20260918 (D31), drawn once and stored as a
   cell list with its sha256 in the manifest. Every fold uses the same draw.
3. **Effort as a covariate, not a weighting.** Each presence and background cell carries
   `log_effort`: the log of its weather cell's expected outings summed over the frame's 573 weeks, read
   from the stored T6 surface (`data/t6/all/`, D107). The effort for a cell is the same for every 250 m
   cell inside it.
4. **Weights:** background total weight equal to presence total weight (each background point weighted
   so the two sums match), so the presence weights from M3 do not change the prevalence the model sees.
5. **The secondary licence track** (SPEC constraint, `SPEC.md:91`; D29, D108) uses the same background
   with `log_effort` from the CC0/CC BY surface (`data/t6/cc/`), reported beside.

**Reason.**
- VR V10: 7,965 of the 12,150 weather cells holding box cells are outside the frame, carrying 66.8% of
  the box's study cells, and `effort()` refuses each one (`src/forager_forecast/effort.py:618-621`).
  D107 forbids a made-up value. A covariate route therefore cannot use those cells at all without a new
  rule.
- The frame is where a search has happened. A cell outside it had no fungal outing of any kind in 11
  years (D101). Presences are in the frame by construction (P2). Background drawn from outside the frame
  would teach the model that "nobody looked here" looks like "not habitat", which is the bias effort is
  meant to remove. Drawing background only where people have looked is the idea behind the
  target-group background of Phillips et al. 2009 (background "with the same bias" as the presences),
  applied here at the level of the frame.
- Inside the frame, people looked a lot in some cells and hardly at all in others. That is what the
  covariate is for: Simmonds et al. 2020, as recorded (`EVIDENCE.md:55`): "Integration alone does not
  fix spatial bias. A bias covariate or spatial term is needed." TASKS.md T7 asks for "the effort
  covariate" (`TASKS.md:83`).
- Not both (covariate **and** effort-weighted background): weighting background by effort and then
  also giving the model effort removes the same bias twice, and the covariate's held-constant
  prediction (P6) only means what it says if the background is not already tilted.
- 500,000 points at about 25 float64 columns is about 100 MB (VR V13's arithmetic: 10^5 to 10^6 points
  is 20 to 200 MB), well inside the 5 GB cap; it samples roughly one eligible cell in several (INFERRED:
  the eligible count is not known until P4's mask is built; VR gives 4,185 frame weather cells with box
  cells and 6,991,082 US cells with shares, not their overlap).

**What it leaves uncorrected (say this in the report).** Effort is known only per 0.1° weather cell,
about 8 by 11 km. Inside one weather cell, searchers favour trails, roads and towns, and the covariate
cannot see that. The 250 m shading inside a weather cell can still lean toward easy-to-reach places.
A finer bias layer (distance to roads, for one) is outside D121's set; it can only come in later through
D121's held-out comparison.

**Sources.** `effort.py:618-621`; D107 (`DECISIONS.md:32`), D101 (`:38`); VR V10 (`VR:176-194`);
`EVIDENCE.md:55`; Phillips, S.J., Dudík, M., Elith, J., Graham, C.H., Lehmann, A., Leathwick, J.,
Ferrier, S. (2009) "Sample selection bias and presence-only distribution models: implications for
background and pseudo-absence data", *Ecological Applications* 19(1):181-197, READ as its Europe PMC
record (abstract summary) at
https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:19323182%20AND%20SRC:MED&resultType=core&format=json
(the publisher page refused): background chosen with the same bias as the presences, built from a
target group's records, improved every method tested across 226 species, most where bias was strongest.

**Alternatives considered.**
- *Background from the whole box, effort as a covariate.* Two in three points land where effort is
  refused; needs a new rule giving those cells a value (for example "zero outings"), which is a fact
  about the counts but not a value the surface holds, and log(0) has no value. Rejected.
- *Background from the whole box, no effort.* Ignores TASKS.md's effort covariate and the bias. Rejected.
- *A true target-group background (the locations of all fungal records).* Ties background to the same
  records whose counts are held under V9's hold in spirit ("in any form"), and T6's surface already
  summarises those outings. Not chosen.
- *Effort-weighted background without the covariate.* Valid in principle (Phillips et al. 2009), but
  TASKS.md names the covariate, and P6's held-constant output needs it.
- *All eligible cells as background (no draw).* Removes the seed dependence; about six times the rows,
  multiplied through P7's nested folds. Kept as a fallback if the draw proves unstable.

**For the owner.** The model compares mushroom reports only against places where someone has reported
any fungus at all, and it allows for how hard people looked in each area, so a quiet patch of desert
cannot be mistaken for poor habitat just because nobody went there.

## P4. Covariates

**Recommendation.**
1. **Which cells enter, for both training and the map.** A cell enters only if it is: on the US side;
   inside the study area (`t6b/mask.tif`, D111, D113, D117); has every share band defined (canopy cover
   at least 10% and at least half valid, D89 (3)); and has a soil pH mean (D74). Every other cell is
   **masked**, with its reason recorded in the mask (P9). No undefined value is filled.
2. **Canada out of the pilot fit and map.** All 102,543 Canadian box cells are masked "host layers
   incomplete across the border".
3. **Bands in the base model** (D121's lean set, read as the T5 bands): `share_Pseudotsuga`, `Tsuga`,
   `Picea`, `Abies`, `Pinus`, `Quercus`, `share_conifer`, `share_broadleaf`, `total_cover_pct`,
   `ph_mean_0_30cm`, plus `log_effort` (P3).
4. **Bands that must earn a place (D129):** each of the seven tier A genera (`Larix`, `Betula`,
   `Populus`, `Alnus`, `Lithocarpus`, `Chrysolepis`, `Arbutus`) and `ecm_hosts`, one at a time, added to
   the base model and kept only if P7's pooled held-out difference favours it with an interval excluding
   zero. The kept bands together form the full model.
5. **Bands left out, stated in the report:** the five tier B genera (zero on every box cell, VR V5, HR
   item 9: a held-out test cannot evaluate a constant); `valid_fraction`, `source` and soil
   `valid_fraction_mean` (quality fields used only to decide entry); NALCMS (a mask only, A4).
6. **Small shares floored.** Every share below 0.01 is read as 0 before the fit, and the floor is in the
   manifest.
7. **Total cover's seam artifact:** does not enter, because no Canadian cell enters. Stated, and carried
   to the continental fit as an open problem.

**Reason.**
- **Undefined shares (57.8% of US box cells, VR V5).** A share is undefined where canopy is under 10% or
  under half valid. Three ways in:
  - *Missing:* the tree model sends every such cell down one learned branch. It mixes two different
    things (little canopy, bad data) into one, and it keeps in the model the towns, farms and steppe
    where many reports are made but where the tree layer says nothing about hosts (TreeMap maps forest).
    The coarse effort covariate cannot remove the town effect inside a weather cell (P3).
  - *Zero:* false. A zero share means canopy is present and none of it is that genus.
  - *Masked:* the map says nothing where the tree layer says nothing. This is the honest reading of a
    host-tree layer, and it removes most of the desert from the fit (Basin and Range blocks have 5% to
    7% of cells with shares, VR V12), which is half of the "deserts flatter the score" risk P7 faces.
    Its cost: presences in low-canopy cells (parks, yards, open woodland, recent clearcuts) leave the
    training set. They are counted and reported by reason, never silently dropped.
- **Canada's "not available" bands.** 18 of 21 share bands are flag 3 on every Canadian cell (VR V5; HR
  item 4). Entering them as missing makes "missing" mean "Canada", so the model can learn a country
  effect from reporting habits, not habitat. Filling them is ruled out by D85 and D89 (1). Using only
  the three bands both sides share would throw away the US genus detail for the 99.4% of the box that
  has it. Masking Canada costs 102,543 cells (0.6%): the Canadian part of Strait of Georgia/Puget
  Lowland (66,806) and the whole Coastal Western Hemlock-Sitka Spruce block (35,737, all Canadian, VR
  V12), leaving 24 blocks. For the continental fit, where Canada is large, this choice cannot stand;
  that is a lesson the pilot records (RECORD -1027).
- **Total cover's seam.** The seam verdict is "artifact" on total cover, with a border step on 23 of 25
  transects (VR V6). With Canada masked there is no border inside the fit, so the artifact cannot enter.
  Inside the US, total cover is TreeMap's alone and is what turns a share into cover (the plan's own
  comparison model reads "conifer plus broadleaf cover", `plan:299-300`).
- **Tier B.** Zero everywhere in the box (VR V5, HR item 9). Constant inputs carry nothing.
- **`ecm_hosts`.** Above 0 on 99.1% of US cells with shares (VR V5), so as a yes-or-no it barely varies;
  its size does vary, block means 0.46 to 0.99 (HR item 8). It equals the sum of the genus shares within
  7.8e-8 (HR item 4), so it adds a sum a tree model finds hard to build itself. D131 leaves "whether the
  total or single genera enter the fit" to T7. It earns its place by the same test as the genera.
- **The floor at 0.01.** HR item 8: `share_Lithocarpus` is above 0 on 17,859 cells from 45 to 49 N,
  north of tanoak's range, and `Larix` on 33,516 cells from 40 to 43 N and 36,882 west of 122 W, each
  with a mean share that rounds to 0.000; INFERRED cause, TreeMap's plot imputation. HR: "A T7 term that
  reads a share as presence (share > 0) would treat these cells as hosted. A term using the share's size
  is barely affected." A tree model splits wherever it gains, including at 0.0001, which turns a size
  into a presence test. A 1% floor removes exactly the values HR flags as unreliable and keeps every
  share that means more than a tree or two in a 250 m cell (INFERRED).
- **D129 "each" read literally.** D129 says the new bands "enter any fit under D121, each kept only if it
  improves held-out years" (`DECISIONS.md:11`). Testing each of eight bands alone follows those words.
  The word "years" is a reading question, raised under P7.

**Sources.** VR V5, V6, V12 (`VR:92-124`, `:126-148`, `:216-253`); HR items 4, 8, 9, 11
(`HR:110-125`, `:176-227`, `:265-299`); D74, D85, D89, D121, D129, D131; `t6b_hosts.py:32-41`;
`t6b_layers.py:107` (`TREE_BANDS`, 24 bands, now on main).

**Alternatives considered.** Undefined shares as missing or as zero (above). Canada in, with the three
shared bands only, as one model for the whole box (keeps 0.6% of cells, loses genus detail everywhere).
Canada in, with missing values (country leak). All eight new bands as one block test (fewer
comparisons, against D129's "each"). No floor (HR's out-of-range cells read as hosted). A floor at
0.005 or 0.02 (no data favours one over 0.01 more than weakly; 0.01 is the round figure).

**For the owner.** The map covers US forest only, where the tree layers say what grows; open country,
towns and the Canadian corner are left blank and labelled, and each new tree type stays in only if it
makes the map better at places it has not seen.

## P5. Model family and package

**Recommendation.** LightGBM 4.7.0, already pinned (`pyproject.toml:17`), objective `binary`
(presence 1, background 0) with the P3 weights, and the T1 code's settings (`deterministic`,
`force_row_wise`, every seed 20260918; `src/forager_forecast/t1_model.py:64-87`). Two constraints on
`log_effort`:
- `interaction_constraints` puts `log_effort` in a group of its own, so no tree branch mixes effort
  with a habitat input;
- `monotone_constraints` makes the prediction rise with effort, never fall.

The comparison models (P7) use the same family, settings and tuning, so a difference is the inputs'.

**Reason.**
- With effort kept apart, the model's score is a habitat part plus an effort part. Holding effort at any
  constant then shifts every cell's score by the same amount, so the map's **ranking** does not depend
  on the value chosen (P6). Warton, Renner and Ramp 2013 state the condition: the values used for the
  bias variables at prediction "are irrelevant" when there is no interaction between observer bias and
  the environment, and if the interaction exists, no method gives a bias-free description. The
  interaction constraint builds that condition into the model rather than hoping for it.
- More effort cannot mean fewer reports, so the monotone constraint removes a way to overfit noise
  without removing anything real (INFERRED).
- LightGBM is already pinned, already used by T1 (`t1_model.py:64-87`, with `auc` at `:165`), and handles
  the presence-background contrast with nonlinear responses to shares and pH. No new dependency.
- Docs read: LightGBM's parameter page documents `interaction_constraints` ("controls which features can
  appear in the same branch") and `monotone_constraints` ("`1` means increasing"). READ at
  https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html, the 4.6.0 docs, not 4.7.0's; that both
  exist unchanged in 4.7.0 is UNVERIFIED and the build confirms it with a test.

**Does its use differ from T1's?** Yes, in four ways: presence against background instead of
report against no report in a cell-week; weights; the two constraints; and P7's block folds instead of
leave-one-year-out.

**Sources.** `pyproject.toml:17`; `t1_model.py:64-87`, `:165`; Warton, D.I., Renner, I.W., Ramp, D.
(2013) "Model-based control of observer bias for the analysis of presence-only data in ecology", *PLOS
ONE*, https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0079168, READ.

**Alternatives considered.** A penalised logistic regression or GAM (statsmodels 0.15.0 is pinned as a
dev dependency only, D106; smooth terms over 15 to 20 inputs need a design choice per input). A maximum
entropy model (a new dependency; equivalent in form to a weighted logistic model, UNVERIFIED from
memory). Random forest (scikit-learn not pinned). LightGBM without the constraints (the map's ranking
would then depend on P6's chosen effort level).

**For the owner.** We reuse the model type the project already trusts, and wire it so that how many
people searched an area can raise or lower a whole area's reports but can never reshape which kinds of
forest look best.

## P6. Effort held constant

**Recommendation.** One box-wide value: the median of `log_effort` over the frame's weather cells that
hold an eligible box cell (P4), computed once before any prediction and recorded in the manifest. A test
on the fitted model checks that the 250 m ranking is identical at the 25th and 75th percentiles of that
distribution (P5's constraint makes it so; the test shows it).

**What the output then means, for a forester:**

> Darker shading marks US forest whose host trees and soil most resemble the forest around reports of
> mycorrhizal mushrooms, once differences in how much people search have been allowed for; it ranks
> places within this map only, it is not a count, an amount or a percent, and it is blank wherever the
> tree layers, the soil layer or the model's experience do not reach.

And for the two thirds of the box outside the effort frame: a forest cell there gets shading only if its
trees and soil are like forest the model was trained on (P8). Its shading is an extension from
searched forest to similar unsearched forest, not something learned there. The report says so in those
words, and the mask map shows the frame's outline.

**Reason.** D107 left the level to T7 (`DECISIONS.md:32`). Under P5's construction the level changes
the score by a constant, so the choice cannot change the map; a median is a value inside the data, so
a raw score at it is never an extrapolation in effort. A per-band value (one per 5° latitude band, D106)
would add a step the ranking does not need.

**Sources.** D107; P5's sources; VR V10 (`VR:186-194`, point 3: holding effort constant needs no
per-cell effort, so prediction outside the frame is not blocked).

**Alternatives considered.** Box-wide mean (pulled by a few heavily searched city cells). The maximum
(Warton et al.'s "ideal access" style; an extrapolating value for most cells). A per-latitude-band
value. Prediction at each cell's own effort (that is a map of reports, not habitat; rejected).

**For the owner.** We pretend every place was searched equally hard, so the shading shows how good the
forest looks, not how many people go there.

## P7. Validation

**Recommendation.**
1. **Blocks and folds.** Level III ecoregions (D125), burned by cell centre with the mask's own rule (VR
   V12). With P4's Canada mask, 24 blocks take part. **Leave one block out:** 24 outer folds; each
   presence and background point is predicted once, by the fold that held its block out. A leakage test
   checks that no point of a held-out block reaches its fold's fit (`plan:324`).
2. **Minimum per block: 30 presences** after P2's thinning, fixed now, before any count. A block under
   it is "uninformative": its own figure is not read, and its points stay in the pooled figure (D125).
   30 is D33 (2)'s per-fold minimum for T1 (`DECISIONS.md:99`), carried over because nothing about a
   habitat model argues for a different number and a fixed number from an existing rule cannot be
   tuned to counts.
3. **The forested-block cut, fixed now from layer counts.** A block is "forested" if at least 15% of its
   study cells have shares (canopy at least 10%). From VR V12's counts this gives **18 forested
   blocks**: 17 at 40% or more, plus NW Great Plains at 20.5%. The seven below are Northern Basin and
   Range 7.4%, Wyoming Basin 6.6%, Central Basin and Range 5.3%, Central California Valley 4.6%, Columbia
   Plateau 3.9%, NW Glaciated Plains 1.8% and Snake River Plain 1.4%. Any cut from 7.5% to 20.5% gives
   the same 18; 15% sits in that gap. With Canada masked, Coastal Western Hemlock-Sitka Spruce Forests
   (98.4%, all Canadian) drops out, so **17 forested blocks** take part.
4. **Metric.** The pooled out-of-block AUC (presence against background, weighted as in P3), computed by
   `t1_model.auc`'s rank-sum formula (`t1_model.py:165`) extended for weights. Reported: pooled over all
   24 blocks; pooled over the 17 forested blocks only; per block (uninformative marked); and a level I
   summary beside (D125).
5. **Comparison models**, same family, folds and tuning:
   - **A, effort only:** `log_effort`;
   - **B, forest only:** `log_effort` plus conifer cover and broadleaf cover (share times total cover).
   Both include effort, so the full model's lead over B is the genus and soil detail, not effort. The
   full model's lead over each is the pooled AUC difference.
6. **Bootstrap.** 1,000 resamples clustered by 0.1° weather cell, seed 20260918 (D31; D104 and D105
   cluster by cell the same way), giving a 95% interval for each difference. A second interval
   clustered by block is printed beside, without a verdict, because 24 blocks are few and spatial
   correlation runs farther than one weather cell (INFERRED).
7. **Tuning (D31).** A grid written into the repo and committed before any fit: 20 random
   configurations, chosen per outer fold by inner grouped 4-fold (by block, training blocks only)
   weighted log loss. Proposed grid: `num_leaves` 15, 31, 63; `min_data_in_leaf` 50, 200, 1,000;
   `learning_rate` 0.03, 0.1; `feature_fraction` 0.7, 1.0; `lambda_l2` 0, 10; `num_boost_round` 200,
   500. The full model and both comparisons are tuned this way. D129's eight add-one tests and the side
   runs (M2's, the licence track, the comparison group) reuse each fold's chosen configuration of the
   full model, to keep the fit count bounded.
8. **Held-out years.** Not a fold. A table beside: the pooled out-of-block AUC split by the presence's
   year (background shared), to show whether the result rests on one year. No verdict.
9. **Side runs, fixed now, reported beside, never dropped after results:** M2's "unclear genera in" run;
   the CC0/CC BY licence track (`SPEC.md:91`); the comparison group (M4) on the same design.

**Reason.**
- "Deserts flatter the score" (`plan:125-129`), in numbers: seven blocks under 8% forested, including
  the two largest (VR V12). A pooled AUC can reward a model for telling sagebrush from forest. P4's mask
  removes most desert cells; the forested-block score removes what is left of the contrast between
  desert blocks and mountain blocks. Fixing the cut from canopy counts now, before any presence is read,
  means it cannot be chosen to flatter the result.
- AUC fits the question "does the model rank held-out presences above held-out background", needs no
  calibration (none is claimed at 250 m, D12, R8), and the project already has the code.
- The comparison models answer `plan:298-300`: whether the full model adds anything beyond "where the
  forest is" and "where people search".
- Tuning per outer fold, as D104 did for T6, keeps the held-out score honest. Fit count, INFERRED, for
  the three tuned models: 24 outer x 4 inner x 20 configurations = 1,920 fits each, 5,760 in all; the
  rest about 24 each. Time per fit is unmeasured (VR V13: no fit allowed), so the build times one trial
  fold before the planner schedules the run against `t6b-night`.

**On D121 and D129's "held-out years".** D121 admits a layer if it "beats the same model without it on
held-out years under the D33 evaluation"; D129 repeats "held-out years" for the new bands. T7's layers
are static and its validation is by block (D125, TASKS.md T7's Verify). **This list reads "held-out" as
held-out level III blocks for T7.** That is a reading of two owner rulings, not a ruling; it goes to
the owner (decision 3 below).

**Sources.** D31, D33 (2), D104, D105, D121, D125, D129; VR V12 (`VR:233-253`); `t1_model.py:89-109`
(T1's inner choice, by year), `:165`; the block percentages above are the verify report's printed counts
divided, nothing re-read.

**Alternatives considered.** Level I blocks (5; too few, D125 rejected them). Grouping small blocks
into larger folds (D125 fixes blocks as level III). Brier or log loss as the headline (scores
calibration, which a presence-background model does not have). A continuous Boyce index (presence-only;
UNVERIFIED from memory, not read here; could be printed beside later). Clustering the bootstrap by
block as primary (24 clusters give a rough interval). Tuning once on all blocks (leaks the held-out
block into the configuration). A forested cut at 40% (17 blocks before Canada; drops NW Great Plains,
which is a grassland block whose forest patches are a real test).

**For the owner.** Each of 24 ecoregions is hidden from the model in turn and the model is scored on
it; it has to beat a "where people search" model and a "where the forest is" model, both over the whole
box and over the forested regions alone, so that telling forest from desert cannot win it the score.

## P8. Area of applicability

**Recommendation.**
- **Method:** the CAST package's approach (Meyer and Pebesma 2021), written in Python: each input scaled
  (subtract the training mean, divide by the training standard deviation), weighted by the full model's
  gain importance, then the dissimilarity index (DI) of a cell is its distance to the nearest training
  point divided by the mean distance between training points. **`log_effort` is left out** (it is held
  constant for the map, P6, and is not a habitat input).
- **Training points** for the distance: all presences plus the 500,000 background points, each fold's DI
  taken against points outside its own block (the cross-validation rule).
- **Threshold:** set from those cross-validated training DIs, by the rule of the **published** paper,
  which the build reads and quotes before writing code. Fixed and committed before any map value is read.
- **What a masked cell shows:** transparent (R5, `SPEC.md:72`). In the mask file it carries its own code,
  distinct from P4's codes (P9).
- **Counted:** cells in and out, by side, block, and inside or outside the effort frame.

**Reason.** It is the method on record (`EVIDENCE.md:56`, `RESEARCH_LOG.md:56`), and the plan names it
(`plan:85-89`). Excluding effort keeps the mask about trees and soil. The frame split counts how much
of the map is extension into unsearched forest (P6).

**Sources.** CAST vignette https://cran.r-project.org/web/packages/CAST/vignettes/cast04-AOA-tutorial.html,
READ (first 100,000 characters): the DI "is calculated that is based on distances to the training data
in the multidimensional predictor variable space"; "we weight variables by the model-derived importance
scores prior to distance calculation"; the AOA uses "a threshold based on the DI observed in the
training data using cross-validation"; it cites Meyer, H., Pebesma, E. (2021),
https://doi.org/10.1111/2041-210X.13650 (*Methods in Ecology and Evolution*; the publisher page refused).
The preprint, arXiv 2005.07939 (https://arxiv.org/abs/2005.07939), READ (abstract): DI "based on the
minimum distance to the training data in the predictor space", "weighted by their respective importance",
threshold "at the .95 quantile of the DI in the training data". **UNVERIFIED, from memory:** that the
published version replaced the 0.95 quantile with an outlier rule on the cross-validated training DI
(the upper whisker, 75th percentile plus 1.5 times the interquartile range), and that DI divides by the
mean training distance and scales by standard deviation. Hence "the published rule, read first" above.

**Alternatives considered.** A per-input range check (a cell is out if any input is beyond the training
range; cheap, misses unusual combinations). A fixed DI value chosen by eye (not fixed before reading).
Including effort in the distance (would mask unsearched forest for being unsearched, which is P3's job
and already handled).

**For the owner.** Wherever a forest's mix of trees and soil is unlike anything the model learned
from, the map stays clear instead of guessing.

## P9. Outputs

**Recommendation.** Under `/mnt/work/forecast-data/t7/pnw-<run date>/` (not the flash drive, which is
the live run's and had 5.7 GB free, VR V13), each with sha256 and size in the report:

| File | What |
|---|---|
| `relative_habitat_pnw.tif` | float32, master grid (ESRI:102008, 250 m) window over the box, the full model's raw score with effort at P6's value; NaN where masked. About 100 MB uncompressed (VR V13), written by tile |
| `applicability_pnw.tif` | uint8 codes: 0 outside study area or box; 1 in (shaded); 2 out of the area of applicability; 3 Canada, pilot; 4 no host shares (canopy under 10% or under half valid); 5 no soil pH; 6 water or unmapped. About 26 MB |
| `block_report.csv`, `block_report.json` | per block: presences, background points, informative or not, forested or not, AUC and interval for the full model and both comparisons; pooled figures and how pooled; level I summary; D129's add-one table; the by-year table; side runs |
| `mask_map.png` | the box: shaded cells in five equal-count classes, codes 2 to 6 in muted greys, the effort frame's outline, level III boundaries. Legend "lower" to "higher relative habitat", no numbers |
| `manifest.json` | input hashes (each tree and soil tile's manifest line and sha256, the mask, the level III file, D26's zip, T6's ten stored files, the membership list's sha256), code commit, seed, background cell list sha256, tuning grid sha256, chosen configurations, P4's floor, P6's effort value, P8's threshold, licence track, attribution |

Small evidence (tables, logs, scripts as run) goes in `docs/audits/<date>-t7-fit/` in the repo; rasters
stay out of git (START_HERE, "Docs hold decisions and pointers, never bulk data"). **Attribution** is
built from the tile tags and filtered to the sources the output actually read; with Canada masked
(P4) that means no SCANFI value reaches the output, and the manifest says which sources were read and
which were not (VR V14 found the PNW render's list omits SCANFI). No file or label carries a percent,
"sighting chance", a forbidden term (D58) or any edibility word (`SPEC.md:25`, R8).

**Reason.** VR V13: prediction must stream by tile; outputs belong on `/mnt/work`. The raw score keeps
the full information; five unnumbered classes show a ranking without inviting anyone to read a number
as a chance (R8, D12). A rank from 0 to 1 was rejected because it reads as a percent.

**Sources.** VR V13, V14; D12, D58, D107 (manifest pattern), R5, R8.

**Alternatives considered.** Writing to the flash drive (the live run's). Storing a 0 to 1 rank (reads
as a percent). One mask code for all exclusions (hides why a cell is blank).

**For the owner.** Everything lands in one dated folder on the work disk with a receipt of exactly
which inputs and settings made it, and the picture shows five shades from lower to higher with no
numbers on them.

## P10. The bar for showing it (M8)

**Recommendation.** Fixed now, before the fit. The habitat map **passes** only if both hold:
1. On the pooled held-out blocks (all 24), the full model's AUC is above comparison model A's and above
   comparison model B's, each difference with a 95% bootstrap interval (clustered by weather cell, seed
   20260918) wholly above zero.
2. The same two differences, pooled over the 17 forested blocks only, each with an interval wholly above
   zero.

Reported beside, no verdict: per-block results; the block-clustered intervals; the comparison group's
map against the group's (rank correlation over shaded cells); the licence track; M2's side run; the
by-year table. If it fails, the report says "not shown" (D33 (5)'s wording) and nothing is shown. If
it passes, nothing is shown either until the owner decides (M8 (a), RECORD -1030).

**Reason.** The same form as D5 and R2 (beat the baseline on held-out data with an interval excluding
zero), with the forested-block condition so that the deserts cannot carry the result. Two baselines,
because beating "where people search" is easy and beating "where the forest is" is the real test of a
mycorrhizal habitat map (`plan:298-300`). A threshold on the comparison group's correlation was
considered and left as a printed figure: no source or data says what value would mean "too similar".

**Sources.** D5, D33 (5), R2 (`SPEC.md:63-65`), D60 ("Trust is in operability, not promises"), RECORD
-1030 (point of no return 3).

**Alternatives considered.** Beating comparison A only (too easy). An AUC floor such as 0.7 (a number
with no source behind it for this design). The pooled condition alone (deserts can carry it).

**For the owner.** The map is only ever a candidate to show if it beats both simple stand-ins, across
the whole box and across the forests alone, by a margin that is clearly not luck.

## New code T7 needs that does not exist yet

Found missing by the verify report or here; none of it is written.

1. **A 250 m cell to its 0.1° weather cell**, through `t6b_mask.cell_lonlat` then `cells.cell_for`
   (VR V11: "No production code maps a master-grid cell to a weather cell today", `git grep cell_for(`
   finds record paths only). With a test of ties.
2. **A level III code per master cell.** The mask stores none (VR V12, `t6b_mask.py:111-114`); T7 burns
   level III itself with `t6b_mask._burn`'s rule (`t6b_mask.py:130`).
3. **A static effort per weather cell:** expected outings summed over the frame's 573 weeks, from the
   stored surface. `EffortSurface.effort` is per cell-week only (`effort.py:618`); nothing aggregates
   it (read here, `effort.py` function list).
4. **Reading genus names** from D26's download: the loader reads `acceptedTaxonKey` and `genusKey` only
   (`records/occurrence.py:52`, VR V16); `genus`, `family`, `order` are in the file (VR V16).
5. **The membership join**, with the list's sha256 checked before use (`plan:319-322`). Waits on M1.
6. **Presence thinning and weighting** per P2 and M3. Waits on V9.
7. **A predictor reader that streams by tile** over the box's tree tiles, soil tiles and mask, applying
   P4's entry rule and floor, and recording each cell's exclusion code (VR V13).
8. **The background sampler** inside the frame and P4's mask, seeded, writing its cell list.
9. **Block folds, the leakage test, and the nested tuning loop** by block (T1's `inner_choice` is by year,
   `t1_model.py:89`).
10. **A weighted AUC and the weather-cell-clustered bootstrap for an AUC difference.** `t1_model.auc` is
    unweighted (`t1_model.py:165`); T6's cluster bootstrap (`effort.py:577`) weights deviance by cell.
11. **The area of applicability in Python.** CAST is an R package. Needs a nearest-neighbour search
    over hundreds of thousands of training points for every eligible cell; scipy 1.18.1 is in the lock
    only as LightGBM's dependency (`uv.lock:402-403`), so using it directly means pinning it in
    `pyproject.toml` (an owner-visible dependency change, small).
12. **The raster and mask writer** on the master grid window, by tile, and the manifest.
13. **Attribution from the tile tags**, filtered to what was read (VR V14; `pnw.py:44-53` omits SCANFI).

Item 7's band names now exist on main: `t6b-host-genera` was merged in `b9127e5`, so `TREE_BANDS` is the
24-band layout (`t6b_layers.py:107`), which closes VR's "premise that was wrong" 1.

## Decisions the owner must make, in plain words

Each is a choice in the proposals above; the recommendation comes first.

1. **Where the comparison points come from (P3).** Recommended: only from places where someone has
   reported any fungus, about one third of the box, with search effort allowed for. Alternative: the
   whole box, which needs a new rule inventing an effort figure for two thirds of it.
2. **What happens to land the tree layers say nothing about (P4).** Recommended: leave it off the map
   and say why (open country, towns, under 10% canopy, no soil reading). Alternatives: let the model
   treat it as "unknown", or as "no host trees".
3. **Reading "held-out years" as "held-out regions" for T7 (P4, P7).** D121 and D129 say a layer earns
   its place on held-out years; a map of trees and soil does not change by year, so the test that makes
   sense is held-out ecoregions. Recommended: yes, for T7, recorded as a reading in its decision row.
4. **Canada in the pilot (P4).** Recommended: left out of the pilot map (0.6% of the box), because 18 of
   its 21 tree bands do not exist there; the continental plan has to solve this properly.
5. **The 1% floor on tree shares (P4).** Recommended: yes, so a stray tree placed out of its range by the
   source cannot mark a cell as host forest.
6. **Each new tree type tested one at a time (P4).** Recommended: yes, as D129's words say.
7. **The forested-region cut and the 30-report minimum (P7).** Recommended: a region counts as forested
   if at least 15% of it has tree canopy (18 regions, 17 after Canada), and a region needs 30 reports
   before its own score is read. Both fixed now, before any count.
8. **The bar (P10).** Recommended: beat both simple stand-ins over the whole box and over the forests
   alone, each clearly. Passing shows nothing by itself; the owner still decides.
9. **Pinning scipy directly (new code 11).** Recommended: yes; it is already installed as part of the
   model package.

M1 (the list and its licence), M2, M3 and M4 stay with V9 (P1, P2), and the permission request to the
list's authors (RECORD -1037 (3)) is what unblocks them.

## Confirmed vs inferred

- **Confirmed (READ here):** the plan's propose section (`plan:269-311`); VR V5, V10 to V13, V16; HR
  items 4, 8 to 11; D31, D33, D85, D89, D101 to D107, D121, D125 to D132; `effort.py:618-621`;
  `filters.py:176-200`; `t1_model.py:64-109`, `:165`; `pyproject.toml:17`; `uv.lock:402-403`;
  `t6b_layers.py:107`; `t6b_hosts.py:32-41`; no `origin/*` row at D133 or above; the five web sources
  as cited.
- **Computed here:** the forested percentage per block, by dividing VR V12's printed counts (no data
  read).
- **Inferred:** that every R6 presence lies in the frame (P2, to be counted); that tree-model splits at
  tiny shares act as presence tests; the fit count; that the block-clustered interval is rougher;
  that a 500,000 draw samples one eligible cell in several.

## Could not determine

- How many cells are eligible under P4 together with the frame (needs a pass over the tiles; not run,
  documents only).
- Fit and predict time and memory (no fit allowed); hence the trial fold.
- The published AOA threshold rule and DI normalisation (publisher page refused; the preprint says 0.95
  quantile; the rest is UNVERIFIED memory).
- That LightGBM 4.7.0 keeps the two constraint parameters as in 4.6.0's docs.
- Anything about any group's records (held).

## Premises that were wrong

1. VR's "premise wrong" 1 (the base lacks the 24-band code) **no longer holds**: main `b9127e5` merged
   `t6b-host-genera`; `TREE_BANDS` at `t6b_layers.py:107`.
2. The dispatch to this session said `ecm_hosts` "barely varies". Its presence barely varies (above 0
   on 99.1% of US cells with shares, VR V5); its size runs from 0.46 to 0.99 in block means (HR item 8).
   P4 treats it accordingly.
3. The plan's comparison model "host-tree totals only (conifer plus broadleaf cover)" (`plan:299-300`)
   would not include effort, so it would lose to the full model partly for lacking effort. P7 gives both
   comparisons effort; stated as a reading.

## Decided beyond scope

- Read five public pages (LightGBM docs, CAST vignette, the AOA preprint abstract, Warton et al. 2013,
  Phillips et al. 2009's index record) to cite sources rather than memory. Nothing downloaded.
- Proposed P8's exclusion of effort from the distance, P4's floor and P9's mask codes, none of which the
  plan asked for by name.

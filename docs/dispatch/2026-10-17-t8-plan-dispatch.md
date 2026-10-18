# Dispatch 2026-10-17-T8P: write the T8 plan (the weather trigger model and the joint challenger) for the owner's rulings; nothing downloaded, counted or fitted

Written by the planner (Rowan Waymark), 2026-10-17, for Ash Transect, this repository's coder (profile `docs/process/coder-profile.md`). Forager RECORD: intent -1248; direction -1027; T7's outcome -1247.

## Authorisation

The owner, verbatim: "Go on T8 when ready". Under -1027 every task goes: plan, then the owner's rulings, then a go, then the build, then an independent review (D18), then a merge on the owner's word (D40). This dispatch is **the plan only**.

## Writing rule

Describe products generically. Commits end with `Co-Authored-By: Claude <noreply@anthropic.com>` and no model name.

## Change

One plan document, `docs/dispatch/2026-10-17-t8-trigger-plan.md`, on branch `t8-plan` (from main `f99dbcbf`), pushed, with no PR. It is laid out like the T7 plans (`docs/dispatch/2026-10-15-t7-mycorrhizal-habitat.md` on t7-mycorrhizal-plan; `docs/dispatch/2026-10-17-t7-strengthen-plan.md` on t7-strengthen-plan). It ends in **numbered decisions for the owner, each with a recommendation**, written so a non-programmer can choose.

## Read first (from source, cite file and line)

- **The task and the spec:**
  - `docs/planning/TASKS.md`, T8 and T9;
  - `docs/planning/SPEC.md`, especially R3 (what calibration means), the "Trigger windows are learned from records" decision, and the Unverified and Open questions sections;
  - `docs/planning/DECISIONS.md`, the rows touching T1, T6, T8, D33 and the PNW pilot.
- **T1, the calendar smoke test:** `docs/audits/2026-09-18-t1-*.md` and `2026-09-20-t1-move-review.md`. What did T1 find about weather adding skill over the calendar? T1 was the premise TASKS.md says must hold first.
- **T6, the effort surface,** and its review (`docs/audits/2026-10-06-t6-*.md`), including the open question "are lichens fit as T8's benchmark?" and how it was ruled.
- **The PNW pilot's scoring route** and its lessons: `docs/audits/2026-10-10-pnw-pilot-scoring-report.md`, and Forager RECORD -1034/-1035, where the weather archive lags about a week, so a week can only be scored near its end.
- **T7's outcome** (Forager RECORD -1229, -1230, -1246, -1247; reports on t7-refit, t7-refit-review, t7-refit-review-2). What it teaches T8:
  - reporting effort and road access dominate where reports fall;
  - the strict bar P10b was set before the result;
  - two independent reviews were run.
- **-1027's folded-in checks:** D33 (3) and (4), sensitivity and the commercial-safe run.

## What the plan must settle (each as a decision with a recommendation, or a premise to check)

1. **The question T8 answers,** in R3's terms: what a "trigger" predicts (the chance a group is reported in a weather cell and week), and over which region and years. The PNW first, per -1027.
2. **The group or groups:** the mycorrhizal group T7 used, the saprotroph comparison group, chanterelles as in T1, or another. Name what each costs and what it can show.
3. **The weather windows:** which variables (rain, temperature, soil moisture and so on), which lags, how the window search is done, and the randomisation check that guards it against picking noise. All of it is fixed before any search is run.
4. **Effort:** how T6's surface enters, so a "trigger" can't be just more people out on wet weekends. Use T7's lesson: the bar must see through effort.
5. **The joint challenger:** what it is, and how it is compared on held-out years and ecoregions.
6. **The bar, fixed before any result is read:** T8's pass condition, written as strictly as P10b, including an effort-only comparison and held-out years.
7. **Habitat:** T7 stopped with no habitat claim (-1247). Should T8 use no habitat input, use T7's layers as a nuisance covariate only, or something else? And what replaces T9's dependence on T7 (TASKS.md T9 "Depends on: T7, T8")?
8. **The archive lag:** what that does to a usable weekly forecast, and whether T8 should be judged as a now-cast or a forecast.
9. **Data and cost:**
   - what's already in the store under `/mnt/work` and on the T6b drive, and what would need fetching (sources, licences quoted at source, sizes);
   - compute time on the shared laptop, given T6b's nightly runs.
10. **The points of no return:** where in T8 the count and the fit happen, so the owner's words can be asked at each.
11. **Review:** two Sorrel reviews on models other than Opus (Fable and Sonnet), as for T7.

## Scope boundary

- **May touch:** branch `t8-plan`, worktree `~/Zynergy/forager-forecast-t8-plan`, the plan file only.
- **Must not touch:**
  - downloads of any kind;
  - counts of presences (the first point of no return);
  - fits (the second);
  - publishing;
  - main;
  - other branches;
  - `/mnt/work` beyond reading listings and manifests;
  - t6b and `t6b-night`;
  - Forager's RECORD and this repository's audits index (the planner writes those).
- Small read-only probes of existing files are fine (sizes, date ranges, column names). State each one.

## Baseline (premises to re-check)

- main is at `f99dbcbf`, holding the Ash profile merge.
- TASKS.md says "T7 to T11 | Not started | Not written yet". That is stale for T7; check what it says now.
- T1 reported before any other model work, as TASKS.md requires.
- The PNW pilot's weekly scoring uses Copernicus ERA5-Land and ERA5 hourly through the route in the scoring report.

## Predictions

- **Outcome (planner):** a plan with 8 to 12 owner decisions. The biggest are the group, how effort enters, and what replaces T9's dependence on T7. The plan recommends starting with one group on the PNW and an effort-aware bar.
- **Mechanism (Ash):** at the top of the plan, before the body.

## Stops

- a premise wrong in a way that changes T8's shape (for example, T1 found no weather skill at all);
- anything that would need a download, count or fit to answer. Write it as a decision instead.

## Finish line

The plan pushed to `t8-plan`, and a short final message: the decisions list in plain words, what you couldn't determine, the premises that were wrong, and every call beyond this dispatch.

# T8 plan: STOPPED at the premise check, before the plan was written

**Status:** this file is **not the T8 plan.** It records a stop under the dispatch's own stop rule and
asks the owner one question. The plan is written after the owner answers.

**By:** Ash Transect (coder, `docs/process/coder-profile.md`), 2026-10-18 UTC.
**Dispatch:** `docs/dispatch/2026-10-17-t8-plan-dispatch.md` (t8-plan `b603c37`). Forager RECORD intent
-1248; the owner's words: "Go on T8 when ready".
**Nothing was downloaded, counted, fitted or published.** No file under `/mnt/work` was opened.

## Why this stopped

The dispatch's Stops section reads: "a premise wrong in a way that changes T8's shape (for example,
T1 found no weather skill at all)". RECORD -1248 repeats it as an abort condition: "a premise that
changes T8's shape (such as T1 finding no weather skill)".

T1 found no weather skill in the only box it was run on. That is the named example.

## The premise, read from source

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

## Why it changes T8's shape

TASKS.md's T8 is "search the windows with randomisation checks, fit the trigger model, fit one
joint model, and compare both on held-out years" (`:89`). Written that way, T8 assumes the weather
signal exists and asks which windows carry it. After T1, the first question is instead whether a
weather signal survives at all in the PNW once T1's way of looking is changed. That is a second test
of a premise that failed once, and it needs to be planned as one: what is different from T1, why
that difference could matter, and a bar that accounts for this being the second look at the same
records. Writing the original T8 plan would build on a premise the record says failed.

## The question for the owner

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

## Premises in the dispatch, checked

- **main is at `f99dbcbf`:** holds. `origin/main` = `f99dbcbf`; t8-plan = `b603c37`, one commit (the
  dispatch) on top.
- **TASKS.md says "T7 to T11 | Not started | Not written yet":** still says so at `TASKS.md:20`.
  Stale for T7, which was fitted twice and stopped (RECORD -1247).
- **"T1 reported before any other model work":** in form, yes (T1's fits ran 2026-10-11, T7's
  later). In substance, the premise T1 tested did not hold. That is this stop.
- **The pilot's scoring uses Copernicus ERA5-Land and ERA5 hourly:** not re-checked, since the stop
  came first.

## Not done, because of the stop

The eleven items the dispatch asks the plan to settle (the question, groups, windows, effort, the
joint challenger, the bar, habitat and T9, the archive lag, data and cost, points of no return,
reviews). The T6, PNW-scoring and T7 reports were not read in full. Ash's mechanism prediction for
the plan is not written, because the plan's shape depends on Q1.

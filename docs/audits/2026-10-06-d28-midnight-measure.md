# D28: the midnight measure, fixed before any count

Answers Part 1, step 1 of `docs/dispatch/2026-10-06-d28-date-rule.md` (Forager RECORD -601, -602).
Written 2026-10-06 (UTC) by the coder session on this laptop (D38), branch `d28-date-rule`, worktree
`~/Zynergy/forager-forecast-d28`, base `origin/main` `41005c1` plus the dispatch commit `df3456e`
(`git fetch origin` this session: `origin/d28-date-rule` = `df3456e`, observed). **Committed before any
midnight count was read.** No count of midnight records by dataset, on any day, has been opened in this
session. The one midnight figure already on record, 30 records on the 1st across the whole download
(`2026-10-06-d27-d29-completion-report.md:66`, re-derived in the review), was read in those reports
before this measure was written; it is a whole-download total and says nothing about any dataset or
about other days. `tables_0012112/day_of_month_by_dataset.csv` carries a per-dataset column for
midnight on the 1st; it has not been opened in this session.

## The question

The owner's provisional "keep the midnight check" drops a record whose clock time is exactly 00:00:00
on the 1st of a month. Per dataset: **is midnight on the 1st special, or is midnight common on every
day for that source?** If the 1st carries more than its calendar share of a dataset's midnight records,
midnight there looks like a filled-in default. If it carries about its share, midnight is a habit of the
source on every day, and the check would remove only the 1st's slice of that habit.

## What is counted

- **Population.** Every record the loader can type (`records/occurrence.py`, `record_from_row`), at the
  source stage, before any filter, by `datasetKey`. The same population as D95.
- **Timed record.** `event_time` is not None: the eventDate carried a clock time.
- **Midnight.** `event_time == time(0, 0, 0)` as the loader parses it: a `Z` or offset suffix is dropped,
  so it is midnight as written, not converted; a fractional second other than zero is not midnight; a
  same-day range keeps its start's time. This is the clock half of `is_default_date`
  (`records/filters.py:87-89`), so the count describes exactly the records the midnight check drops.
- **Per dataset:** timed records (T); midnight records on any day (M); midnight on day 1 (k); midnight
  on days 2 to 31 (M − k); and, as a control, timed records on day 1 that are not at midnight, against
  all timed records not at midnight.
- **Also counted, informative only:** for each step list (`t1_steps()`, `r6_audit_steps()`), how many
  midnight-on-the-1st records clear every filter before the date step (the date step is the last
  filter in both lists, `filters.py`). Only these can move a survivor count.

## How "expected" is computed

If midnight on the 1st is no more common than midnight on any other day, a dataset's M midnight
records fall on the 1st in proportion to how often the 1st occurs in the calendar: 12 of 365.2425 days
a year. So the expected day-1 share of midnight records is **p0 = 12/365.2425 = 0.03285**. This is the
rate on days 2 to 31 carried over to the 1st: given M, a per-calendar-day rate taken from the other
days, times the 1st's calendar days, gives M × p0 on the 1st. It is D95's calendar share; D95's 1/30 is
not used here because D28 worded 1/30 for date-only records, and the calendar share is what "the other
days" gives exactly.

Shown beside each row and used in no verdict:
- the share against 1/30 (D95's reference);
- the **own-calendar share**: the day-1 share among the dataset's timed records not at midnight. A
  source that records on the 1st often at every time of day (a survey calendar) will show it here too;
  if both are high, the excess belongs to the 1st, not to midnight.
- the **any-day midnight share**, M / T: how common midnight is for that source on any day.

## The test (D95's style)

- A dataset needs **M ≥ 300** midnight records to be tested (expected on the 1st about 9.9).
- **One-sided exact binomial**: p-value P(X ≥ k) for X ~ Binomial(M, p0), by
  `binomial_upper_tail` in `records/date_quality.py` (the function D95 used, re-derived by the review).
- Family level **0.01, Bonferroni** over the datasets tested.
- **Verdicts:**
  - **midnight on the 1st is special (clear excess):** significant, and the 95% Clopper-Pearson
    interval's lower end is at least 2 × p0. At twice the expected share, at least half the 1st's
    midnight records are in excess of the other days, so the check removes more defaults than real
    times (D95's reasoning carried over).
  - **small excess on the 1st:** significant but below that.
  - **midnight is common on every day (not special to the 1st):** not significant.
  - **too few to test:** M under 300.
- A whole-download row (all datasets pooled) is shown under the same arithmetic and is not a verdict.

## What this does not do

No rule is changed; `records/filters.py` is untouched in Part 1. The binomial test assumes independent
dates; real records cluster on survey days and seasons, which makes it flag excesses more readily, never
less (as `2026-10-06-d27-d29-completion-report.md` notes for D95; inferred, not measured). The verdict is
for the owner's ruling on the midnight check; it applies nothing.

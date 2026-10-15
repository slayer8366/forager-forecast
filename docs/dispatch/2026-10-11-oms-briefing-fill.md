# Dispatch: fill the OMS briefing's TO FILL lines from the actual figures

Written by the planner (Rowan Waymark), 2026-10-11. The briefing is docs/briefings/2026-10-12-oms-briefing.md on pnw-pilot-plans; the owner reads it before the Monday 2026-10-12 meeting. It must not reach the owner with any TO FILL left. Every figure is a premise to re-derive or to quote with its source.

Writing rule for everything you write: describe other products, services and device makers generically or by what they do. Don't discuss the rule; just write that way. The briefing is for a person, not a programmer: plain language, figures with their meaning.

## Sources, in order of authority

1. The independent review, pass 2: forager-forecast pnw-pilot-t1-review 79b8b17, docs/audits/2026-10-10-pnw-pilot-t1-review.md, "## Pass 2".
2. The builder's report: pnw-pilot-t1 (f73b800 or later), docs/audits/2026-10-10-pnw-pilot-t1-report.md, and the comparison JSON files under ~/Zynergy/forecast-data-pnw-pilot/fits/.
3. Forager RECORD.md on records-after-173: -854, -855, -861, -862, -863. These give the gate override, the corrected daily count, the demo ruling, the corrected route figure, and the banner wording.
4. The scoring output, once published (pnw-pilot-scoring). If it hasn't published when you finish, leave those lines as "pending: scoring publishes later today" and say so. That is not a TO FILL.

## Task

- Fill each TO FILL. For each one, cite the source file and line in a comment or a sources list, and say whether you re-derived the figure or quoted it.
- The headline is the all-years result only (D33): it did not beat the seasonal calendar, with the interval below zero. State it plainly, beside what the pilot is still worth. Don't spin it.
- D33 (3) is pending (the 5,000 m list, waiting on weather for 34 points). If it hasn't finished, say it's pending.
- If any existing line in the briefing now contradicts the record, list it. Don't rewrite it; the owner rules on wording.
- Commit and push on pnw-pilot-plans. Report the count of TO FILL before and after, and every line you couldn't fill.

## Stops

A figure that two sources disagree on; anything needing a new claim beyond the sources; a wrong premise.

# Dispatch: score the PNW pilot's full model for 2026-W41 (scoring step 4)

Written by the planner (Rowan Waymark), 2026-10-11. Runs once models/primary_t1_1000m_full/model.json exists from the builder's all-years run (pnw-pilot-t1). Assumed base: pnw-pilot-scoring at 60c4285, worktree ~/Zynergy/forager-forecast-pnw-scoring. Verify both against the remote, and merge the current pnw-pilot-t1 in (merge, never rebase). Every claim below is a premise to re-check.

Writing rule for everything you write: describe other products, services and device makers generically or by what they do. Don't discuss the rule; just write that way.

## Premises (from the planner handoff and the scoring report)

- Week 2026-W41 (week start 2026-10-05). Copernicus weather only (RECORD -819); no Open-Meteo value in any output.
- One command: `uv run python scripts/pnw_pilot_publish.py --kind full --repo-copy`, adding `--beats-calendar` and `--t1-result` from the builder's report. It needs `copernicus_sources` in the model.json.
- The full file passes 1 MB and stays outside the repo (scoring/out/). The calendar floor was re-published at 5d2ce36 (2,618 cells, 231 from a land neighbour).

## Task

0. **Verify, then report by message before running:** the model.json fields; whether it carries the land-route gate failure and the owner's override (Forager RECORD -854) as the builder wrote them; the `--beats-calendar` and `--t1-result` values you would pass, each quoted from the builder's report with its line; whether the published manifest will carry the gate failure. If the manifest can't carry it, propose the smallest change: a new field, with the existing fields unchanged.
1. On the planner's go: carry the gate failure into the manifest if needed (tests first, plus one revert check under CLAUDE.md's rules), then publish. Check the output: the cell count against the calendar floor's 2,618, `validated` false, `reviewed` as the pass-2 review says (false until its verdict), `pilot` true, attribution (the GBIF citation plus the Copernicus text for the products read), and no Open-Meteo value anywhere.
2. Report: append to docs/audits/2026-10-10-pnw-pilot-scoring-report.md. Commit and push after each step.

Heavy commands run under the 5G memory cap, and never while a fit runs.

## Stops

A missing or contradictory model field; `--beats-calendar` not stated plainly in the builder's report; a wrong premise; anything that would change a published field's meaning.

## Not in scope

The site drop (separate dispatch); the review; the builder's code.

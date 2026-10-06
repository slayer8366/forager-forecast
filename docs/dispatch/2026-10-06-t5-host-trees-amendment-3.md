# T5 dispatch, Amendment 3: the owner's answers to the T5 review's findings

Filed by the T5 coder session on 2026-10-06 from the message the Forager planner session sent it.
The planner's text is quoted whole below. The amendment is recorded in the Forager repository as
RECORD -594. It answers `../audits/2026-10-06-t5-review.md` (origin/t5-review at `20eda69`), which
was merged into `t5-host-trees` first.

> Planner: Amendment 3 to T5, Forager RECORD -594, after the independent review (origin/t5-review at 20eda69, docs/audits/2026-10-06-t5-review.md; read it in full). First merge origin/t5-review into t5-host-trees, so its added test at tests/test_t5_layer.py:426-439 comes with it. The owner's answers, verbatim:
> 1. F1, "Fix the rule, record both (Recommended)": the null for each variable is built from the same transects as its border step (matched counts). Fix seam.py, add a test that fails on the old rule with unequal counts (for example 7 against 24 at the review's 0.165 false-alarm rate), and re-run. Record the old and new verdicts side by side with the reason, in an appended section.
> 2. F2, "Cap at the fitted size (Recommended)": a diameter beyond the species' Bechtold Table 1 fitted range takes the crown width at the largest fitted diameter. No tree is dropped silently. Count the capped trees and any non-positive widths that remain, with a test that fails on the 29 dropped redcedars' case.
> 3. F3, "Use SCANFI's own total (Recommended)": fetch SCANFI v2 2025's total crown closure for the strip to the flash drive (windowed, small; record the request in docs/pulls/). Use it as Canada's total, with the ten-layer split for the shares, as D88 does for the US. Report the sum against the total on the strip before switching. Re-run.
> File D90 to D92 for these, quoting the owner. Correct the F5 slips with appended, dated notes; don't edit. Tests first, the strict revert runner, full suite. Push, and end with a short report of all three results and the new transect table.

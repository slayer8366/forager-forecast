# Dispatch: survey of new data for a third PNW test (read-only research)

Written by the forecast planner (Alder Bearing), 2026-10-25, for Juniper Sounding (read-only research, Fable).
The owner chose "New data, then retest" after the PNW's second "no" (forecast RECORD 2026-09-28-2052), and said
"Yes" to starting this survey. Branch `new-data-survey`, cut from main at 98d4b33. Under D133 (7) there is no
third weather test on these records without new data and the owner's word. This survey finds out what new data
exists. It doesn't choose the data or design the test; the planner's plan does that, and the owner rules on it.

**You change nothing.** No edits to code, data, decisions or the record. No bulk downloads, no counts and no fits.
You may fetch a small sample (under 50 MB per source, 500 MB in total) only where a source can't be judged
without one. List every sample with its URL, size and time. Scratch goes under `/mnt/work/scratch/new-data-survey/`,
never /tmp and never under `~/.cache`: the root disk has about 1 GB free. Keep any one process under 1 GB of
memory (`systemd-run --user --scope -p MemoryMax=1G -p MemorySwapMax=0 nice -n 10`). Don't touch `t6b-night` or
anything under `~/Zynergy/forecast-data/`.

**Read first** (this branch): `docs/audits/2026-10-21-pnw-finding.md`; `docs/audits/2026-10-21-t8-fit/`
(results.md, review-fable.md, review-sonnet.md); `docs/planning/SPEC.md`, `DATA_REGISTER.md`, and D12 and D133
in `DECISIONS.md`. These say what the first two tests used, what the forecast's number means, and where the
reviewers thought the design may have missed a weather signal. Check every premise in this dispatch against
them. Where one is wrong, say so first in your report.

**What to find.** For each, give the PNW (WA, OR, ID, northern CA, southern BC) coverage, years, spatial and time
resolution, how it is accessed, and its licence and terms **quoted at source, with the URL**:

1. **Effort and absence.** Sources that record who searched where and when, or "searched, found nothing":
   foray and club lists, surveys and monitoring plots, checklist-style apps, agency fungal surveys. Our number
   leans on "someone reported a fungus there that week" standing in for effort (D12). Anything better is the
   most valuable find.
2. **More chanterelle presences** beyond what the register says we already use: herbaria and other aggregators,
   club records, published datasets. Say how much each one overlaps what we have, if you can tell.
3. **Weather and ground measures the first two tests didn't use**: for example fog and cloud drip, snowpack and
   melt timing, finer or station-based rain and soil moisture, and soil temperature at depth. Tie each to a
   specific weakness the reviews named, where one fits (for example the 2021 rain extrapolation).
4. **Anything that would let us check the 2024–25 jump**, for example whether coordinate-uncertainty reporting
   changed (review-sonnet.md finding 6).

**What not to do:** don't rank sources into a plan, propose a model, or set any thresholds. Facts and licences
only, with your own reading of fit marked as inferred.

**Report:** `docs/audits/2026-10-25-new-data-survey/report.md` on this branch. Commit it and push it as you go:
a rough commit beats lost work. End your commit messages with "Co-Authored-By: Claude <noreply@anthropic.com>".
Start with any wrong premises, then one table row per source (name, what it holds, PNW coverage, years,
resolution, access, licence quote and URL, inferred fit to items 1 to 4). Mark every claim read, fetched or
inferred. End with what you couldn't confirm or reach, and why. Then add one row to `docs/audits/README.md`.

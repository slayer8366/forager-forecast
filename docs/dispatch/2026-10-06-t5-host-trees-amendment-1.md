# T5 dispatch, Amendment 1: the owner's answers to the Part 1 survey, and Part 2's go

Filed by the T5 coder session on 2026-10-06 from the message the Forager planner session sent it.
The planner's text is quoted whole below. The amendment is recorded in the Forager repository as
RECORD -587. This copy exists so the build cites a file in this repository and not a relay. The
dispatch it amends is `2026-10-06-t5-host-trees.md`. The survey it answers is
`../audits/2026-10-06-t5-source-survey.md`.

> Planner: Part 2 has the go. T4 is merged into forecast main as 74c7f3b. The owner's answers to your survey are Amendment 1 to the T5 dispatch, Forager RECORD -587. Verbatim:
> 1. BIGMAP: "Yes, it's cleared (Recommended)". File a decision row quoting the IIPP statement with its URL and read time; D31 is not edited. BIGMAP isn't used in T5.
> 2. US source: "TreeMap 2023". File a row, recording the Archive's CC-BY terms as quoted (attribution; don't present a modified version as the original), and how the attribution is carried.
> 3. "Flag missing in Canada (Recommended)": genera from TreeMap on the US side. Where SCANFI can't supply a genus (Tsuga, Quercus, the missing Pinus), mark it not available on the Canadian side with the source flag, and carry conifer and broadleaf totals for both sides. The host genera need a cited source. Find one (a primary or review paper) and record it, or say the list is unverified.
> 4. "Keep it masked (Recommended)": Alaska stays masked.
> 5. "Canopy share both sides (Recommended)": the US share is crown cover from TreeMap's tree list, matching SCANFI's crown closure. Propose the crown-cover formula from the tree table with a cited source before building it. If none is defensible, stop.
> Decision rows start at D83.
> **Data:** the laptop has about 4 GB free, so TreeMap's 4.87 GB zip goes on the USB flash drive the owner named: /run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t5/ (31 GB free; the folder exists). Point a gitignored data/t5 at it, or pass the path. Read through /vsizip or extract on the flash drive only, never to internal disk. If the drive isn't mounted, stop. Don't touch other folders on that drive. One download at a time; nothing else is downloading.
> Merge origin/main (74c7f3b) into t5-host-trees first, so you build on T4's grid.py and regrid.py. Then follow the dispatch's Part 2: verify first and report the strip width and transect plan, the crown formula and the host-genus source by message, and carry on unless something is a stop. Tests first, revert checks with the strict runner, full suite before and after. Commit and push as you go. Your final message is the completion report.

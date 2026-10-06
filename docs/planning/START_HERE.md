# Start here

As of 2026-09-18.

## Where things stand

Planning is complete enough to start. The owner is sending this pack to code agents to begin work in the
repo (D13). The author has not read the repo. The goal is a calibrated weekly sighting chance per forager
group and area, shown on a North America map only where the model beats a seasonal calendar.

Decisions agreed so far (full rows in DECISIONS.md):

- The target is a sighting chance per forager group, weather cell and week (D12). It is not a map of
  patches, and it is not a fruiting probability.
- North America is one pipeline and one grid. Each ecoregion switches on only after it beats a calendar
  baseline on held-out years.
- The model is habitat x trigger x observation, with one joint model kept as a challenger.
- Order of work: chanterelles first, chicken of the woods beside them as a control, morels as two models
  for spring 2027, then king boletes. Matsutake is on hold.
- Delivery is PMTiles on Cloudflare, set up separately through Cowork, with MapLibre on the client.
- Planning lives in the planning doc. Spec and task files live in the repo once building starts.

Next up: T0, then T1 to T3. T1 is the task most likely to overturn the plan, so it runs before any
pipeline work.

## Fixed terms

These words keep one meaning everywhere: in the spec, the code, the manifest and the map. If a sentence
needs one of them to mean something else, the sentence is wrong.

| Term | Meaning | Never means |
| --- | --- | --- |
| Sighting chance | The chance a forager group is reported in a weather cell and week, given at least one fungal observation of any kind there that week | The chance mushrooms are present, or the chance you will find them |
| Calibrated | Of all cell-weeks given 30%, about 30 in 100 have a report, checked on held-out years | Accurate for one spot or one trip |
| Relative habitat | The 250 m shading inside a weather cell. It ranks places and carries no percent | A probability |
| Forager group | A genus-level group such as chanterelles, with the species name stored | A single species |
| Calendar baseline | A model that sees only day of year and region | A forecast. It knows nothing about this year's weather |

## Working rules

- Append, mark, preserve. A published claim that turns out wrong gets a new dated row that quotes the old
  wording. It is never quietly edited.
- Every fact carries one of three flags: verified (source opened), abstract only, or from memory.
  From-memory items wait in the RESEARCH_LOG queue until someone checks them.
- Ideas stay in IDEAS.md until a test result moves them to DECISIONS.md. A good argument alone does not
  promote an idea.
- A task with no observable result is not a task. Each one names the check that proves it landed.
- Thresholds belong to the weather product they were fitted on. Never carry a number across products
  without refitting.
- No em dashes, plain words, short sentences.

## How we work

- One task, one session. Name the task, read this file, that task's dispatch, and only the rows needed.
- Docs hold decisions and pointers, never bulk data. Data stays out of git.
- Who decides what. The implementer decides names, formats and the order of small steps, and logs them.
  Anything that changes scope, cost, licenses or what users are told goes to the owner as a proposed row
  and waits for a yes.
- Every session ends the same way: update task status, add a session log row, say what was not checked.
- The forbidden terms never reach the Forager repo (D58). "fruiting probability", "probability of finding"
  and "chance of finding" are not committed to slayer8366/Forager in code, strings, docs or commit
  messages, other than inside a rule or test that names them as forbidden. Before any forecast copy
  lands there, rerun the check in docs/audits/2026-09-21-d55-vetting-report.md and report the counts.

## Session log

| Date | What was done | What is next |
| --- | --- | --- |
| 2026-09-18 | Evidence review, lag atlas published, North America data stack chosen, species order agreed, planning doc created, sighting chance named and confirmed (D12), planning pack exported for the repo (D13) | Code agents run T0, then T1 to T3 |
| 2026-09-18 | Pack landed in the zynergy-site repo at Forager/mushroom-forecast/ with content unchanged (commit b707cbe, branch claude/forager-forecast-planning-pack), verified byte-identical to the export. Site README points here. T0 verify-first facts reported to the owner. Not done from T0: .gitignore and the project layout proposal, because zynergy-site is a static Cloudflare Pages site with JavaScript functions and no Python, so it cannot host T1 to T3. Where that code lives is open. | Owner merges the branch and names the repo for T1 to T3 |
| 2026-09-18 | T0b: private repo forager-forecast stood up on main. Pack copied from the site branch at c8e8ce3, byte-identical (2fcb3c0). Added docs/audits with index and three filed records, .gitignore, a 1 MB large-file guard as pre-commit hook and CI step, the two Forager verify scripts copied at 175b050 and extended for T1, the T1 amendment, and a uv Python skeleton (3.14, rasterio 1.5.1, pyproj 3.8.0, locked) with lint-and-test CI, green on its first run. Found: GDAL Python bindings do not pip-install here but do from conda-forge; on Open-Meteo's archive, models=era5_land serves no precipitation, era5_seamless serves ERA5-Land temperature and soil with ERA5 precipitation, and the default is a third product; DECISIONS.md ends at D13 while dispatches cite D15 to D18. Report: docs/audits/2026-09-18-t0b-completion-report.md | Owner: close the site branch; rule on the weather product for T1 (D7), the GDAL toolchain and the licence; export D14 to D18. Then T1 to T3 |
| 2026-09-18 | T3 (branch t3-verify-data-layers, base main f96d557): opened the primary source for every Memory or Not-checked register row and all 17 research-log items; 21 log rows added, 12 items ticked, 5 left unticked with the dead end logged; 31 register cells got the verified value appended beside the old one. ESRI:102008 accepted by the installed PROJ and GDAL. Open-Meteo free tier is non-commercial by its terms; POLARIS and BIGMAP state no licence; BIGMAP covers the coterminous US only. Report: docs/audits/2026-09-18-t3-verify-data-layers-completion-report.md | Owner: rule on the commercial-use question (Open-Meteo plan, POLARIS, BIGMAP) before T4 uses a layer. Reviewer files the T3 review. T4 and T5 wait on both |
| 2026-09-18 | T2 on branch t2-record-audit from main f96d557. Verify-first answered with sources: GBIF's iNaturalist dataset is research grade only, carries no identification count or agreement, and marks user-obscured records with `informationWithheld` and a 26 to 29 km uncertainty; none of Cantharellus, Laetiporus, Hygrophoropsis, Omphalotus or Craterellus has a taxon geoprivacy on iNaturalist. Built against synthetic fixtures, 65 new tests green, ten revert checks: the shared GBIF download request (docs/pulls/gbif-fungi-north-america-2015-2025.json, DWCA), the four-step R6 filter pipeline with counts, the count table, and the seeded 200-record sampler. Not done: the count tables and the real CSV, because the download needs GBIF credentials this machine does not have. Report: docs/audits/2026-09-18-t2-record-audit-completion-report.md | Owner: create a GBIF.org account and set GBIF_USER, GBIF_PWD, GBIF_EMAIL, then submit the committed request; rule on the proposed one-query iNaturalist pull for the sample; then T2 runs the pipeline and the person does the photo hand check |
| 2026-09-18 | T2 credentialed run: download DOI 10.15468/dl.k3mwnn (provisional, test account) requested with the committed template, count tables by group, region, year, step, license and publisher produced; the taxon-less duplicate key measured at 42 percent of Cantharellus records; hand-check CSV blocked on the iNaturalist-pull ruling, seed fixed at 20260918 (docs/audits/2026-09-18-t2-credentialed-run-report.md). | Owner rules on the duplicate key, the iNaturalist pull and the licence gate; review of both run reports under the standing protocol. |
| 2026-09-18 | T1 on branch t1-calendar-smoke-test from main f96d557. Verify-first done as far as the machine allows: no GBIF credentials here, so the download (item 1) is blocked and no model was fit; the predicate, filters, cell-week labels, weather windows, archive URL builder (models=era5_seamless, elevation=nan, cell_selection=nearest) and the two named tests landed (ac12f55, 54 tests). Item 2: variables confirmed live; free tier fits about 34 cells a day, so the weather pull needs a ruling; rain is shared by 4, 6 or 9 cells (6.25 average). lightgbm 4.7.0 pinned after a 3.14 wheel check. Report: docs/audits/2026-09-18-t1-calendar-smoke-test-completion-report.md | Owner: supply GBIF_USER, GBIF_PWD, GBIF_EMAIL; rule on proposed D24 (weather pull), D25 (cell-level requests), D26 (one DWCA download for T1 and T2); then T1 pulls, filters, counts and fits. Review per the standing protocol |
| 2026-09-18 | T1 credentialed run: GBIF credentials proven, download DOI 10.15468/dl.hdkjmn (provisional, test account) requested with the fixed predicate, count tables by box, year, filter step and license produced, premise holds under its literal reading in both boxes and is thin in the PNW for 2015 to 2018 (docs/audits/2026-09-18-t1-credentialed-run-report.md). | Owner reads the premise table and rules on the default-date rule; modelling waits. T2 download running. |
| 2026-09-21 | Forager-app's proposed D55, the artifact contract, copied into docs/audits byte-identical to Forager-app ecfcbde (blob 86e54c5) and vetted against main 82f28b6 and MapLibre Native at tag android-v13.6.1: all six of its premises hold, two sentences in its Reason column are corrected. Filed as D55 and accepted with those two edits as D56 on the owner's delegation of 2026-09-21. Branch d55-artifact-contract. Nothing built; the app built its own "no forecast published yet" source on its side (Forager-app 16246bf). | Owner merges d55-artifact-contract, or overturns D56 with a new row. T11's dispatch, when written, cites D55 and D56. The commercial-use ruling (D29, open) still gates any forecast layer in the app. |
| 2026-09-21 | Owner named the target of the artifact contract: the existing Forager app is the product and Forager-app is the research bench (D57, quoting the owner). Forager's map stack re-read at 89f53a4: MapLibre 13.5.0, same offline download source, PR #4290 contained, so D55's offline argument transfers. Appended to the vetting report; same branch d55-artifact-contract. | Owner merges the branch. A T11 dispatch checks D55's client assumptions against Forager, not Forager-app. |
| 2026-09-21 | Forager checked for the forbidden terms at origin/main 89f53a4: zero hits for "fruiting probability", "probability of finding", "chance of finding" and thirteen adjacent phrasings; two plan lines list a fruiting forecast as refused, none names a number. Standing rule added above and recorded as D58, quoting the owner. Report section appended; same branch d55-artifact-contract. | Owner merges the branch. Any agent about to put forecast copy into Forager reruns the check first. |
| 2026-09-21 | Owner ruled Forager's own rules out of scope for this project (D59, quoting the owner): they are being changed to fit the integration and redone afterwards. D58 stands narrowly as what this project's agents may not commit to Forager; the report's notes on Forager's plan and vocabulary are observations, not instructions. Same branch d55-artifact-contract. | Owner merges the branch. |
| 2026-09-21 | Owner stated the principle behind D59 (D60, quoting the owner): Forager's refusals reflect confidence in the shipped product, and evidence of effectiveness, not a decision, is what makes them out of date. "Trust is in operability, not promises." For the forecast that gate is D5 and R3. Same branch d55-artifact-contract. | Owner merges the branch. |
| 2026-10-01 | Owner ruled that Forager is not sold and ships the full model on records of every licence (D61, quoting the owner), and that this repository opens up (D62). D61 answers D29's gate and replaces the commercial-safe ruling of 2026-09-28, which was never filed here. Rows, release checklist notes and the filing report (docs/audits/2026-10-01-decisions-d61-d62-report.md) are on branch decisions-d61-d62, unmerged. | The owner's written authorisation to merge decisions-d61-d62 (D40). Before the repository is made public: the history check (release checklist item 3) and the owner's word on identifiers in filed reports. A SPEC.md sync for D61 (lines 85 and 123 to 126). The licence (D22) is still open. |
| 2026-10-01 | The owner made the repository public (D62 carried out) and authorised the merge of decisions-d61-d62 in the words "Merge decisions-d61-d62 into main. Repo is now public". A history check was run after the change, on all 26 remote refs and 123 commits: no GBIF password and no Climate Data Store key anywhere, positive control found. Recorded in the appended section of docs/audits/2026-10-01-decisions-d61-d62-report.md. | The licence (D22): a public repository with none can be read and not reused. The owner's view on the identifiers now readable (GBIF username, account email, commit author address). A SPEC.md sync for D61. The release checklist's item 3 again once business accounts exist. |
| 2026-10-06 | D32 follow-up on branch d32-followup-unify-filters from main 1d5bd80. Verify first found four stops; the owner answered them (D64 to D67, relayed by the Forager planner). Built: one Record type with a loader that counts the 9,627 rows of T2's download it cannot type, one filter pipeline with T1's and the R6 audit's step lists, nearest-point cells with exact ties toward +infinity on the decimal value at 0.1 and 0.25 degree, DWCA-only download requests, the old T1 path kept frozen as evidence. Tests 97 to 109 functions, 12 revert checks, every count difference over both downloads explained. Not checked: the new request body against GBIF, the unified T1 list on one download. Report: docs/audits/2026-10-06-d32-followup-completion-report.md | Independent review of the branch (D18), then the owner's merge authorisation (D40). Then D26's download |
| 2026-10-06 | D26 on branch d26-shared-download from main ad64fef. Records owed from the D32 merge filed (D68 to D71, the 117 test-count correction). Verify first found GBIF's GADM country tag missing on 61,508 US and Canada records, 29,904 inside the T1 boxes, and the disk too full; the owner chose tag, else country field (D72) and the planner freed space. Built d26_predicate, download_status and fetch_download, region renamed outside_t1_boxes with no count change; tests 117 to 123 functions, nine revert checks. One download: 0012112-260928105237408, DOI 10.15468/dl.8jxmeb, 2,493,578 records, provisional, read in place. Acceptance: 1,194,729 of 0005709's 1,195,034 keys in the box subset; the 305 missing are all gone from GBIF. Every step-count difference against 0005714 split by geography, snapshot or reinterpretation, except the duplicate steps. Not checked: why the tag is missing, why iNaturalist withdrew the 305. Report: docs/audits/2026-10-06-d26-completion-report.md | Independent review of the branch (D18), then the owner's merge authorisation (D40). Then D27 in full, D28's day-of-month table, D29's dataset list |
| 2026-10-06 | T4 on branch t4-master-grid from main ad64fef. Verify first stopped on depth, range and area; the owner ruled D80 (0 to 30 cm, thickness-weighted), D81 (Q0.05 and Q0.95 carried, approximate, master grid only) and D82 (45.5 to 49.0 N, 121 to 125 W). Built the master grid (ESRI:102008, 250 m, lattice at the false origin, uint32 cell id) and an exact area-weighted regrid in place of GDAL's average, which differed by up to 0.50 pH on the real geometry. One SoilGrids fetch (9 VRTs, sha256 match), master grid, zoom-9 PMTiles archive (891,388 bytes, sha256 84905e33...). Ten-cell check 10 of 10, largest difference 0.00062 pH. Tests 117 to 162 functions, 20 revert checks, 19 bite. Not checked: the datum pin (no test fails when reverted), the tile pixels against a publisher checksum (ISRIC gives none), pmtiles.io in a browser. Report: docs/audits/2026-10-06-t4-completion-report.md | Independent review of the branch (D18), then the owner's merge authorisation (D40). The 0.5 valid-fraction threshold is the builder's choice and awaits a word |

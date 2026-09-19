# Pulse: what is the Forager repo, and could it host the forecast model work?

**Date:** 2026-09-18
**Type:** read-only pulse, answered from the repo. Nothing was written, committed or branched in Forager.
**Base:** Forager origin/main at 175b050a0a507afb74686285c87fb36f72b9b548, fetched that day. The
worktree read from sat at the same commit, zero behind and zero ahead.
**Filed by:** T0b (docs/dispatch/2026-09-18-t0b-forecast-repo-bootstrap.md). The answer is the one
given to the owner in chat that day, with headings added; the substance is unchanged. The pulse as
received follows it. The owner's ruling on it is D15: a dedicated repo, this one.

Every claim names a file and line on 175b050, or is marked inferred. Kotlin paths are relative to
app/src/main/java/com/zynergylabs/forager/app/. The T0 line the pulse rested on was confirmed but
imprecise: scripts/ holds two Python files among twelve.

---

## The answer

### 1. What Forager is

An Android app that ranks which species are worth looking for in a chosen region and month, from
how often people have logged them on iNaturalist; not limited to fungi, at README.md:5-9. The README
states it is "a historical-frequency ranking over real observation data, not a weather-style
forecast or a fitted model", at README.md:11-14. What ships: one APK from a single Gradle module,
settings.gradle.kts:17, applicationId com.zynergylabs.forager.app, minSdk 26, targetSdk 37, at
app/build.gradle.kts:243-245. CI publishes the debug APK as an artifact, ci.yml:390-402. One server
piece is deployed for the app: a Cloudflare Worker serving vector tiles for the offline map style,
server/pmtiles-worker/README.md:13-16, referenced at map/OfflineStyle.kt:18. No other platform. The
README does not mention Google Play; the build file describes applicationId as the app's identity
on Play at app/build.gradle.kts:214.

### 2. Head, date, size

Head is 175b050, "Merge pull request #100", committer date 2026-09-12 06:26:49 -0700. GitHub reports
the repo public, created 2026-08-15, last push 2026-09-18.

| Measure | Value |
|---|---|
| Commits on main | 628 |
| Tracked files | 651 |
| Tracked content at head | 18.1 MB |
| Packfile | 12.14 MiB |
| GitHub disk usage | 13,173 KB |

Largest tracked files: app/src/main/assets/databases/fungi_index.db 4.22 MB,
data/species-index/fungi-us-species-index.json 2.38 MB, data/species-index/_raw/merged_counts.json
1.35 MB, _raw/names_by_id.json 1.25 MB, then four fonts at 0.42 to 0.53 MB, then
ui/availability/AvailabilityScreen.kt at 0.31 MB.

### 3. scripts/

Twelve files: two Python, ten bash.

| File | What it does |
|---|---|
| build_fungi_species_index.py | Builds the species-index JSON from iNaturalist, paced to the API's published limits, lines 2 and 16-20 |
| generate_fungi_index_db.sh | Regenerates the Room .db asset from that JSON by running a real Room database through the test task, lines 2-11 |
| measure-night-inversion.py | One-off luminance measurement of basemap tiles for a night palette; needs Pillow, lines 2 and 27 |
| setup-android-sdk.sh | Installs cmdline-tools, platform 37.1, build-tools 37.0.0; CI runs it at ci.yml:90 |
| verify-codeowners-placeholders.sh | Fails while CODEOWNERS has a placeholder; kept out of CI by design, line 12 |
| verify-design-tokens.sh | Greps for theme and motion token violations; kept out of CI, line 7 |
| verify-inaturalist-access.sh | Reachability of the iNaturalist site and API |
| verify-lichen-exclusion.sh | Live check that iNaturalist honours without_taxon_id |
| verify-open-meteo-fields.sh | Live check of forecast fields, including hourly soil variables |
| verify-open-meteo-historical-fields.sh | Live check of archive fields, with backoff on 429 |
| verify-policy-permissions.sh | Privacy policy against manifest permissions and applicationId |
| verify-usgs-basemap.sh | Live check of USGS tiles, coverage and zoom ceiling |

Python version: both scripts use "#!/usr/bin/env python3" and nothing pins a version anywhere.
Features used are f-strings and "from __future__ import annotations" with tuple[int, int] hints at
measure-night-inversion.py:34,79, which run on 3.7 and up. Dependencies: no requirements file,
pyproject, Pipfile, lock file or environment file exists anywhere outside build directories.
Pillow is the only third-party import, stated in a docstring at line 27 and guarded at lines 44-46;
the index builder is standard library only. A third Python file,
docs/audits/2026-09-08-path-home-ratio-discriminators.py, says "no dependencies" at line 1. CI's
only Python is an inline standard-library script that summarises JUnit XML, ci.yml:165-388;
nothing in scripts/ runs in CI except the SDK installer.

### 4. CI

One workflow, .github/workflows/ci.yml, one job, "Build, test, publish APK", on pinned
ubuntu-24.04 with a 45-minute timeout, lines 41-47. Triggers: push to main, and every pull request
with no branch filter, lines 8-15. Concurrency is per ref with cancel-in-progress everywhere except
main, lines 23-25. Steps in order: full-history checkout, JDK 21, Gradle cache, Robolectric jar
cache, SDK via the repo's script, assembleDebug, an APK version check, testDebugUnitTest, the
Python summary with a skipped-test allowlist, then APK and report upload. Wall-clock from GitHub
for the last eight runs on main was 3.9 to 8.0 minutes, and 4.8 to 6.9 minutes for the last eight
PR runs, measured 2026-09-18.

Whether Python tests would slow or break it, stated structurally and marked as inference, not
measured: a step inside this job runs serially after the Gradle steps and consumes the same
45-minute budget; a second job in the same file runs on its own runner in parallel, and the
workflow's result becomes the AND of both; a separate workflow file gets its own concurrency
group. The job installs no Python and uses the runner image's python3, line 165. CODEOWNERS routes
only motion paths, .github/CODEOWNERS:12-14, and the PR template's mandatory section applies only
to those, PULL_REQUEST_TEMPLATE.md:11-14, so a Python folder would have no owner routing and no
template section.

### 5. .gitignore and data conventions

The root file has 39 lines: IDE and Gradle outputs, lines 1-12; *.gpx by owner decision because
the repo is public and a track is a trace of where someone walked, lines 14-17; keystores and
signing.properties except the debug keystore, lines 19-26; .claude/, lines 28-33; a Gradle daemon
file and *.stackdump. There is no rule for data folders, models, downloads, notebooks, virtualenvs,
__pycache__ or .pyc. One nested file, server/pmtiles-worker/.gitignore, ignores node_modules/,
dist/, .wrangler/. No .gitattributes, no LFS objects, zero notebooks tracked. The existing
convention for data is to commit it: data/species-index/ holds the derived index and a _raw/ cache
of API responses so the index can be regenerated without re-querying,
data/species-index/README.md:24-26 and the "Regenerating" section at line 86, and the 4.2 MB
database asset is committed. The only exclusions are privacy and secrets driven.

### 6. Docs, decisions, dispatches

Several conventions exist; the current one is docs/audits/.

- Audits hold 82 files, 66 of them dated September, indexed by one table row per entry in
  docs/audits/README.md, 97 rows; a later audit supersedes an earlier one rather than editing it,
  lines 10-13. Filenames end in -prebuild-report, -completion-report, -pulse, -findings,
  -decisions or start with ruling-. Example pulse: docs/audits/2026-09-06-light-budget-pulse.md,
  whose header states type, date, base commit and "every claim names a file and line", lines
  9-12. CLAUDE.md names that index as the serialization point every dispatch appends to.
- Dispatches in September live in docs/plans/2026-09-09-beta-dispatches.md, five in one file with
  the base commit stated at line 4. August ones are docs/qc/dispatches/*.md with reports under
  docs/qc/dispatches/reports/, five plus ten files dated Aug 22-28, and three root-level
  *-DISPATCH.md files dated Aug 29. Root DISPATCH-REPORT.md, TRACK-PULSE.md and STATUS.md were
  last touched Sep 9.
- Pulse responses from August sit in docs/qc/pulses/reports/, eight files; the questions
  themselves were not stored. September pulses are audit files as above.
- Decision records: docs/adr/ has two, 0001-motion-precedence.md and
  0002-motion-scheme-adoption.md, shaped "ADR NNNN: title" with Status and Context sections, 0001
  lines 1-10. Other decisions are audit entries such as
  2026-09-07-ruling-path-home-self-intersection.md and 2026-09-11-way-back-route-decisions.md.
  There is no dated decision table like the pack's DECISIONS.md.
- Plans: docs/plans/, 13 files, with a status table in its README, lines 1-15. docs/phase-stack.md
  is a running nesting record.

### 7. Existing data fetching and map drawing

| What | Source | Where |
|---|---|---|
| Observations, species counts, taxa | iNaturalist REST API v1 | data/remote/INaturalistApi.kt:9, behind domain/MushroomRepository.kt:9 and domain/TaxonSearchRepository.kt:10 |
| Offline fungi name index | Built from iNaturalist by the scripts, shipped as a Room asset | data/local/fungiindex/FungiIndexDatabase.kt:26-29 |
| Recent and forecast weather: daily precipitation and ET0, hourly soil moisture at four depth bands and soil temperature at two, up to 16 forecast days | Open-Meteo forecast API | data/remote/OpenMeteoApi.kt:30-47, behind domain/WeatherProvider.kt:11 and domain/TripPlanningWeatherProvider.kt |
| Historical daily precipitation, arbitrary range, nothing else | Open-Meteo archive API | data/remote/OpenMeteoArchiveApi.kt:23-34, behind domain/HistoricalWeatherProvider.kt:25 |
| Raster basemaps | USGS imagery, OpenTopoMap, OpenStreetMap | ui/map/Basemap.kt:148,162,171 |
| Offline vector tiles and style | The repo's own Worker over a PMTiles archive in R2, built from Protomaps daily builds | map/OfflineStyle.kt:18, server/pmtiles-worker/README.md:13-16, src/index.ts:161 |
| Font glyphs | demotiles.maplibre.org | ui/map/BasemapStyles.kt:154 |
| Map rendering | MapLibre Android SDK 13.5.0 | gradle/libs.versions.toml:32,73 |
| Sun position | Computed locally from NOAA equations, no network | domain/CivilTwilight.kt:12-16 |

Not present: no terrain or elevation dataset, since elevation figures come from GPS altitude on
recorded track points, domain/ComputeTrackStatisticsUseCase.kt:14-24; no tree, canopy or
land-cover layer; no soil dataset beyond Open-Meteo's modelled soil variables. A grep across
domain/ and data/ for canopy, land cover, terrain, slope, aspect and soil returned only the
Open-Meteo hits and a log-entry substrate enum at data/local/MushroomLogEntryEntity.kt:123.

### 8. What else a D14 decider would want

- A small version of T1's question already exists in the app. FruitingLagDistribution tests a
  rule-of-thumb lag window, FRUITING_LAG_DAYS = 7..21 at domain/FruitingPatternAssumptions.kt:54,
  against real iNaturalist sightings and Open-Meteo archive rainfall per region, month and taxon,
  domain/model/FruitingLagDistribution.kt:24-27. The code states that nothing in the codebase has
  yet measured a correlation between weather and observation frequency and calls that "a
  separate, planned piece of work", FruitingPatternAssumptions.kt:6-7, and forbids the result from
  feeding any ranking, FruitingLagDistribution.kt:35-38. The archive verify script calls this
  feature the "seasonal fruiting-lag visualizer", scripts/verify-open-meteo-historical-fields.sh:2-3.
- Both shapes in the D14 framing already have precedent. Inside Forager: server/pmtiles-worker/ is
  a TypeScript Worker with its own package.json, lockfile, wrangler.toml and .gitignore, and
  data/species-index/ is Python-generated data with its own README. Neither is wired into CI. As a
  separate repo: the site lives in zynergy-site. The framing is not wrong on the evidence; which
  to pick is not answered here.
- A PMTiles pipeline already exists. Bucket forager-maps, Worker forager-pmtiles, Cloudflare
  account a6a899e0..., server/pmtiles-worker/wrangler.toml:1,4,18-21, with Workers Logs
  deliberately off for privacy, lines 7-13. The pack's D6 plans PMTiles on Cloudflare "set up
  separately"; the site README records that this Worker's account differs from the account
  holding the zynergy-site Pages project.
- The repo is public and tracks no LICENSE file. The pack's open-data and commercial-use
  questions land on a repo with no licence of its own.
- No Python dependency management and no version pin, as in question 3.
- Every PR runs the full Android build, five to seven minutes, and no LFS means anything
  committed goes straight into history; the largest tracked files today are already data.
- iNaturalist rate limits are already encoded at scripts/build_fungi_species_index.py:16-20,
  which matches the pack's "counts and spot checks only" constraint.
- Velocity and a known conflict point. Created 2026-08-15, 628 commits, PR #100 merged
  2026-09-12. docs/audits/README.md is 0.11 MB with 97 rows, which CLAUDE.md flags as the file
  two parallel sessions will always conflict on.

### Not checked

No script, test or build was run. The Worker being live is the README's claim, not observed that
day. CI durations are GitHub's created-to-updated wall-clock and include queue time. The three
root-level dispatch files were read only for their first line and last commit date. The
docs/audits Python file was read only for its header. Whether Play distribution exists was not
verified beyond the build-file comment.

---

## The pulse as received

# Pulse: what is the Forager repo, and could it host the forecast model work?

Read-only. No code changes, no commits, no judgment calls. Plain answers with file-and-line or command
evidence. Negative answers are complete answers ("there is no such directory").

## State this was written against

- Written 2026-09-18 by Claude, who has never read the Forager repo. Everything Claude believes about it
  comes from one line in the T0 report: "The Forager repo already has Python scripts under scripts/".
- Planning pack: zynergy-site, branch claude/forager-forecast-planning-pack, Forager/mushroom-forecast/.
- What the plan hinges on: decision D14 (proposed). Model code for T1 to T9 needs pinned Python
  dependencies, large data folders kept out of git, and its own tests. The owner must choose between a
  dedicated forecast repo and a folder inside Forager. Tell us if that framing is wrong.

## Questions

1. What is Forager? One or two sentences from its README, with the path. What ships to users from it,
   and on which platforms?
2. Branch head and date of the last commit on the default branch. Rough size of the repo and of its
   largest tracked files.
3. What is under scripts/? List the files with one line each. Which Python version do they assume, and
   how are dependencies declared (requirements file, pyproject, lock file, none)?
4. Is there CI? Name the workflow files and what they run. Would adding Python tests slow or break the
   app's existing checks?
5. What does .gitignore already exclude? Is there any existing convention for data folders, notebooks,
   model artifacts or large downloads?
6. Is there an existing convention for docs, decision records or dispatch files in Forager? Paths and
   one example of each.
7. Does anything in Forager already fetch weather, soil, terrain, tree or observation data, or draw a
   map? Paths and the data source each one uses.
8. Anything else you noticed that someone deciding D14 would want to know and did not think to ask.

## Do not

- Do not move the planning pack, create folders, or propose a layout. That comes after D14.
- Do not answer what you think was meant. If a question does not fit the repo, say so.

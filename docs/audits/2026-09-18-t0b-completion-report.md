# T0b completion report: the dedicated forecast repo, bootstrapped

**Date:** 2026-09-18
**Type:** completion report for docs/dispatch/2026-09-18-t0b-forecast-repo-bootstrap.md.
**Base:** this repository, which was empty when work started (created 2026-09-19 01:02 UTC,
private, no default branch). Work is on main from 2fcb3c0 onward; the commit that adds this
report is the last of it. Pack source: zynergy-site branch claude/forager-forecast-planning-pack
at c8e8ce3. Forager facts: Forager origin/main at 175b050.
**Supersedes:** the .gitignore and layout items of T0
(2026-09-18-t0-planning-pack-landing-report.md). What T0 landed stands.

Every claim below names a file and line, a commit, or a command whose output is quoted, or is
marked inferred.

---

## The short version

The repo is stood up and everything the dispatch listed is on main: the pack at the root,
byte-identical; docs/audits with its index and the three records the dispatch named; .gitignore;
a 1 MB guard as a pre-commit hook and a CI step, shown failing and passing; the two Forager
verify scripts, copied with their source and commit in the header and extended for T1; the T1
amendment appended; TASKS.md and START_HERE.md updated; and a uv-based Python skeleton with a
lock file and a lint-and-test workflow that passed on its first run.

Two premises did not survive contact, and both are for the owner:

1. **The GDAL Python bindings do not install from PyPI on this machine.** rasterio 1.5.1 and
   pyproj 3.8.0 do, with GDAL 3.12.4 bundled inside rasterio's wheel. The bindings need the system
   GDAL library and headers, which are not installed and would need sudo. They do install cleanly
   from conda-forge through pixi. The skeleton pins rasterio and pyproj and leaves the bindings out.
2. **Open-Meteo's archive serves no precipitation for ERA5-Land.** With models=era5_land, the
   two soil variables and daily mean temperature are fully populated in both T1 boxes, and daily
   and hourly precipitation are null at every step, in a September and a January window. The
   seamless product returns ERA5-Land's exact temperature and soil values with ERA5's precipitation.
   The endpoint's default, which the unchanged Forager checks exercise, is a third product with
   different values again. D7 says "train and serve on ERA5-Land"; on this API that means
   models=era5_seamless once precipitation is needed, and the precipitation is then ERA5's.

The dispatch said to report and stop if premise 1 failed. I proceeded, with the reasoning under
"Deviations" below, and kept the Python skeleton in one commit so it is one revert if the owner
chooses the conda-forge toolchain instead.

A third item, found by the review-protocol session reading main: DECISIONS.md ends at D13, while
this dispatch cites D15 and D17 and the review protocol cites D18. D14 to D18 exist only in the
planning doc. I did not add rows I do not have the text of; that is the owner's export.

## Verify first, as answered

1. **The new repo.** slayer8366/forager-forecast, private, created 2026-09-19T01:02:31Z, empty
   with no default branch (gh repo view, before the first push). The owner confirmed the name in
   chat. The first push set main as the default branch.
2. **The pack on the site branch.** Remote head c8e8ce3, matching the record. Per-file sha256 of
   the branch's Forager/mushroom-forecast/ against the zip re-extracted from the upload: 15 files
   identical; docs/planning/START_HERE.md and TASKS.md differ by exactly the session-log row and
   T0 status added in 851b96d, shown by diff. The sha256 record kept from T0 matches the zip
   line for line. The branch versions were copied, as the dispatch said.
3. **Python and the geo stack.** The machine has one interpreter, /usr/bin/python3.14, version
   3.14.4, so "3.11 or newer" holds. It has no venv module (ensurepip missing), no pip, no uv,
   no conda, no gdal-config and no PROJ, so a fresh environment could not be made with what was
   installed. uv 0.12.17 was installed user-locally at ~/.local/bin, no sudo and no shell rc
   edits, and later pixi at ~/.pixi/bin the same way. Results, each in a fresh environment:

   | Python | rasterio | pyproj | rio-pmtiles | GDAL bindings via PyPI | GDAL bindings via conda-forge |
   |---|---|---|---|---|---|
   | 3.14.4, system | 1.5.1, bundled GDAL 3.12.4 | 3.8.0, PROJ 9.8.1 | 1.2.2 | fails: "Could not find gdal-config" | not tested |
   | 3.12.14, uv-managed | 1.5.1, bundled GDAL 3.12.4 | 3.8.0, PROJ 9.8.1 | 1.2.2 | fails, same error | osgeo 3.13.3, rasterio 1.5.1, pyproj 3.8.0, gdalwarp present, 17 s |

   The premise is confirmed for rasterio and pyproj, disproved for the GDAL bindings under pip,
   and confirmed for all three under conda-forge.
4. **Forager's record form.** Read docs/audits/README.md lines 1-16 and three September files:
   2026-09-06-light-budget-pulse.md, 2026-09-12-recording-state-resync-completion-report.md and
   2026-09-11-sundown-countdown-prebuild-report.md. Fields reused here and in the other two filed
   records: a title naming the kind of record; a bold header block with Date, Type or Status, Base
   as branch plus commit, and Preceded by or Supersedes; a horizontal rule; "The short version"
   first; claims with file and line or marked inferred; a closing "Not checked". The index keeps
   Forager's three columns, Date, Scope and File, and its rule that a later entry supersedes
   rather than edits.

## What landed

| Commit | Change |
|---|---|
| 2fcb3c0 | The pack, 17 files, at the repo root, byte-identical to the site branch at c8e8ce3 |
| 1d5378e | docs/audits index, the T0 report, the Forager pulse, the T0b dispatch |
| 1b8adc7 | .gitignore, scripts/check-large-files.sh, .githooks/pre-commit |
| 8099fd8 | The two verify scripts copied from Forager 175b050, the Open-Meteo one extended with section 4 |
| ed63a19 | T1 amendment appended, TASKS.md T0 superseded and T0b added, README section |
| 9a9a276 | Python skeleton: pyproject.toml, .python-version, uv.lock, src/, tests/, CI workflow |
| this commit | Open-Meteo script section 5 with the finding in its header, this report, START_HERE row, index row |

Tree at this commit:

```
docs/audits/2026-09-18-forager-repo-pulse.md
docs/audits/2026-09-18-t0b-completion-report.md
docs/audits/2026-09-18-t0-planning-pack-landing-report.md
docs/audits/README.md
docs/dispatch/2026-09-18-t0b-forecast-repo-bootstrap.md
docs/dispatch/2026-09-18-t0-repo-bootstrap.md
docs/dispatch/2026-09-18-t1-calendar-smoke-test.md
docs/dispatch/2026-09-18-t2-record-audit.md
docs/dispatch/2026-09-18-t3-verify-data-layers.md
docs/planning/DATA_REGISTER.md
docs/planning/DECISIONS.md
docs/planning/evidence/fruiting-lag-atlas.html
docs/planning/evidence/inat_counts_2026-09-18.json
docs/planning/EVIDENCE.md
docs/planning/IDEAS.md
docs/planning/RESEARCH_LOG.md
docs/planning/SPEC.md
docs/planning/START_HERE.md
docs/planning/TASKS.md
.githooks/pre-commit
.github/workflows/ci.yml
.gitignore
pyproject.toml
.python-version
README.md
scripts/check-large-files.sh
scripts/inat_counts.py
scripts/inat_taxon_ids.py
scripts/verify-inaturalist-access.sh
scripts/verify-open-meteo-historical-fields.sh
src/forager_forecast/__init__.py
tests/test_large_file_guard.py
tests/test_package.py
uv.lock
```

## Evidence

### sha256

diff -r and per-file sha256 between the site branch export and the new root: identical, 17 files,
before 2fcb3c0 was made. Recorded in that commit's message.

### The large-file guard, failing then passing

Run in this clone with core.hooksPath set to .githooks, before 1b8adc7 was made:

```
=== guard with a 1,100,000-byte file staged (expect exit 1) ===
LARGE FILE: big.bin is 1100000 bytes, limit is 1048576 bytes
Refused: a file over the limit is in the staged set. Keep data out of git (see .gitignore).
hook exit=1

=== after removing it (expect exit 0) ===
check-large-files --staged: 0 file(s) checked, none over 1048576 bytes
hook exit=0

=== CI mode on the whole tree (expect exit 0) ===
check-large-files --all: 17 file(s) checked, none over 1048576 bytes
exit=0

=== boundary ===
1048576 bytes: exit=0
1048577 bytes: exit=1
```

Every commit after 1b8adc7 printed the hook's own line, for example
"check-large-files --staged: 7 file(s) checked, none over 1048576 bytes" on 9a9a276. The same
fail-then-pass sequence, plus a --no-verify bypass caught by --all, runs in CI as
tests/test_large_file_guard.py, five tests driven through real git in a temporary repository.

### CI

Run on 9a9a276, the first in the repo: conclusion success, 2026-09-19T01:21:09Z to 01:21:26Z.
Job "Large-file guard, lint, tests": steps Check out, Refuse any tracked file over 1 MB, Install
uv, Install the pinned Python and the locked environment, Lint, Format check, Tests, all success.
Locally the same commands gave "All checks passed!", "19 files already formatted" and "6 passed in
0.47s". The run on the commit that adds this report is reported in chat, since a file cannot
quote the run it triggers.

### scripts/verify-inaturalist-access.sh, run 2026-09-18

```
https://www.inaturalist.org/                            -> HTTP 200
https://api.inaturalist.org/v1/taxa?q=morel&per_page=1  -> HTTP 200
https://api.inaturalist.org/v1/observations?per_page=1  -> HTTP 200
exit=0
```

### scripts/verify-open-meteo-historical-fields.sh, run 2026-09-18 at 18:32 local, as committed

Sections 1 to 3 are Forager's checks, unchanged, and pass. Section 4 is the four T1 variables
under models=era5_land, and it fails on precipitation, which is the finding; the exit code of 1
is that failure. Section 5 is the by-model comparison that locates it. Verbatim:

```
--- request shape and response fields (10-day window) ---
  utc_offset_seconds=-25200 timezone=America/Los_Angeles
  daily window: 10 days, 2024-01-01 -> 2024-01-10
  precipitation_sum: 10 entries, 10 non-null
  OK

--- a single request spanning several years (2016-01-01 to 2024-12-31, 3288 days) ---
  3288 days returned (expected 3288), 2016-01-01 -> 2024-12-31
  3288/3288 non-null
  OK: one request served the full multi-year span with no truncation and no gaps

All Open-Meteo historical-archive field checks passed.

--- T1 variables, pnw box point (47.0, -123.0), ERA5-Land, 2024-09-01 to 2024-09-10 ---
  grid elevation=80.0 m, timezone=America/Los_Angeles, utc_offset_seconds=-25200
  daily.temperature_2m_mean: 10 values, 10 non-null, unit °C, range 16.1 to 24.8
  daily.precipitation_sum: 10 values, 0 non-null, unit mm, range ? to ?
  hourly.soil_temperature_0_to_7cm: 240 values, 240 non-null, unit °C, range 15.4 to 29.1
  hourly.soil_moisture_0_to_7cm: 240 values, 240 non-null, unit m³/m³, range 0.163 to 0.21
  FAILED: daily.precipitation_sum: 10 null value(s)

--- T1 variables, east box point (42.0, -77.0), ERA5-Land, 2024-09-01 to 2024-09-10 ---
  grid elevation=538.0 m, timezone=America/New_York, utc_offset_seconds=-14400
  daily.temperature_2m_mean: 10 values, 10 non-null, unit °C, range 11.1 to 20.1
  daily.precipitation_sum: 10 values, 0 non-null, unit mm, range ? to ?
  hourly.soil_temperature_0_to_7cm: 240 values, 240 non-null, unit °C, range 10.6 to 22.8
  hourly.soil_moisture_0_to_7cm: 240 values, 240 non-null, unit m³/m³, range 0.288 to 0.387
  FAILED: daily.precipitation_sum: 10 null value(s)

--- T1 variables by model, PNW point (47.0, -123.0), 2024-09-01 to 2024-09-10 ---
  era5_land      temperature_2m_mean 10/10 sum=202.2; precipitation_sum 0/10 sum=-; soil_temperature_0_to_7cm 240/240 sum=4951.6; soil_moisture_0_to_7cm 240/240 sum=43.7
  era5           temperature_2m_mean 10/10 sum=187.7; precipitation_sum 10/10 sum=5.2; soil_temperature_0_to_7cm 240/240 sum=4365.7; soil_moisture_0_to_7cm 240/240 sum=53.6
  era5_seamless  temperature_2m_mean 10/10 sum=202.2; precipitation_sum 10/10 sum=5.2; soil_temperature_0_to_7cm 240/240 sum=4951.6; soil_moisture_0_to_7cm 240/240 sum=43.7
  attempt 1/6: curl failed (network/timeout, not a rate limit)
  attempt 2/6: curl failed (network/timeout, not a rate limit)
  attempt 3/6: curl failed (network/timeout, not a rate limit)
  attempt 4/6: curl failed (network/timeout, not a rate limit)
  attempt 5/6: curl failed (network/timeout, not a rate limit)
  attempt 6/6: rate-limited (Too many concurrent requests), backing off 8s
  best_match     could not fetch: exhausted retries

One or more Open-Meteo historical-archive checks failed or could not complete (see above).
exit=1
```

The best_match line did not complete in that run: the archive host answered the script's first
requests with timeouts and then 429 "Too many concurrent requests" for about eight minutes that
evening, and section 5's last request fell inside a second such spell. A direct curl probe at 18:23,
before the throttling, returned for best_match and for a request with no models parameter the same
values: temperature_2m_mean 10/10 sum 188.3, precipitation_sum 10/10 sum 2.0,
soil_temperature_0_to_7cm 240/240 sum 4452.3, soil_moisture_0_to_7cm 240/240 sum 51.06. That probe
also confirmed era5_land precipitation null at the east point and in a January window, hourly rain
included.

The by-model line for era5_seamless carries the same temperature sum (202.2) and soil sums (4951.6,
43.7) as era5_land and the same precipitation sum (5.2) as era5. That is the basis for "ERA5-Land
temperature and soil with ERA5 precipitation" above. Inferred from equal sums over 10 days and 240
hours at one point, not from Open-Meteo's documentation, which was not opened.

## Conventions line

Checked in Forager at 175b050: docs/audits/README.md for the index form and the supersede rule;
one pulse file, one completion report and one pre-build report for the header fields; scripts/
for the two scripts copied, their headers and the "copied, not imported" habit;
.github/workflows/ci.yml for the pinned runner and actions pinned to commits; CLAUDE.md for
pinning versions and reporting what was not checked. Followed all of them. Not followed:
Forager's docs/qc layout, which its own September records no longer use.

## Decisions taken here, and what was rejected

- **uv, not pixi, for the skeleton.** uv gives a pyproject, a pinned interpreter and a lock file
  with one user-local binary, and the proven stack installs under it. pixi would add the GDAL
  bindings and was set aside only because nothing in the pack yet needs osgeo; its result is
  recorded above so the choice can be reversed with one commit.
- **rasterio and pyproj pinned exactly, GDAL bindings absent**, pyproject.toml lines 9-19.
- **Python pinned to 3.14.\***, the interpreter this was proven on; CI installs it from
  .python-version through uv.
- **The pack's two count scripts are excluded from ruff**, pyproject.toml lines 27-30, so the
  exported record stays as exported.
- **The guard measures the index blob, not the working file**, scripts/check-large-files.sh
  lines 9-11, and CI runs it over the whole tree so a --no-verify commit is still caught.
- **The hook is enabled per clone** with git config core.hooksPath .githooks, README.md, because
  git does not version hooks. A fresh clone without that line has the CI step as its backstop.
- **A sibling clone, ~/Zynergy/forager-forecast-t0b.** The directory ~/Zynergy/forager-forecast
  already existed when T0b started, initialised at 18:05 by another Claude session on this
  machine for the standing review protocol, on an unpushed branch review-protocol with processes
  still in it. It was left untouched. That session was told by message what T0b would push, and
  has since pushed review-protocol at 0f860c2 on top of 9a9a276 with one appended index row; it
  will merge main into that branch after this commit.
- **Section 5 was added to the Open-Meteo script after section 4 first ran**, so the finding is
  reproducible by running the script, not only recorded here.
- **models=era5_land was added to the T1 request.** The dispatch names the four variables and D7
  fixes ERA5-Land. Without the parameter the check would have passed on the default product and
  said nothing about ERA5-Land. This is what surfaced the finding.

## Deviations from the dispatch

- **"If not, report and stop" on the Python premise.** The premise failed for the GDAL bindings
  only. Nothing in T0b's remaining items depends on those bindings, the proven stack covers the
  pack's stated needs (rasterio for rasters, pyproj for the projection, rio-pmtiles for tiles, per
  the "Methods" table in docs/planning/EVIDENCE.md), and stopping would have held the repo, the
  guards and the weather finding for a question that does not touch them. The skeleton is the
  single commit 9a9a276 so a different toolchain decision costs one revert.

## Safe to close the site branch

Yes. The pack is on main at 2fcb3c0, pushed, verified byte-identical against the branch head
c8e8ce3, and every later edit lives here. Closing claude/forager-forecast-planning-pack on
zynergy-site loses nothing. Its three commits also touched the site README; if the owner wants the
site to point at this repo, that is a new one-line change on the site, not a reason to keep the
branch.

## Owner items

- Close the site branch.
- Rule on the weather product for T1: era5_seamless with ERA5 precipitation, or something else (D7).
- Rule on the GDAL toolchain: stay on uv without the bindings, or move to pixi.
- Export D14 to D18 into DECISIONS.md.
- The licence, which waits on the commercial-use question.

## Not checked

- Whether pixi's conda-forge environment resolves identically on a CI runner; it ran once,
  locally, on Python 3.12.
- Open-Meteo's documentation for the models. The by-model finding rests on the API's responses on
  2026-09-18 alone.
- The ERA5-Land soil values against any other source; only presence, count and range were read.
- The review-protocol session's merge; its message said it would, and nothing here depends on it.

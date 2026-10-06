# D26 shared download: verify-first report

Answers the "Verify first" section of `docs/dispatch/2026-10-06-d26-shared-download.md`. Written
2026-10-06 (UTC) by the coder session on the credentials machine (D38), on branch
`d26-shared-download`, worktree `~/Zynergy/forager-forecast-d26`. **Two stops are met (section 9),
so nothing is built and no download is requested.** No credential was read or used for anything
here. No Climate Data Store or Open-Meteo pull, no model fit, no merge. No secret appears here.

"Read" means opened in this session; "observed" means command output from this session; "inferred"
is marked. Line cites are to `cc57e54`, whose `src` and `tests` equal `ad64fef`'s. Counts come from
the scripts in `docs/audits/2026-10-06-d26-verify/` (saved as `.py.txt`, byte-identical to what ran
from `/tmp/claude-1000/d26/`), run between 06:40 and 06:47 UTC on 2026-10-06 against GBIF's live
index with no credentials. They are counts of GBIF's index at that time, not of any download.

Landed so far on this branch: `64ffb20`, the first records commit (D68 to D71, and the 109 to 117
test-count correction appended to the D32 follow-up completion report with an index row).

## 1. Base

- `git fetch origin`; `origin/main` = `ad64fef` (observed, `git rev-parse`). Unmoved.
- `origin/d26-shared-download` = `cc57e54` before this session's commits.
- Suite at `cc57e54`: **213 passed**; `ruff check` clean (observed). `^def test_` over `tests`: 117.

## 2. The request path

- `request_template` is at `records/gbif_download.py:100-114` and returns exactly `format` DWCA,
  `checklistKey` (the backbone, `:38`) and the caller's `predicate` (read). `submit_download_request`
  is at `:117-153`: it adds `creator`, `notificationAddresses`, `sendNotification` and POSTs with
  basic auth through `urllib` (read).
- Tests: `tests/test_records_gbif_download.py` covers the T1 predicate file, credentials, the POST
  body, the refusal path, DWCA format and the template's three keys (read).
- **Nothing builds a D26 predicate today.** `grep` over `src`, `scripts` and `tests` for `GADM`,
  `COUNTRY`, `CONTINENT`, `request_template` and `submit_download_request` finds only this module and
  its test file; the module docstring (`:11-13`) says D26's predicate is "passed to request_template
  by its caller", and no caller exists (observed).
- **Nothing polls or fetches a finished download.** No reference to the download status endpoint
  (`occurrence/download/{key}`) or to a zip fetch anywhere in `src` or `scripts` (observed). The only
  zip readers are `scripts/t1_count_table.py`, `t2_count_table.py` and `t2_withheld_wordings.py`,
  which open a local zip with `zipfile` and never extract it.

## 3. The predicate, proposed in full

```json
{
  "type": "and",
  "predicates": [
    {"type": "equals", "key": "TAXON_KEY", "value": "5"},
    {"type": "equals", "key": "BASIS_OF_RECORD", "value": "HUMAN_OBSERVATION"},
    {"type": "greaterThanOrEquals", "key": "YEAR", "value": "2015"},
    {"type": "lessThanOrEquals", "key": "YEAR", "value": "2025"},
    {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
    {"type": "in", "key": "GADM_LEVEL_0_GID", "values": ["USA", "CAN"]}
  ]
}
```

with `checklistKey` `d7dddbf4-2cf0-4f39-9b2a-bb099caae36c` from `request_template`. The first five
predicates are the T1 template's (`gbif_download.py:82-97`) without the box disjunction. No
`CONTINENT`, no licence filter. **This is the predicate D71 rules; section 4 shows it fails the
dispatch's T1-box test.**

**Where the key comes from.** Three GBIF sources, none guessed:

1. GBIF's OpenAPI description of the occurrence API, `https://techdocs.gbif.org/openapi/occurrence.json`
   (sha256 in `gbif_docs_read.sha256`), lists the search parameter `gadmLevel0Gid`, "A GADM
   geographic identifier at the zero level, for example AGO", beside `gadmGid` (any level).
2. GBIF's API downloads page, `https://techdocs.gbif.org/en/data-use/api-downloads`: "The keys are
   listed and described on the /occurrence/search API call ... Note they must be provided in
   UPPER_CASE_WITH_UNDERSCORES for the download APIs."
3. GBIF's own converter, `GET /v1/occurrence/download/request/predicate?format=DWCA&gadmLevel0Gid=USA&gadmLevel0Gid=CAN&taxonKey=5`,
   returned `{"type":"in","key":"GADM_LEVEL_0_GID","values":["CAN","USA"]}` (saved as
   `predicate-conversion.json`). The same call with `gadmGid` returns key `GADM_GID`.

`GADM_LEVEL_0_GID` is proposed over `GADM_GID`: at level 0 only country codes match, while
`GADM_GID` matches a code at any level. Their counts were not compared (not run).

**Is it available as a download predicate?** GBIF's converter emits it as a download predicate, and
GBIF's predicate search (`POST /v1/occurrence/search/predicate`, "using predicates (as used for the
download API)") accepted it, together with `not`, `isNull` and `within`, and returned counts. Not
verified: the download endpoint itself, which only a real request would show.

## 4. The small test of the tag (no download, no credentials)

All counts carry the five base filters. Source: `tag_counts.json`, `null_gadm_counts.json`,
`null_gadm_why.json`, `obscured_share.json`, `box_obscured.json`, `edges.json`.

| Query | GADM tag (`GADM_LEVEL_0_GID`) | GBIF `country` field |
|---|---|---|
| United States | 2,051,625 | 2,094,743 |
| Canada | 380,445 | 398,969 |
| Both | **2,432,070** | **2,493,712** |
| PNW box, all records (no area filter): **252,822** | 243,611 (**9,211 left out**) | 252,821 (1 left out) |
| East box, all records (no area filter): **945,486** | 924,793 (**20,693 left out**) | 945,485 (1 left out) |

For scale: the same base filters with `CONTINENT` NORTH_AMERICA give 2,555,190 today (T2's download
0005714 held 2,549,508 on 2026-09-19).

**The difference, 61,642 records, decomposes exactly** (2,493,712 - 2,432,070 = 61,508 + 149 - 15):

- **61,508 records** have country US or CA and **no GADM tag at all** (`isNull`). This is the
  difference. Nothing about where they are explains it (section 4.1).
- **149 records** have country US or CA and a GADM tag of another country. Of the 20 sampled
  (`mismatch_samples.json`): 16 are iNaturalist records in Texas or Arizona whose public coordinates
  fall just inside Mexico, with 29 km uncertainty (obscured points near the border); 4 are
  Mushroom Observer records with impossible coordinates (Russia, Antarctica at -90, Algeria at
  longitude 0.0) and GBIF's `COUNTRY_COORDINATE_MISMATCH` flag.
- **15 records** carry GADM USA or CAN and a different `country`: 3 iNaturalist records whose
  coordinates are on the US side of the Rio Grande while `country` says Mexico, and 12 Mushroom
  Observer records with a wrong `country` (Japan, Costa Rica, Brazil, "unknown or invalid") and
  `COUNTRY_COORDINATE_MISMATCH`.

No US or Canada record reaches the boxes with a GADM tag of another country: `notnull_not_USACAN`
is 0 in both boxes. **Every box record the tag leaves out is a record with no tag.**

### 4.1 What the 61,508 untagged records are

- They are not offshore and not on borders. The sample of 20 inside the boxes
  (`null_gadm_box_sample.json`) includes Amherst MA (42.40, -72.52), Front Royal VA (38.68, -78.17),
  and Akron OH (41.29, -81.50): plainly inland. Outside the boxes, Concord CA (38.0, -122.0) is
  another (`mismatch_samples.json`). GADM covers them; the tag
  is simply absent (the record's `gadm` field is empty or missing).
- **89% have a coordinate uncertainty of 20 km or more**: 54,627 of 61,508, against 181,942 of
  2,493,712 (7.3%) for all US and Canada records. In the boxes: PNW 7,547 of 9,211, East 19,179 of
  20,693. 20 km and up is the obscured-record range T2 found (26 to 29 km typical). So the missing
  tag goes mostly with iNaturalist's obscured coordinates.
- 56,271 are iNaturalist ("iNaturalist Research-grade Observations", `50c9509d…`), and 56,272 were
  last interpreted on or after 2026-09-29; the rest include Mushroom Observer records last
  interpreted 2026-09-02. But 2,113,256 US and Canada records interpreted since 2026-09-29 do carry the
  tag, so the latest reprocessing is not the cause by itself.
- **Mechanism: could not determine.** Inferred, not verified: GBIF may skip the GADM lookup when
  the uncertainty circle is large. Nothing read here documents that, and about 6,900 untagged
  records have uncertainty under 20 km or none, which that guess does not explain.
- Across all countries, 315,648 of 14,548,380 base-filter records (2.2%) have no GADM tag.

### 4.2 The excluded sample the dispatch asked for

"Records the country-borders filter excludes that `country` includes": the 61,508 untagged plus the
149 tagged elsewhere. Samples of both are in `null_gadm_box_sample.json` (20 untagged, in the boxes),
`mismatch_samples.json` (20 tagged elsewhere, 10 more untagged outside the newest reprocessing) and
`excluded_sample.json`. Why, grouped: **no GADM tag (inland, mostly obscured)**; **obscured point
across the Mexican border**; **impossible coordinates**. None is offshore in the samples read.

### 4.3 The stop

**The tag leaves out 29,904 records inside the T1 boxes** (PNW 9,211, East 20,693). The dispatch's
stop applies: "Stop if the tag leaves out records inside either T1 box". Most of those would later
be dropped by the obscured step, which is in both step lists (D65), but 1,664 (PNW) and 1,514 (East)
have uncertainty under 20 km or none, and the acceptance check against 0005709 would show a hole
for every one of them that 0005709 holds.

## 5. Size and disk

- Estimate, scaling 0005714 (2,549,508 records, 1,475,785,280 bytes zipped, `docs/pulls/gbif-fungi-north-america-2015-2025.doi.json`)
  by record count:
  - GADM tag only (2,432,070): about **1.41 GB** zipped, **6.71 GB** if fully extracted (0005714's
    members total 7,034,889,303 bytes by `unzip -l`, observed; occurrence.txt alone about 3.40 GB).
  - Country field, or GADM with the untagged added back (about 2,493,600): about **1.44 GB** zipped,
    **6.88 GB** extracted.
- **Free disk: 1,858,334,720 bytes (1.86 GB, 98% used)** on `/` (`df -B1 ~`, observed). `/tmp` is a
  3 GB tmpfs and is not a home for it.
- The zip alone would fit with about 0.4 GB to spare; extraction would not. The code here reads
  the zip in place without extracting, so extraction may not be needed (inferred from the three zip
  readers above; the unified pipeline's runner for this download is not written yet). **Stop, as the
  planner instructed:** what gets deleted is the owner's call, and I have not freed or moved anything.

## 6. The acceptance check's input

- **Original**, `~/Zynergy/forager-forecast-t1-calendar-smoke-test/data/t1/downloads/0005709-260916113435855.zip`:
  163,662,303 bytes, sha256 `6468a43137d4f1da0379d0e6e5574d0cc5d3ab8e72d2ae50b140cac464a41683`, mtime
  2026-09-18 21:11 PDT (observed). Matches `docs/pulls/t1-fungi-two-boxes-2015-2025.doi.json`.
- **The planner's copy**, `~/Zynergy/forecast-data/gbif/0005709-260916113435855.zip` (copied on the
  owner's "Yes, copy them to one data folder", per the planner): same sha256 (observed). The folder's
  `SHA256SUMS` lists that hash and 0005714's `d0e8e7cd…caaf`, which matches its DOI record. The
  acceptance check will read from this path. Neither zip was moved, copied or written by me. The DOI
  records' `local_copy` fields are not edited; a note will be appended if one is needed.

## 7. Longitude ±180 (review finding 8)

- **No record reaches ±180 under either filter.** GADM-tagged US and Canada records at
  |longitude| ≥ 179.9: **0**. East of 0° with the tag: **3**, all at 51.63 N 178.66 E, GADM
  "Aleutians West" (`edges.json`). With the `country` field: 8 east of 0°, 20 at |longitude| ≥ 170.
- So `cell_for`'s two ids for one meridian (`cells.py:68-96`) are not exercised by this data. The
  three Aleutian records get eastern-hemisphere cell ids, far in id space from their neighbours across
  180°; that matters only to something that treats cell ids as adjacent, which nothing here does yet
  (inferred).

## 8. The count region

`records/counts.py:3`, `:44` and `:63` call the region outside the boxes "rest of North America",
and `scripts/t2_render_tables.py:17,21` and `tests/test_records_counts.py:45-48,83-85` use the name
(read). Proposal: rename it **`outside_t1_boxes`** (constant `OUTSIDE_T1_BOXES`), with the docstring
saying the region is the rest of whatever area the download covers. That is true over 0005714 (the
continent) and over D26's download (US and Canada) alike, where "rest of US and Canada" would be
false over 0005714. Filed T2 tables keep their old label. Implementer's naming call under START_HERE
"Who decides what"; not done yet, pending the stops.

## 9. Stops

1. **The country-borders tag leaves out 29,904 T1-box records** (section 4.3). D71 rules the GADM
   tag; moving off it changes the owner's ruling, so it goes to the owner. Options, as I see them:
   - **A. Tag, or `country` where the tag is missing:** `GADM_LEVEL_0_GID in (USA, CAN)` or
     (`GADM_LEVEL_0_GID` is null and `COUNTRY in (US, CA)`). About 2,493,578 records. Keeps the
     tag's ruling where GBIF has a tag; loses no box record that `country` holds. Both pieces were
     accepted by the predicate search; the `or`/`isNull` form is not verified on the download
     endpoint.
   - **B. `country` field only:** 2,493,712. Simplest. Loses 2 box records (both Mushroom Observer
     with wrong country), takes in the 149 tagged elsewhere (16 of 20 sampled are obscured points in
     Mexico). `country` is GBIF's interpreted field, not purely coordinate-derived.
   - **C. Tag only, as ruled:** 2,432,070. Loses 29,904 box records, about 3,178 of them below
     20 km uncertainty. The acceptance check then explains each missing key as "no GADM tag".
   - **D. The owner's other earlier option, a simple outline then trimming.** Not measured.
2. **Disk** (section 5): about 1.41 to 1.44 GB zipped against 1.86 GB free; extraction (about 6.7
   to 6.9 GB) does not fit. The planner's instruction is to report this as a stop and free nothing.

No other stop: `origin/main` has not moved; the tag is available as a predicate key (section 3); no
second download is needed.

## 10. Not verified

- The predicate on GBIF's download endpoint (needs a real request, which waits for the go).
- Why GBIF has no GADM tag on 61,508 US and Canada records; whether a later reprocessing fills it.
- `GADM_GID` counts against `GADM_LEVEL_0_GID`.
- Whether any of 0005709's keys is among the untagged records (needs the new download, or a key-by-key
  query not run here). The box counts above are of today's index, not of 0005709.

# T2 completion report: record audit, verify-first answered, pipeline prepared, pull blocked

**Date:** 2026-09-18
**Type:** completion report for docs/dispatch/2026-09-18-t2-record-audit.md.
**Base:** main f96d557, on branch t2-record-audit. Code commit 4e247d5; this report is the next
commit; the index row, session log row and TASKS.md cell follow in one more.
**Supersedes:** none.

Every claim below names a file and line, a commit, a URL opened on 2026-09-18, or a command whose
output is quoted, or is marked inferred. Read, observed and inferred are kept apart.

---

## The short version

**No count table and no real 200-record sample were produced.** Both need the GBIF download the
dispatch relies on, and a download request needs a GBIF.org username and password
(https://techdocs.gbif.org/en/data-use/api-downloads, "It is necessary to register as a user on
GBIF.org to create a download request, and to authenticate using the username (not the email) and
password"). This machine has none: `env | grep -i gbif` is empty, `~/.netrc` does not exist, and
the launching session's unauthenticated POST to the request endpoint returned 403. SPEC.md,
Constraints, allows bulk pulls only through GBIF downloads, so the search API was not used as a
substitute. Everything that could be built without the data was built against synthetic fixtures
and is tested in CI: the exact download request, the four-step filter pipeline with every step
counted, the count table, and the seeded sampler with its CSV. The task is blocked on one owner
item, credentials, and the report says exactly what is read and what is submitted once they exist.

Two verify-first findings change the dispatch's picture, and both are for the owner:

1. **GBIF cannot supply the 200-record sample at all.** The iNaturalist dataset on GBIF is
   research grade only. Its own metadata says the archive holds observations that "Achieved one
   of following iNaturalist quality grades: Research" (https://api.gbif.org/v1/dataset/50c9509d-22c7-4a22-a47d-8c48425ef4a7,
   description field), and iNaturalist's help page says "Research-grade observations with CC0,
   CC BY, or CC-BY NC licenses" are exported
   (https://help.inaturalist.org/en/support/solutions/articles/151000170346). The dispatch's
   sample is of records that are "not research grade", so it can only come from iNaturalist. GBIF
   also carries no identification count and no agreement count: `identifiedBy` is one name on
   every one of 899 sampled records that had it, and there is no identification extension in the
   archive (verbatim record 5006980885 has one extension, Multimedia). The smallest iNaturalist
   pull that carries agreement is one search query of 17,165 observations, stated under "Owner
   items" as a proposal; it was not run.
2. **User-obscured coordinates are visible on GBIF, but through `informationWithheld` and a raised
   `coordinateUncertaintyInMeters`, not through `dataGeneralizations`.** 177 of a 900-record spot
   sample carried the text "Coordinate uncertainty increased to NNNNNm at the request of the
   observer" with uncertainties of 26.5 to 28.9 km; `dataGeneralizations` was empty on all 900.
   The R6 uncertainty filter alone would catch them; the pipeline names them first anyway, so the
   count table shows how many there are. SIMPLE_CSV downloads do not carry `informationWithheld`
   (column list at https://techdocs.gbif.org/en/data-use/download-formats), so the request asks
   for DWCA.

Neither target group and none of the named contaminants is obscured at taxon level by iNaturalist
(verify-first item 2, below).

## Verify first, as answered

### 1. How GBIF exposes identification agreement and user-obscured coordinates

**What the dataset is.** GBIF dataset 50c9509d-22c7-4a22-a47d-8c48425ef4a7, "iNaturalist
Research-grade Observations", DOI 10.15468/ab3s5x, licence CC BY-NC 4.0, 166,947,411 occurrences
on 2026-09-18 (search API, limit=0), published 2026-09-07 and modified 2026-09-10 (dataset API,
fields `doi`, `license`, `pubDate`, `modified`). Read from the API because https://www.gbif.org
returns 403 to a non-browser client (observed, curl and WebFetch). Its description states three
inclusion rules: a licence of CC0, CC BY or CC BY-NC; "Achieved one of following iNaturalist
quality grades: Research"; created on or before the export date. iNaturalist's own page agrees and
adds that the export is weekly (URL above, opened; quoted: "iNaturalist generates data for GBIF
once a week, and they attempt to ingest it once a week").

**Identification agreement: not carried.** Observed on the interpreted and verbatim records
(`https://api.gbif.org/v1/occurrence/5006980885` and `/verbatim`, and the five records of
`spot_search.json` under data/t2, gitignored):

- `identifiedBy` holds one name (the last identifier, inferred from `dateIdentified` matching the
  observation's most recent identification; not confirmed against iNaturalist).
- `identificationID` holds one iNaturalist identification id.
- `identifiedByID` holds an ORCID when that one identifier has one (record 5006816912).
- `identificationRemarks` holds that identifier's free text when present (record 5006702681).
- There is no count of identifications, no count of agreements, no community taxon, and no
  quality grade field (every record is research grade by construction). The only extension in
  the archive is `http://rs.gbif.org/terms/1.0/Multimedia` (verbatim response, `extensions`).
- In the 900-record sample, `identifiedBy` never contained a separator (`|` or `;`): 0 of 899.

What research grade means on iNaturalist, from
https://help.inaturalist.org/en/support/solutions/articles/151000169936 (opened, quoted): an
observation is research grade when "the community agrees on species-level ID or lower, i.e. when
more than 2/3 of identifiers agree on a taxon at species-level", or when "the community agrees on
an ID between family and species and votes that the community taxon is as good as it can be";
"Observations can be Research Grade at genus or any other level below family if the community
agrees on an ID at that level and votes that the observation does not need more IDs". So a
research-grade record on GBIF implies at least two identifications with more than two-thirds
agreement, but the number is not in the record. In the spot sample 896 of 900 records were at
species rank and 4 at genus rank; the 4 are the voted-as-good-as-it-gets case.

**User-obscured coordinates: carried, in two fields.** Observed on record 5006980885
(iNaturalist observation 257648390, Washington, Cantharellus formosus):

```
coordinateUncertaintyInMeters = 26775
informationWithheld = Coordinate uncertainty increased to 26775m at the request of the observer
dataGeneralizations = (absent)
decimalLatitude = 47.8184800926, decimalLongitude = -122.2805825552
```

Against the mechanics iNaturalist documents
(https://help.inaturalist.org/support/solutions/articles/151000169938, opened, quoted): "The
public positional accuracy is increased to the diagonal of a 0.2 x 0.2 degree cell (~500km2 at
the equator or about the same size as the Isle of Man). Latitude and longitude are replaced with a
random point within this cell." The diagonal of a 0.2 x 0.2 degree cell at latitude 47.818 is
26,787 m (computed: hypot(0.2 x 111,195, 0.2 x 111,195 x cos(lat))); the record says 26,775 m, a
ratio of 0.9995. Inferred from that one record: GBIF receives the public (randomised) point and
the public positional accuracy, and iNaturalist writes the reason into `informationWithheld`.
The 900-record tally (three pages of 300 at offsets 0, 5,000 and 10,000 of the Cantharellus,
North America, 2015 to 2025, hasCoordinate query; data/t2/spot_sample_900.json, gitignored):

```
('open', 'nodg', 'unc missing') 114
('open', 'nodg', 'unc<=250')    483
('open', 'nodg', 'unc>250')     126
('withheld', 'nodg', 'unc>250') 177
withheld records: uncertainty values [(26839.0, 17), (26550.0, 17), (28329.0, 9), ...]
distinct withheld texts: Counter({None: 723, 'Coordinate uncertainty increased': 177})
```

So: every withheld record had uncertainty above 250 m, no record had `dataGeneralizations`, and
126 open records also exceeded 250 m (GPS accuracy as the observer's device reported it, inferred).
`informationWithheld` is not a facetable field on the search API (a `facet=informationWithheld`
request returned the count and no facet), which is why the share was read from a sample rather
than a count. The Darwin Core definitions, from https://dwc.tdwg.org/list/ (opened):
`informationWithheld` "Information withheld that may increase the sensitivity of the data";
`dataGeneralizations` "Actions taken to make the shared data less specific or 'less raw'";
`coordinateUncertaintyInMeters` "The uncertainty radius around the coordinates in meters".

**Which download format carries it.** From https://techdocs.gbif.org/en/data-use/download-formats
(opened): the SIMPLE_CSV column list has `coordinateUncertaintyInMeters` and `identifiedBy` but
not `informationWithheld` or `dataGeneralizations`; the DWCA format's occurrence.txt and
verbatim.txt carry all four. The prepared request therefore asks for DWCA
(src/forager_forecast/records/gbif_download.py:64-70).

**Orientation counts from the search API, not the count table.** These are limit=0 counts,
allowed as spot checks, and are not the dispatch's table: that table is computed from the
download after each filter. Cantharellus (GBIF backbone genus key 9623860), iNaturalist dataset,
North America, 2015 to 2025, hasCoordinate, HumanObservation: 16,231. Laetiporus (2542160):
37,857. By uncertainty band for Cantharellus: 0 to 250 m 7,913; 251 to 1,000 m 1,054; 1,001 to
10,000 m 1,430; 10,001 to 100,000 m 3,246; above 100,000 m 55; the remaining 2,533 have no
uncertainty (inferred by subtraction from 16,231). The whole shared pull, kingdom Fungi,
HumanObservation, North America, 2015 to 2025, hasCoordinate, across all datasets: 2,549,508, of
which iNaturalist 2,221,740, Mushroom Observer (d714382d-5890-4234-ae81-696eeb53658a, CC BY-NC)
164,890, and "Fungi of parks, forests and reserves of New Jersey (2007-2019)"
(fca5e616-990e-4d62-adc3-3122ed64b8e8, CC BY) 156,744. The pull is not iNaturalist alone; the
filter reads Darwin Core fields, so the other publishers pass through the same steps, and the
count table will show them if they matter.

**If GBIF does not carry it: the smallest iNaturalist pull.** The record set the dispatch names
does not exist on GBIF. On iNaturalist it is one search:
`/v1/observations?taxon_id=47348&place_id=97394&lrank=genus&hrank=genus&quality_grade=needs_id&identifications=most_agree&verifiable=true&d1=2015-01-01&d2=2025-12-31`,
which counted 17,165 on 2026-09-18 (`total_results`, per_page=0; 18,714 without the date range).
Each result already lists every identification with `current`, `taxon` and `user`, so no
per-record call is needed (observed on observations 1175887, 1446122 and 1537515, which the
query returned first by id: each shows two to five current identifications at Cantharellus by
distinct users and quality grade needs_id). At 200 per page and one request a second that is 86
requests, about two minutes. A second, smaller call fetches the state or province name for the
distinct admin-level-10 place ids in the drawn 200. This is a proposal (Owner items), not an
action; it is expressed in code as `population_query()`
(src/forager_forecast/records/sampler.py:45-63) so that the proposal and the test agree.

### 2. Whether iNaturalist obscures any target taxon automatically

**No, for all nine taxa checked.** From `/v1/taxa?q=<name>` on 2026-09-18 (data/t2/inat_taxa.json,
gitignored), the exact-name hit for each carries `conservation_status: None` and
`conservation_statuses: None`, and no key containing "geopriv" or "threat":

| Taxon | iNaturalist id | rank | observations |
|---|---|---|---|
| Cantharellus | 47348 | genus | 134,410 |
| Laetiporus | 48431 | genus | 154,646 |
| Hygrophoropsis aurantiaca (false chanterelle) | 63538 | species | 24,205 |
| Hygrophoropsis | 63543 | genus | 28,250 |
| Omphalotus (jack-o'-lantern) | 64014 | genus | 63,598 |
| Omphalotus illudens | 126831 | species | 25,060 |
| Omphalotus olearius | 64021 | species | 3,167 |
| Omphalotus olivascens | 67752 | species | 15,657 |
| Craterellus | 48611 | genus | 43,541 |

And from the observations endpoint, North America (place 97394), verifiable:

```
Cantharellus: verifiable NA=104689, taxon_geoprivacy=obscured 0, user geoprivacy=obscured 12193, private 0
Laetiporus: verifiable NA=101866, taxon_geoprivacy=obscured 0, user geoprivacy=obscured 7547, private 0
Hygrophoropsis aurantiaca: verifiable NA=13359, taxon_geoprivacy=obscured 0, user geoprivacy=obscured 687, private 0
Omphalotus: verifiable NA=46951, taxon_geoprivacy=obscured 0, user geoprivacy=obscured 2294, private 0
```

The `taxon_geoprivacy=obscured` zeros are the direct answer. The `private 0` figures are not
evidence of anything: a private observation has no public place, so a place-filtered query
cannot see it (inferred from the mechanics; not tested). Source for the mechanism, opened and
quoted: "Taxa on iNaturalist can have multiple conservation statuses ... If the threats include
pressures that are increased from location disclosure, the conservation status may include a
geoprivacy setting of 'obscured' or in rare cases 'private'. This will automatically apply this
geoprivacy setting to all observations of that taxon globally or in the place specified by the
conservation status" (https://help.inaturalist.org/support/solutions/articles/151000169938). A
status can be place-specific, so the taxa endpoint's global answer was cross-checked by the
observation counts above, which cover all of North America. The user-obscured shares are 11.6%
of verifiable Cantharellus and 7.4% of Laetiporus; EVIDENCE.md's 17.3% and 8.1% are shares of
research-grade records, a different denominator, and were not recomputed.

## What landed

| Commit | Change |
|---|---|
| 4e247d5 | `src/forager_forecast/records/` (five modules), `docs/pulls/gbif-fungi-north-america-2015-2025.json`, four test files with 65 tests |
| this commit | This report |
| next commit | Index row, session log row, T2 status cell |

What each module is, with the load-bearing lines:

- **gbif_download.py.** `predicate()` (:43-61) is the dispatch's five terms as six clauses
  (YEAR is two comparisons), `request_template()` (:64-70) adds format DWCA and the GBIF Backbone
  checklist key, `credentials_from_env()` (:93-97) reads `GBIF_USER`, `GBIF_PWD`, `GBIF_EMAIL`
  (:38-40, the rgbif and pygbif names) and raises `MissingCredentials` naming every unset one
  (:85-90); `curl_argv()` (:108-125) is the submission as GBIF documents it. No function opens a
  connection.
- **filters.py.** The four steps in the dispatch's order, `default_steps()` (:150-158):
  `is_user_obscured` (:42-55, any non-empty `informationWithheld` or `dataGeneralizations`),
  `exceeds_r6_uncertainty` (:72-75, above 250 or missing; the constant at :35 is not a parameter),
  `is_default_first_of_month_date` (:78-97, day 1 with no time or 00:00:00), and
  `DuplicateObserverCellDay` (:125-142, first record per observer, 0.1 degree cell and day flows
  on; a 16-byte digest per key). `Pipeline.run()` (:172-205) is a generator over a stream,
  counting `before` and `dropped` per step and calling `on_pass` for the count table.
  `read_occurrence_table()` (:208-219) streams a DWCA table read-only with QUOTE_NONE.
- **counts.py.** The T1 boxes (:40-43), `region_of()` (:58-67, inclusive limits, else
  "rest_of_north_america"), `group_of()` by GBIF genusKey (:50-53, :70-72), `CountTable`
  (:87-113) keyed by stage, group, region, year, with every record also under "all_fungi".
- **sampler.py.** `is_eligible()` (:80-90: not research grade, taxon 47348 at genus rank, a
  photo, two or more distinct users with a current identification at 47348), `sample()`
  (:134-140: sort by id, `random.Random(seed).sample`, fewer than 200 raises), and
  `write_hand_check_csv()` (:143-159) with the columns record_link, photo_link, date,
  state_or_province, verdict, notes (:33-40).

## Evidence

### Lint and tests

```
$ uv run ruff check .            -> All checks passed!
$ uv run ruff format --check .   -> 34 files already formatted
$ uv run pytest -q               -> 71 passed in 0.69s
```

6 tests existed before; 65 are new. The dispatch's named test is
tests/test_records_sampler.py:134 `test_same_seed_gives_the_same_200_records`, with
`test_input_order_does_not_change_the_draw` (:141) and `test_a_different_seed_gives_a_different_draw`
(:147) beside it. One test per filter step: tests/test_records_filters.py:38-46 (obscured),
:68 (uncertainty, nine parametrised values including 250 kept and 250.5 dropped), :94 (default
date, ten values), :109-131 (duplicates). Pipeline counting and source integrity: :161, :188,
:199, :209.

### Revert checks

Ten, each done the same way: the module file was copied to /tmp first, one line changed with
sed, the affected test file run, the copy restored (never `git checkout`), and afterwards all five
module files hashed against the pre-edit hashes (`sha256sum -c`: five OK) and the suite re-run
(71 passed). The runner refused to cite a result if the reverted build failed to import; none
did. Each failure names the reverted behaviour:

| Reverted line | Failures | Message that ties it to the edit |
|---|---|---|
| `>` to `>=` on the R6 threshold | 2 | `exceeds_r6_uncertainty(... row(coordinateUncertaintyInMeters='250'))` returned True |
| `or` to `and` in `is_user_obscured` | 4 | `is_user_obscured(... informationWithheld='Coordinate uncertainty increased ...')` returned False |
| date-only first of month passes | 3 | `row(eventDate='2024-09-01')` not dropped; kept ids `['1', '5', '7'] == ['1', '7']` |
| duplicates never remembered | 3 | second record `gbifID '2'` not dropped; kept `['1', '6', '7']` |
| step `before` never incremented | 1 | `(0, 1) == (7, 1)` |
| sampler skips the sort | 1 | `test_input_order_does_not_change_the_draw`, first record 1002 vs 1000 |
| sampler ignores the seed | 1 | `test_a_different_seed_gives_a_different_draw`, two draws equal |
| sampler pads a short pool | 1 | `DID NOT RAISE TooFewCandidates` |
| `LAST_YEAR = 2024` | 2 | committed file differs at `"value": "2024"` |
| format `SIMPLE_CSV` | 2 | committed file differs at `"format": "DWCA"` |

### Spot-check records, with GBIF keys

| GBIF key | iNaturalist observation | What it showed |
|---|---|---|
| 5006980885 | 257648390 | obscured: `informationWithheld` text, uncertainty 26,775 m, verbatim has no identification extension |
| 5006816912 | 257503074 | open: uncertainty 8 m, `identifiedByID` an ORCID, `identifiedBy` one name |
| 5006702681 | 257482626 | `identificationRemarks` carries one identifier's text; uncertainty 1,759 m |
| 5006830067 | 257421856 | uncertainty absent |
| 5007026983 | 257295378 | no media |

iNaturalist observations read for the sampler's shape: 1175887, 1446122, 1537515 (needs_id, genus
Cantharellus, two to five current agreeing identifications, `positional_accuracy` 5, 162, 5 m).

### GBIF taxon keys

`/v1/species/match?name=Cantharellus&rank=GENUS&kingdom=Fungi&verbose=true`: 9623860,
"Cantharellus Adans. ex Fr., 1821", EXACT, ACCEPTED; the alternatives are synonyms, a doubtful
name, a coral genus (2260638, Hoeksema & Best, 1984) and fuzzy matches. Laetiporus: 2542160,
EXACT, ACCEPTED. Contaminants, for the record: Hygrophoropsis aurantiaca 2525710, Omphalotus
2525554. The GBIF Backbone checklist key d7dddbf4-2cf0-4f39-9b2a-bb099caae36c resolves to "GBIF
Backbone Taxonomy" and key 5 in it to "Fungi", KINGDOM; the download documentation's example
checklist key 7ddf754f-d193-4cc9-b351-99906754a03b resolves to "Catalogue of Life", which is why
the backbone key is written into the request rather than copied from the example.

### The first-of-month step on this data

In the 900-record sample, 32 records fell on day 1 of a month (3.6%, against 1 in 30.4 expected
if dates were uniform), 0 had an eventDate ending in T00:00:00 and 7 were date-only. Inferred:
iNaturalist records will lose few or no records to this step, since observers record a time and
iNaturalist fills a real date; the step exists because the dispatch names it and because the
other two publishers in the pull may not behave the same way. The count table will say.

## Deviations from the dispatch

- **The count tables and the CSV were not produced.** The dispatch's "Then build" section
  assumes the GBIF pull. Without credentials the pull cannot be requested, and the search API is
  not permitted as a substitute (SPEC.md, Constraints). The pipeline, the table and the sampler
  are built and tested on synthetic fixtures instead, so that once the download lands the
  remaining work is running them and reading the output.
- **The 200-record sample cannot come from the GBIF pull**, which the dispatch implies by placing
  it under the same "Then build" heading. It needs the iNaturalist pull proposed above. The
  dispatch itself anticipated this in verify-first item 1 ("If GBIF does not carry what is
  needed, say so and propose the smallest iNaturalist pull that does").
- **The launching message and the dispatch agree** on everything checked. The launching message
  added the predicate's exact five terms and the DWCA-vs-CSV question; the dispatch says "Can
  share the GBIF pull with T1" without listing terms, and T1's dispatch lists the same five.

## Decisions taken here, and what was rejected

- **DWCA, not SIMPLE_CSV.** SIMPLE_CSV lacks `informationWithheld` (download-formats page), and
  that is the field that names an obscured record. Rejected: SIMPLE_CSV with the R6 uncertainty
  filter alone, which would catch the same records but could not count "user-obscured" as its own
  step, which the dispatch asks for.
- **Any non-empty `informationWithheld` or `dataGeneralizations` counts as obscured**
  (filters.py:42-55). Rejected: matching iNaturalist's exact wording, which would pass a
  taxon-geoprivacy obscuring or another publisher's wording as open. The cost is that a
  non-coordinate withholding, if one exists in the pull, is dropped at this step too; the table
  will show the step's count and the report after the run can say what the texts were.
- **The duplicate step's cell is the 0.1 degree weather cell** (filters.py:39, D19 and D21).
  Rejected: the 250 m habitat cell, which is not defined until T4, and any rounding other than
  floor.
- **Missing coordinates and unparseable dates are not filter steps.** The predicate requires
  coordinates, and the dispatch names no date-shape step beyond the first-of-month default. Ranges
  and month-only dates pass the date step and are dedup-keyed on their raw text
  (filters.py:78-97, :108-111). Proposed for the owner if the count table shows them in numbers
  that matter; not added now.
- **The sampler sorts by id before drawing** (sampler.py:134-140), so the draw depends on the
  seed and the candidate set, not on the order the API returned them in. Rejected: iNaturalist's
  own `order_by=random`, which takes no seed.
- **Eligibility counts distinct users with a current identification at the genus itself**
  (sampler.py:65-90). Rejected: iNaturalist's `num_identification_agreements`, whose reference
  taxon is the observation's, so a species-level maverick could inflate it; and counting
  identifications rather than identifiers, which a user who re-identifies twice would inflate.
- **A photo is required for eligibility** (sampler.py:87-88). The dispatch does not say so, but a
  photo hand check of a record without a photo cannot be done, and every candidate is verifiable
  (the population query) so almost all have one; the count of those without will be reported when
  the pull runs.
- **State or province comes from `place_ids` at admin level 10, or is left empty**
  (sampler.py:101-112). Rejected: parsing `place_guess`, which is observer free text.
- **Credentials from three environment variables and nothing else** (gbif_download.py:38-40).
  Rejected: ~/.netrc (would work with `curl --netrc`, and is mentioned in the docstring as the
  owner's option), a config file (one more secret-bearing file to keep out of git).
- **Predicate as code and as a committed JSON file, held equal by a test**
  (tests/test_records_gbif_download.py:19). The file is what the owner submits; the test is what
  stops it drifting from the constants.
- **Standard library only.** No dependency was added, so nothing to pin and nothing to check for
  a 3.14 wheel (D20). csv streaming keeps memory flat on a machine that had about 1 GB free.

## Owner items

1. **GBIF credentials.** A GBIF.org account is needed; registration is at https://www.gbif.org
   and is free. Once it exists, set `GBIF_USER` (the username, not the email), `GBIF_PWD` and
   `GBIF_EMAIL` in the environment of the session that submits. Nothing else is read. The body to
   submit is `docs/pulls/gbif-fungi-north-america-2015-2025.json` with two fields added,
   `"notificationAddresses": ["<GBIF_EMAIL>"]` and `"sendNotification": true`
   (`request_body()`, gbif_download.py:100-105), POSTed to
   `https://api.gbif.org/v1/occurrence/download/request` with HTTP basic auth
   (`curl_argv()`, :108-125, matches GBIF's documented command). The predicate is: TAXON_KEY 5
   (Fungi), BASIS_OF_RECORD HUMAN_OBSERVATION, YEAR 2015 to 2025 inclusive, HAS_COORDINATE true,
   CONTINENT NORTH_AMERICA; format DWCA; checklistKey the GBIF Backbone. Expected size: about
   2.55 million records, three publishers above 100,000. The download key becomes a DOI, which is
   the citation T2 and T1 both record. Two names that the predicate uses, `checklistKey` in the
   body and `CONTINENT` as a key, are from the documentation page and could not be validated
   without submitting (no predicate-validation endpoint: 404, observed); if the API rejects
   either, the error is the next fact.
2. **The iNaturalist pull for the sample, as a proposed DECISIONS.md row.** "T2 may pull, once,
   the iNaturalist search `population_query()` (sampler.py:45-63): about 17,165 observations, 86
   requests at one per second, plus one places lookup for the drawn 200; the result is kept under
   data/ and never committed; the 200-record CSV, the seed and the query are the record. Reason:
   the dispatch's sample is of not-research-grade records, which GBIF does not carry, and this
   query is the smallest pull that carries identification agreement." Alternative considered: no
   sample, and training on research grade only without the check, which the dispatch's "Already
   considered and rejected" rules out.
3. **The person-only photo hand check** waits on that CSV. Verdicts: chanterelle, not a
   chanterelle, cannot tell. Above 5% error keeps training on research grade only (dispatch,
   IDEAS.md I2).
4. **Two publishers other than iNaturalist are in the shared pull** (Mushroom Observer, CC BY-NC;
   the New Jersey fungi dataset, CC BY). DATA_REGISTER.md should carry them before their records
   are used; that is a T3-shaped item and is reported, not done.

## Not checked

- Whether the download API accepts the request as written. No submission was possible.
- Whether the DWCA occurrence.txt column names match the API field names used in filters.py
  (`informationWithheld`, `dataGeneralizations`, `coordinateUncertaintyInMeters`, `recordedBy`,
  `decimalLatitude`, `decimalLongitude`, `eventDate`, `genusKey`, `year`). The download-formats
  page says the interpreted table carries the Darwin Core terms and the API returns them under
  the same names; read_occurrence_table() will show any mismatch as a KeyError on the first row,
  not as a silent empty count, because the tally reads `record["decimalLatitude"]` directly.
- The interpreted `eventDate` shape in the DWCA file against the API's (observed: the API returns
  "2025-01-06T13:24:27" with no offset; the verbatim keeps the offset).
- Whether `identifiedBy` on GBIF is the last identifier or the first. Inferred from
  `dateIdentified` on one record.
- Whether Mushroom Observer or the New Jersey dataset use `dataGeneralizations` or their own
  `informationWithheld` wording. The pipeline treats any text as obscured, so the count table will
  show it either way.
- Any research-grade record's photo, and the misidentification rate. Person-only, and waiting
  on the sample.
- The 900-record sample is a sample: three pages at fixed offsets, not random. It was used for
  the shape of fields, not for a rate that gets carried anywhere.
- The private-geoprivacy count. The zero is explained above as a property of the query.

## Conventions

Checked: docs/audits/README.md for the index form and the append-only rule; the T0b report for
the header fields and section order, followed here; pyproject.toml for ruff's rule set and line
length, both satisfied; tests/test_large_file_guard.py for the test style (real entry points,
assertions on output); .gitignore for data/ (used for every fetched file); the Forager CLAUDE.md
rules on revert checks (copies, not git; build must import before a failure is cited) and on
citing a figure with its scope. No em dashes. Not followed: nothing knowingly.

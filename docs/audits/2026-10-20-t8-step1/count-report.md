# T8's count: Ash Transect's report, as received

Filed by the forecast planner (Alder Bearing), 2026-10-20. The run used t8-build at 0cb9566, under D134 and
D135 (forecast RECORD 2026-09-28-2033). The planner checked the four output files' sha256 values and the
summary's identity flags and labels against the report, and they match.

The outputs are in `~/Zynergy/forecast-data/t8/count/`. They are read-only, with SHA256SUMS. They are not
committed: the summary holds per-cell chanterelle rises at 0.1°, and the repository is public.

| File | sha256 |
|---|---|
| count_summary.json | 0773c0cffa3e41b14852c3ae1b6624e22d89db41d08434209f062a708dd43b9b |
| lichen_t1_1000m.npz | fbcf00ae595126daf80cfd5ca76e4609831d00c27eac2e92ca8ffdd5c57431bf |
| lichen_t1_5000m.npz | 05d948aeed08cd2d10d675934e9a9785407188bcf23da70c82d243a62e4cb7e5 |
| lichen_t1_1000m_cc.npz | fa1355756871be7e5c46197bc22dd9d096558b3a91d55cf2fa3fca708ef82da5 |

## The run (read: journal and summary)

- One run, 04:04:18Z to 04:08:09Z: exit 0, 230.7 s, peak 325.8 MB under a 3 GB cap.
- MemAvailable was 6,681,364 kB before the run.
- No network call, no fit and no weather read. t6b-night was left alone.
- The zip's sha256 matched its pull record. 2,493,578 rows were read, of which 252,818 fall in the PNW
  box. 9,627 were unloadable: 9,604 have no calendar day, and 23 span more than one day.

## T1 identity: all three lists identical to T1

| List | Units | Allowed extras (T1's sea drops) | Survivors |
|---|---|---|---|
| t1_1000m | 52,718 | 468 | 144,145 |
| t1_5000m | 56,927 | 491 | 157,232 |
| t1_1000m_cc | 9,640 | 49 | 24,198 |

## Lichen attach

| List | Lichen-positive units | Share | Outings | Records in units | Records outside |
|---|---|---|---|---|---|
| t1_1000m | 13,142 of 52,718 | 24.9% | 16,038 | 23,036 | 373 |
| t1_5000m | 13,844 of 56,927 | 24.3% | 16,913 | 24,097 | 379 |
| t1_1000m_cc | 3,468 of 9,640 | 36.0% | 3,925 | 7,592 | 89 |

## The jump check, headline list

Cantharellus survivors in the box:

| | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Records | 3 | 8 | 12 | 29 | 81 | 111 | 122 | 98 | 99 | 346 | 326 |
| Distinct observers (J1) | 3 | 7 | 9 | 19 | 49 | 89 | 94 | 70 | 73 | 241 | 230 |

The rise is 247 records for 2023→2024 and 227 for 2023→2025.

| | 2023→2024 | 2023→2025 |
|---|---|---|
| J1: observers, from 73 | 241 (doubled) | 230 (doubled) |
| J2: share of the rise from new heavy observers | 0.04 (10 records, 1 observer) | 0.15 (33 records, 3 observers) |
| J3: rise carried by the main dataset | 247 of 247 | 226 of 227 |
| J3: largest rise from any other dataset | 0 | 1 |
| J4: top 3 weeks' share of the rise | 0.31 | 0.27 |
| J4: top 5 cells' share of the rise | 0.18 | 0.16 |
| J5: genera rising 1.5x or more | 1 of 6 (Hydnum) | 1 of 6 (Hydnum) |
| J6: share named to species | 1.0 | 1.0 |

- **The main dataset:** 50c9509d-22c7-4a22-a47d-8c48425ef4a7, with 99, 346 and 325 records. No other
  dataset reaches 20 records in any of those years.
- **J5 rate ratios against 2023:**

  | Genus | 2023→2024 | 2023→2025 |
  |---|---|---|
  | Boletus | 1.283 | 1.464 |
  | Hydnum | 2.146 | 2.106 |
  | Russula | 0.935 | 0.850 |
  | Lactarius | 1.047 | 1.066 |
  | Suillus | 0.936 | 1.335 |
  | Amanita | 1.141 | 1.207 |

**Label: undetermined**, overall and for each comparison alone. No reporting-led condition holds, and the
surge reading fails on the genera, 1 of 6 against the 4 it needs.

## Notes

- **The plan's §2 figures:** 321, 941 and 783 were raw records from the superseded T1 download, counted
  before T1's steps. These are survivors after the steps. The two have not been reconciled.
- **Planner's observation, no verdict:** almost all the rise came through one dataset, so J3's
  "another dataset" condition could not separate the readings here. The rise came from many new light
  reporters, not a few heavy ones: observers went from 73 to 241, while J2 stays at 0.04 to 0.15.

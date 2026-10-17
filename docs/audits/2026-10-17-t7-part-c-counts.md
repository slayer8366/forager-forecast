# T7 part C: the saprotroph comparison group counted (and P10b condition 2 by block)

Hazel Cairnwright (coder), 2026-10-17. Dispatch: `docs/dispatch/2026-10-17-t7-part-c.md` (branch `t7-strengthen-plan`, 2baa537). Forager RECORD: intent -1165; the owner's rulings -1164 and -1167. Decision rows: D145 amended (step 1), D155 (step 2). Nothing was fitted. Nothing is published.

## Mechanism prediction (written before building, in the first report)

- **Step 1.** A new function sits beside `within_cluster_auc_difference`. It keeps the within-weather-cell pair statistic, so the point stays +0.0540, and resamples level III blocks instead of weather cells. Only 22 blocks carry within-cell pairs, against 1,862 weather cells, so the interval was expected to widen. No call was made on whether it would stay above zero.
- **Step 2.** The adapter derives the group's genera from the committed export. The group joins by genus name through the same `Join` as Laetiporus (M4). The normalised list and its sha256 are unchanged, so the main group's inputs are untouched. The V9 counter gets a selector argument rather than a fork.
- **Outcome (planner).** The group is smaller than the mycorrhizal group's 23,069 thinned presences. **Read:** yes. The main run has 17,403 and the side run 24,272.

## Readings put to the owner before anything was computed or counted

The first report stopped on three open readings (RECORD -1167). Each was ruled before any figure or count was read:

1. **Condition 2's resampling.** 374 of the 1,862 weather cells holding pairs span more than one block, carrying 5.9% of the within-cell pair weight (`probe_straddle.py`, in the step 1 folder). The ruling was reading (a), condition 1's exact resampling. The owner: "Same method as the other test (Recommended)".
2. **The nine genera with "ectomycorrhizal" in their secondary lifestyle or lifestyle comment are out.** The owner: "Out (Recommended)".
3. **Genera with a secondary lifestyle go to a side run.** The owner: "Side run, like the main group (Recommended)".

**A slip of mine, disclosed.** My first report said "131 of the 669 genera, including those nine, have a secondary lifestyle". In fact only 6 of the nine have a secondary lifestyle; Ceratorhiza, Clavariadelphus and Sistotrema carry "ectomycorrhizal" in the comment only. So "the 131 less the nine" is 125 genera, not 122. The split applied is 535 main, 125 side-only and 9 out, which totals 669 (`counts.json`, `group_rule`).

## Step 1: P10b condition 2, clustered by level III block

- **Code.** `metrics.within_cluster_auc_difference_rows_resampled` draws blocks with replacement and multiplies each row's weight by its block's draw count, as `clustered_auc_difference` does for condition 1. It keeps every pair inside one weather cell, including pairs whose rows lie in two blocks. `scripts/t7_fit.py` reports it from both `fit` and `figures` as `within_weather_cell_block_clustered`, beside the weather-cell figure.
- **D145.** An amendment line is appended to the row; the original text is unedited (checked by stripping the insertion and comparing with HEAD's file).
- **Result on the existing 2026-10-17 cache.** The read-only `figures` command ran at 691d2ee: 776 s, peak 1,013 MB, under the memory cap (`docs/audits/2026-10-17-t7-part-a/condition2-by-block/`).

| figure | point | 95% interval | wholly above zero |
|---|---:|---|---|
| full minus A, within weather cell, weather-cell interval (part A) | +0.0540 | +0.0354 to +0.0705 | yes |
| **full minus A, within weather cell, block interval (condition 2 as amended)** | **+0.0540** | **+0.0160 to +0.0639** | **yes** |
| full minus B, within weather cell, block interval (not a P10b condition) | +0.0474 | −0.0043 to +0.0762 | no |

- **Consistency check.** Every other figure in the new JSON (within-cell AUCs, block-clustered pooled intervals, base minus B, pooled AUCs) is identical to part A's `figures_from_cache.json`.
- **P10b on the existing run.** Condition 1 fails, condition 2 passes, condition 3 has not been computed and condition 4 has no data. The verdict is "fail", on condition 1 as before.

## Step 2: the count

The count ran at c67b608 under the memory cap: 773 s, peak 1,834 MB. It streamed the D26 zip (sha256 c0d5f6a1…72b26c, equal to the pull record's) over the same box, the same effort frame and V9's code paths. Outputs:

- `2026-10-17-t7-part-c/counts.json` for the counts;
- `2026-10-17-t7-part-c/entering_by_block.json` for the presences that would enter a fit. It was read through `t7_fit.Data` on the fit's work dir; no model was trained.
- Presence tables are under `/mnt/work/Zynergy/forecast-data/t7/v9c/`.

**Check on the entering script.** It reproduces the mycorrhizal main group's fit figures exactly: 15,624 entering presences and 44 genera alone (D147).

**Overlap with the main group: none.** No genus in either saprotroph run is one the list classes ectomycorrhizal, and none is among V9's main-run genera (`group_rule.shared_with_*`, both empty). The count refuses to run otherwise.

### Table 1. Presences by side (thinned, in the box)

| run | before thinning | thinned | US | Canada | outside study area | genera |
|---|---:|---:|---:|---:|---:|---:|
| saprotroph main | 20,493 | 17,403 | 15,688 | 1,492 | 223 | 136 |
| saprotroph side | 29,194 | 24,272 | 21,795 | 2,137 | 340 | 184 |

### Table 2. Genera alone and pooled (D144 rule 4, 30 presences)

| run | population | genera alone | genera pooled | presences in the pool |
|---|---|---:|---:|---:|
| saprotroph main | all thinned box presences (as V9) | 57 | 79 | 576 |
| saprotroph side | all thinned box presences (as V9) | 78 | 106 | 808 |
| saprotroph main | presences entering a fit (D147) | 47 | 77 | 564 |
| saprotroph side | presences entering a fit (D147) | 66 | 104 | 798 |
| mycorrhizal main (V9) | presences entering a fit (D147) | 44 | 40 | 285 |

### Table 3. Presences by level III block

Box columns: thinned presences in the box (V9's tally, by the 250 m cell centre). Entering columns: presences that would enter a fit (P4's cell codes, T6's effort frame; US only). Bold: a forested block (D139) in the fit at or above 30 entering presences.

| level III block | forested (D139) | saprotroph main, box US | box Canada | entering: saprotroph main | entering: saprotroph side | entering: mycorrhizal main |
|---|---|---:|---:|---:|---:|---:|
| 7.1.8 Coastal Range | yes | 3,742 | 0 | **2,963** | **4,712** | **5,992** |
| 7.1.7 Strait of Georgia/Puget Lowland | yes | 5,238 | 1,448 | **2,832** | **3,934** | **2,330** |
| 6.2.7 Cascades | yes | 1,254 | 0 | **1,186** | **1,792** | **3,137** |
| 7.1.9 Willamette Valley | yes | 2,804 | 0 | **1,076** | **1,353** | **636** |
| 6.2.5 North Cascades | yes | 406 | 0 | **376** | **589** | **1,422** |
| 6.2.11 Klamath Mountains | yes | 497 | 0 | **373** | **572** | **462** |
| 6.2.3 Columbia Mountains/Northern Rockies | yes | 284 | 0 | **200** | **325** | **463** |
| 6.2.15 Idaho Batholith | yes | 167 | 0 | **148** | **255** | **410** |
| 6.2.8 Eastern Cascades Slopes and Foothills | yes | 174 | 0 | **123** | **198** | **229** |
| 6.2.13 Wasatch and Uinta Mountains | yes | 110 | 0 | **90** | **114** | **179** |
| 6.2.9 Blue Mountains | yes | 92 | 0 | **60** | **86** | **141** |
| 6.2.10 Middle Rockies | yes | 97 | 0 | **44** | **67** | **91** |
| 11.1.1 Central California Foothills and Coastal Mountains | yes | 120 | 0 | **31** | **40** | **37** |
| 10.1.3 Northern Basin and Range | no | 66 | 0 | 29 | 33 | 15 |
| 10.1.2 Columbia Plateau | no | 121 | 0 | 20 | 27 | 6 |
| 10.1.5 Central Basin and Range | no | 280 | 0 | 13 | 15 | 6 |
| 6.2.4 Canadian Rockies | yes | 15 | 0 | 13 | **30** | **53** |
| 6.2.12 Sierra Nevada | yes | 8 | 0 | 7 | 13 | 7 |
| 10.1.8 Snake River Plain | no | 197 | 0 | 5 | 6 | 7 |
| 11.1.2 Central California Valley | no | 14 | 0 | 2 | 2 | 1 |
| 10.1.4 Wyoming Basin | no | 0 | 0 | 0 | 0 | 0 |
| 10.1.6 Colorado Plateaus | yes | 0 | 0 | 0 | 0 | 0 |
| 7.1.5 Coastal Western Hemlock-Sitka Spruce Forests | yes (not in the fit) | 0 | 44 | 0 | 0 | 0 |
| 9.3.1 Northwestern Glaciated Plains | no | 2 | 0 | 0 | 0 | 0 |
| 9.3.3 Northwestern Great Plains | yes | 0 | 0 | 0 | 0 | 0 |
| none (outside every block) | | 0 | 0 | | | |

### Table 4. Genera of the saprotroph main run, thinned box presences

Alone (57): Stropharia 1,920; Agaricus 1,240; Strobilurus 787; Nidula 743; Leucocoprinus 723; Coprinopsis 669; Lycoperdon 665; Aleuria 649; Coprinellus 631; Marasmiellus 628; Chlorophyllum 588; Leratiomyces 570; Auriscalpium 531; Cyathus 505; Clitocybe 418; Agrocybe 403; Crucibulum 344; Lepiota 343; Pluteus 316; Tubaria 303; Geastrum 267; Verpa 237; Leucoagaricus 224; Psilocybe 204; Gymnopus 188; Conocybe 186; Cystoderma 169; Clitopilus 154; Calvatia 149; Panaeolina 149; Deconica 139; Macrocystidia 132; Phallus 130; Baeospora 108; Plectania 106; Rhodocollybia 103; Parasola 99; Cystodermella 93; Floccularia 92; Connopus 87; Clavicorona 84; Caulorhiza 72; Paralepista 66; Calbovista 66; Ampulloclitocybe 64; Battarrea 53; Infundibulicybe 52; Roridomyces 50; Lacrymaria 46; Pseudoomphalina 43; Entocybe 40; Pseudoclitocybe 36; Callistosporium 35; Pseudoplectania 34; Leucocybe 32; Crinipellis 32; Nidularia 30.

Pooled (79 genera, 576 presences): Volvopluteus 29; Phaeoclavulina 29; Mutinus 27; Gastropila 23; Heyderia 23; Aphroditeola 23; Pseudolaccaria 23; Myxomphalia 23; Rhizocybe 22; Montagnea 21; Hemimycena 20; Bovista 19; Calocybe 18; Mycetinis 18; Vibrissea 17; Neournula 14; Echinoderma 12; Volvariella 11; Trochila 11; Lysurus 10; Lepista 10; Tephrocybe 9; Clathrus 8; Rhodophana 8; Flammulaster 8; Aspropaxillus 7; Phaeolepiota 7; Gamundia 6; Meottomyces 6; Pseudaleuria 5; Myochromella 5; Mythicomyces 5; Galeropsis 5; Pseudopithyella 4; Trappea 4; Microglossum 4; Resinomycena 4; Gerhardtia 4; Cystolepiota 3; Endoptychum 3; Lanzia 3; Cantharocybe 3; Mycenastrum 3; Cyathicula 3; Tulostoma 3; Sarcoleotia 3; Stagnicola 3; Zhuliangomyces 2; Schenella 2; Clitopilopsis 2; Mycopan 2; Harmajaea 2; Sagaranella 2; Atractosporocybe 2; Paraxerula 2; Melanophyllum 2; Leucoscypha 2; Micromphale 2; Pholiotina 2; Tetrapyrgos 2; Chlamydopus 2; Nidulariopsis 2; Brunnipila 1; Discinella 1; Vascellum 1; Limacella 1; Xanthoporia 1; Cercopemyces 1; Rhizomarasmius 1; Cryptomarasmius 1; Amaurodon 1; Kjeldsenia 1; Pseudocolus 1; Singerocybe 1; Delicatula 1; Phaeogalera 1; Pseudotricharina 1; Lactocollybia 1; Gastrosporium 1.

Genera the side run adds (thinned box presences): Mycena 1,855; Hygrocybe 815; Hygrophoropsis 645; Marasmius 600; Morchella 540; Clavaria 291; Gliophorus 289; Armillaria 268; Leucopaxillus 206; Arrhenia 204; Coccomyces 169; Clavulinopsis 161; Cuphophyllus 132; Geopyxis 91; Chromosera 81; Lachnum 69; Melanoleuca 69; Porpolomopsis 41; Spathularia 39; Ramariopsis 39; Cudonia 33; Mitrula 29; Crassisporium 28; Anthracobia 25; Pyronema 21; Trichoglossum 14; Plicaria 14; Geoglossum 11; Humidicutis 11; Pachycudonia 10; Cantharellula 8; Hodophilus 7; Pseudobaeospora 7; Byssonectria 7; Macrotyphula 6; Tricharina 5; Marthamyces 5; Megacollybia 4; Omphalina 4; Cudoniella 3; Lophomerum 3; Hymenoscyphus 3; Glutinoglossum 2; Cheilymenia 1; Calyptella 1; Bryoglossum 1; Bogbodia 1; Nolanea 1.


## Can condition 3 be tested?

**Yes, as far as the count goes.**

- **Blocks.** The saprotroph main run has at least 30 entering presences in 13 of the 17 forested blocks in the fit. The mycorrhizal group reaches 30 in 14. Every one of the 13 is also informative for the mycorrhizal group, so the host-specific contrast has 13 shared forested blocks for a block-clustered interval. That is one fewer than condition 1 had.
  - The block lost is 6.2.4 Canadian Rockies: 13 saprotroph presences against 53 mycorrhizal.
  - The other three forested blocks are under 30 for both groups: 10.1.6 Colorado Plateaus (0), 6.2.12 Sierra Nevada (7) and 9.3.3 Northwestern Great Plains (0).
  - The side run reaches 14.
- **Presences.** The main run has 9,591 entering presences, 61% of the mycorrhizal group's 15,624, with 47 genera counting alone.
- **What the count cannot answer.** Whether the contrast's interval will be narrow enough to clear zero is a question for the fit, which is the second point of no return and was not passed.
- **Concentration.** 84% of the entering presences sit in four blocks: Coastal Range 2,963, Puget Lowland 2,832, Cascades 1,186 and Willamette Valley 1,076. Condition 1's block interval on the mycorrhizal group was already wide relative to its point (+0.0027, −0.0004 to +0.0081).

## Observations, not verdicts

- **Many presences are lost before the fit.** 5,300 of the main run's 17,403 thinned presences (30%) fall in cells with no tree shares (P4 code 4), against 18% for the mycorrhizal group (4,160 of 23,069). The background is drawn from eligible cells only, so a fit would see only the group's presences in forested cells. Another 1,492 are in Canada (code 3).
- **The main run has none of the largest litter genera.** Mycena (1,855), Marasmius (600), Hygrocybe (815) and Morchella (540) all carry a secondary lifestyle, so they are in the side run only, as ruled.
- **Armillaria (268) is in the side run.** FungalTraits gives it primary `litter_saprotroph` with secondary `plant_pathogen`. The rule as ruled puts it there; whether it suits a "not the hosts" comparison is a question for the owner, not answered here.

## Evidence

- **Tests first, over stubs.**
  - Step 1 (e8551d6): all 6 tests in `tests/test_t7_condition2_by_block.py` failed on the stubs, on nan values, no refusal and missing keys. After that commit, one test's data was changed (c94ae0c): the original cross-block case failed with a ValueError when a block draw held no pair, a fault in the test data rather than the rule. The replacement data was not run over the stub. Revert c2 shows it bites.
  - Step 2 (0782e20): 6 of the 7 tests in `tests/test_t7_saprotroph_group.py` failed on the stubs. The unspecified-saprotroph exclusion test passed over the stub, because empty sets satisfy it; revert p1 shows it bites.
- **Revert checks.** Every revert failed with a message specific to its own edit, built in a scratch worktree with the compile and collection log read first. Files were restored from saved copies, and the forward lines were confirmed present afterwards.
  - Step 1: 3 reverts (`2026-10-17-t7-part-a/condition2-by-block/revert_checks.txt`).
  - Step 2: 6 reverts (`2026-10-17-t7-part-c/revert_checks.txt`). Revert p1, with `unspecified_saprotroph` added, gives 709 = 669 + 40, matching the 40 found beforehand.
- **Suite.** Read from JUnit XML: t7-part-a at da25950 ran 688 tests with 0 failures and 0 errors; t7-part-c (this commit's tree) ran 695, which is 688 plus the 7 new tests, also with 0 failures and 0 errors. ruff check and format are clean.

## Not checked

- No fit and no host-specific contrast: condition 3 itself is untested.
- The licence track was not counted for this group, because the dispatch did not ask for it.
- Records named only to family: no family-level side run was built for this group, because no ruling covers one. They join neither run.
- The rule's genus names were not checked against GBIF's genus spellings beyond the join itself; this is the same limitation as V9.

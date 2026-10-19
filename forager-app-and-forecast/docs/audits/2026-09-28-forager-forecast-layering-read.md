# What the map layers are for: a read of forager-forecast (read-only, 2026-09-28)

**Asked by the owner:** "Look at forager-forecast repo for details on what the layering is for."
**Read at:** `slayer8366/forager-forecast` `origin/main` `876156b6dea613e95730f41e3e5f870aecdd5995`, through git objects only. `origin/d55-artifact-contract` (`2d8cc8f`) is merged into it (merge `c0fd3fb`). D60 is the newest decision.
**By:** an Explore subagent of the planner session. The planner recorded this from its hand-back, unedited in substance.

**Abbreviations.** Paths are `path:line` at `876156b`: DEC = `docs/planning/DECISIONS.md`, SPEC = `docs/planning/SPEC.md`, SH = `docs/planning/START_HERE.md`, TASKS = `docs/planning/TASKS.md`, VET = `docs/audits/2026-09-21-d55-vetting-report.md`.

**D58.** This record names the forbidden phrases only as "the three phrases D58 forbids". It does not repeat them.

## 1. Purpose

**The goal:** "A forager in North America opens a map and sees a calibrated weekly sighting chance for a forager group in their area, with honest gaps wherever the model has no support" (SPEC:7-9). SH:8-9 adds that it is shown "only where the model beats a seasonal calendar."

**What sighting chance means:** "The chance a forager group is reported in a weather cell and week, given at least one fungal observation of any kind there that week." SH:33 says what it never means, and D12 (DEC:56) and R3 (SPEC:66-69) fix the definition. The reason is D11 (DEC:57): the records are presence-only, so an absolute chance of fruiting cannot be estimated.

**Other fixed terms:**
- "Calibrated" (SH:34).
- "Relative habitat" is 250 m shading with no percent (SH:35).

**The model** is habitat × trigger × observation, with a joint model as the challenger (D2, DEC:66; SPEC:17, :42-43). It works on:
- a 0.1° weather cell, with rain from ERA5 at 0.25° (D19, DEC:49; D54, DEC:14);
- genus-level groups (SH:36, SPEC:49), in the order chanterelles, then chicken of the woods as the control, then morels, then king boletes (D9, DEC:59; SPEC:13-14).

**Acceptance:** "The map shows sighting chance, shows uncertainty and data dates on tap, and leaves masked areas blank" (SPEC:100). T11's check is "a tapped cell shows the same numbers as the scoring table", which is device-only (TASKS:90-94). An ecoregion is shown only after it beats the calendar baseline (D5, DEC:63; R2, SPEC:63-65).

## 2. What the app is expected to draw

**Sighting chance, one layer per group per week, at weather-cell scale.** The files are one per group per week per 1° block (DEC:13).

**Relative habitat at 250 m is not allowed yet** (DEC:13). No decision row allows it, and it "cannot be honest offline".

**Uncertainty is required on tap** (SPEC:100). No separate uncertainty layer is required.

**Ecoregions are publication units** (`docs/planning/DATA_REGISTER.md:25`, CC BY 4.0). No decision draws them.

**Individual conditions as their own layers: not found on main or on the D55 branch.** The owner's ruling 2 on the layer framework therefore needs a new decision in forager-forecast, and a change to D55. Rain is on a 0.25° grid shared by 4, 6 or 9 cells (`docs/audits/2026-09-18-t1-calendar-smoke-test-completion-report.md:38-39`).

**Not decided:** one group or several at once, a week picker, a group picker. The manifest names `groups[]` and one current `week`.

## 3. The artifact contract (D55, accepted with edits as D56, DEC:12-13; the target app is set by D57, DEC:11)

**Files:** GeoJSON, "split by 1 degree by 1 degree block, one file per group per week per block, under a dated path named in the manifest". The block size is provisional.

**Cell properties:**

| Property | Type as written |
|---|---|
| `group` | not stated |
| `week` | ISO week start |
| `chance` | 0 to 1 |
| `uncertainty_low`, `uncertainty_high` | 0 to 1 |
| `applicable` | boolean |
| `drivers` | "list of `{label, value}`, top first" |
| `weather_through` | date |
| `model_version` | not stated |

"Cells with `applicable` false may be omitted from the files; if present they carry the flag."

**Manifest fields:**
- `published_at`;
- `groups[]`, each with `key`, `display_name`, `gbif_taxon_key`, `inaturalist_taxon_id` and `rank`;
- `week`;
- `regions_published[]`;
- `attribution`, holding the D53 Copernicus text and anything else required;
- `layers[]`.

R4 adds model, weather and layer versions (SPEC:70-71).

**Attribution:** D53 (DEC:15), including "Contains modified Copernicus Climate Change Service information 2024". The full assembled string is not composed anywhere.

**Cadence:** nightly (SPEC:18). The weather archive lags by about 5 days (DEC:49).

**`applicable`:** set by the area of applicability (SPEC:61; TASKS:68). Cells outside it are transparent (R5, SPEC:72-73).

**Not stated:** the uncertainty interval's level and method; the meaning and type of a driver's `value`; how blocks align to the grid. ERA5-Land points lie on multiples of 0.1°, so cell edges fall at x.x5 (`docs/audits/2026-09-22-grid-positions-d51-report.md:13-18`).

## 4. What the app promises (D55, DEC:13; R8, SPEC:78-80)

The app:
- calls the number "sighting chance" and nothing else, with a unit test searching its copy for the forbidden terms;
- shows it only beside its reference class;
- draws nothing for unscored cells, with "no forecast here" in the legend;
- shows nothing finer than the weather cell;
- shows the attribution string on the map.

R8: "Only the weather-cell value carries a percent and the label sighting chance", checked by reading the legend and the tap panel.

The tap shows chance, uncertainty, top drivers and data dates (TASKS:92).

Where offline blocks are stored is "a Forager decision" (VET:121).

No colour, ramp or accessibility guidance was found.

The reference-class wording is not committed in forager-forecast. It lives in Forager-app. At `slayer8366/Forager-app` `0172c33`, `presentation/src/main/kotlin/com/zynergy/forager/presentation/SightingChance.kt:33-35` reads: "Chance this group is reported in each 11 km cell this week, where anyone is reporting fungi. Compare areas, not spots. A high chance is not a find." (read by the planner).

## 5. Gates

- **D22** (DEC:46): the repo is private and no licence has been chosen.
- **D29** (DEC:39): nothing derived from CC BY-NC records is published or shipped until the owner rules on commercial use. The ruling is still open (SH:77; VET:94; `docs/planning/RELEASE_CHECKLIST.md:42-47`).
- **D60** (DEC:8): until the model passes D5 and R3, "Forager's refusal is correct".
- **Nothing is published.** T4 to T11 have not started (TASKS:15).

## 6. What this changes in L0b (inferred by the reader; the owner's rulings follow in the plan)

1. **Condition layers have no data source yet.**
2. **Using the fixed term on synthetic numbers.** Putting "sighting chance" on fake numbers attaches the fixed term to values that are not the model's.
3. **Percent.** R8 allows a percent only on the chance layer.
4. **The legend** must carry the reference class and "no forecast here". A blank cell must look unlike a low-chance cell.
5. **The tap readout** must show uncertainty, dates and drivers.
6. **Group and week are the data's own keys.**
7. **Block alignment is unstated**, and cell edges fall at x.x5.
8. **No habitat layer yet.**
9. **Attribution** must carry the D53 text once the data is real.

## Could not determine

- The exact reference-class wording in forager-forecast (see Forager-app above).
- The uncertainty method.
- The semantics of a driver's `value`.
- The types of `model_version` and `group`.
- The block naming and alignment.
- The full attribution string.
- Any ruling on week or group selectors, ramps, accessibility or synthetic data.
- Whether D58's clause about carrying Forager-app's terms test still binds after D59.

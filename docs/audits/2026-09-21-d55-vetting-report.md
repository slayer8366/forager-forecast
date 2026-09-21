# D55 vetting report: the artifact contract proposed from the Forager app

Written 2026-09-21 by the session that copied the proposal in. **Base:** forager-forecast main
82f28b6, branch d55-artifact-contract. **Proposal read from:** slayer8366/Forager-app at ecfcbde,
`docs/research/2026-09-20-proposed-decision-d55-artifact-contract.md`, blob 86e54c5. The copy at
`docs/audits/2026-09-20-proposed-decision-d55-artifact-contract.md` has the same blob hash
(`git hash-object` against the GitHub contents API's `sha`), so it is byte-identical.

The owner's instruction, 2026-09-21: "Copy it and either accept fully, accept with edits, or
decline." The verdict is **accept with edits**, recorded as D56. This file is the evidence behind
it. Every claim below names where it was read; anything not read is marked.

## The six premises the proposal asked a vetting agent to check

| # | Premise as stated | Result | Where read |
| --- | --- | --- | --- |
| 1 | origin/main tip is 82f28b6 and the last row is D54 | Holds. Fetched 2026-09-21; origin/main is 82f28b6; the highest D number in DECISIONS.md is D54 | `git rev-parse origin/main`; `docs/planning/DECISIONS.md` line 8 |
| 2 | T11 still reads "write weather-cell polygons with sighting chance, uncertainty, top drivers and data dates to a second archive" at TASKS.md:90-92 | Holds. Header at line 90, the quoted "Does" line at 92 | `docs/planning/TASKS.md:90-92` at 82f28b6 |
| 3 | D53 is the Copernicus attribution ruling, at DECISIONS.md:9 | Holds. Line 9 begins "D53 ... Copernicus attribution in anything that ships" | `docs/planning/DECISIONS.md:9` at 82f28b6 |
| 4 | The MapLibre offline claim was read at main, not at the 13.6.1 tag the app uses; confirm the tag has no runtime source path and no pmtiles handling | Holds at the tag, with two wording corrections (next section) | See the MapLibre section |
| 5 | The 150,000-cell figure is inferred from area, not counted | Stands as an order of magnitude. Area arithmetic done here: US plus Canada land area about 18.2 million km2, a 0.1 degree cell 79 to 94 km2 between 40 and 50 degrees north, giving about 190,000 to 230,000 cells before masking. Still not a count | This session's arithmetic, not a dataset |
| 6 | Written to this repo's style: no em dashes, plain words, short sentences | Holds. Zero em dashes and zero en dashes in the file. Row column counts match: six for DECISIONS.md, three for START_HERE.md's session log, three for docs/audits/README.md | `grep -c` on the copied file; the three table headers |

## MapLibre, read at the app's pinned tag

Forager-app pins MapLibre 13.6.1 (`gradle/libs.versions.toml:15` at ecfcbde, `maplibre = "13.6.1"`,
module `org.maplibre.gl:android-sdk`). The tag `android-v13.6.1` exists on
maplibre/maplibre-native. Everything below was read through the GitHub contents API at that
tag; nothing was built or run.

- `platform/default/src/mln/storage/offline_download.cpp` is 565 lines and **byte-identical**
  at `android-v13.6.1` and at `main` (`diff` on the two downloads printed nothing). The
  proposal's read at main therefore holds at the tag.
- The string `pmtiles` does not occur in that file at either ref.
- The download reads the style document at the region's style URL (line 248) and iterates
  `parser.sources` (line 261): the sources declared in that document. There is no path that
  reads a source added to the map at runtime.
- Every fetch goes through `onlineFileSource.request` (line 522). The PMTiles file source is a
  separate source that `main_resource_loader.cpp` consults before the online one (lines 75 to
  77); the offline download never consults it, so a `pmtiles://` tileset URL cannot be fetched
  into an offline pack.
- PR #4290 ("core: ambient cache for pmtile sources", merged 2026-06-06) **is contained in the
  tag**: the GitHub compare of `android-v13.6.1` against its merge commit reports the merge
  commit 118 commits behind the tag and 0 ahead. So the ambient cache the proposal's rejected
  alternative relies on is in the app's build, which changes nothing about the rejection: an
  ambient cache is not a promise.

### Two corrections to D55's Reason column

1. **The source-type list is incomplete.** D55 says the download "queues only the vector,
   raster and raster-DEM sources declared there". The switch at lines 185 to 223 (and its twin at
   299 to 337) also handles `SourceType::GeoJSON` and `SourceType::Image` when the source has a
   URL, counting the file as one required resource. So a GeoJSON file declared by URL in the
   style document is downloaded with the region. This does not change the conclusion: such a
   file is frozen at download time and every saved region would need a re-download nightly,
   which is the same reason D55 gives for rejecting the style-document raster. It changes the
   sentence, which D56 restates.
2. **A paraphrase stated as a quotation.** D55 says PR #4290 "states it does not add offline
   pack support". The PR body describes ambient caching for PMTiles sources and a synthetic cache
   key; its comments and the issue it resolves (#3690, "Allow Caching Requests for PMTiles
   Sources") speak only of the ambient cache. None of them mentions offline packs. The claim is
   true by omission and by the code above, not by anything the PR says. D56 restates it as
   silence plus the code.

## The verdict and why

Accept with edits. No premise failed. The decision text of D55 (columns 3 of the row: the
per-block files, the named properties, the named manifest fields, the app's promises, the
provisional block size) is unchanged; the two edits are to the Reason column only. Declining was
considered and rejected: the offline argument holds at the pinned tag, and without a per-area
form the app cannot be honest in a saved region. Accepting fully was rejected because it would
file two wrong sentences in a record that is never edited. The received file is untouched; the
corrections live in D56 and here, as the record's supersede rule requires.

Precedent for the shape: proposed rulings D24 to D32 were filed as
`docs/audits/2026-09-18-proposed-rulings-d24-d32-v2.md` plus rows marked Proposed in
DECISIONS.md, then ruled on in later rows. D55 follows the same shape, with D56 as the ruling row.

## Who made the call

The vetting session, not the owner in person. The owner delegated it in the words quoted above,
and D56 quotes them. The owner overturns it, if at all, with a new row; D55 and D56 are not edited.

## Not checked, and left open

- The Forager-app research documents the proposal cites for its reasoning
  (`2026-09-20-forecast-integration-and-map-layering.md` and
  `2026-09-20-forecast-artifact-contract-proposal.md`) were read for their claims list only, not
  audited line by line.
- Whether the PMTiles file source honours `Resource::Usage::Offline` in any other way was not
  read; it is not on the offline download's path, which is what the claim needs.
- The cell count is arithmetic over land area, not a count of cells in any grid file.
- Nothing here has been run on a device. The 1 degree block size stays provisional, as D55 says.
- The commercial-use ruling (D29) is open and still gates any forecast layer in the app.
- This branch is not merged. Under D40 a merge needs the owner's written authorisation naming
  the branch.

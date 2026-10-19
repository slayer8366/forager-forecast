# 2026-09-27: the map's layers and the app's forecast data, pulse for the layer framework

Read-only pulse in the cloud planner session at `origin/journal-redesign` `3025bab`. No build. Condensed by the planner; "inferred" is the pulse's marking. Paths under `app/src/main/java/com/zynergylabs/forager/app/`.

## Layers today

- Basemaps: one raster source and layer `basemap` per online style (`ui/map/BasemapStyles.kt:72-89, :199-200`); the offline style is one vector source and 57 layers from the worker (`map/OfflineStyle.kt:18`).
- Overlays: all added in `initializeOverlayLayers` (`ui/map/SightingsMap.kt:630-696`) with plain `style.addLayer`, so **insertion order is the z-order**; no `addLayerBelow/Above/At` anywhere in `main/`. Bottom to top: marker images; offline-region fill and dashed outline; search centre; sightings (circle); breadcrumb casing and line; kept-track casing and line; planned trips, waypoints, finds, photos (symbols). Ids at `:1137-1159`. The comment at `:614-615` describing the order is stale.
- Data: every source is a `GeoJsonSource` created empty on each style load and filled by `refreshOverlayData` (`:718-741`) from pure builders (`:885-1132`), all pushed by one `LaunchedEffect` keyed on the style and 12 inputs (`:482-491`), which re-pushes all nine sources on any change, including about every 15 s while recording a track (`:497`). Nothing is loaded from a file or URL.
- Style reload (basemap, offline, night; guarded by `needsStyleReload`, `BasemapStyles.kt:141-159, :196`) drops every layer; the callback recolours the offline style for night, re-adds the overlays, and refills them (`SightingsMap.kt:420-475`). Colours are fixed into layer properties, so a palette change forces a reload.
- Data-driven styling: only the sighting ring's stroke, a boolean `switchCase` (`:959-980`); the file records that comparing an id inside an expression never selected anything on real hardware (`:935-944`), so a precomputed property per feature is the safer pattern (inferred).
- **Tap-to-query exists for sightings only** (`:318-328`); `queryRenderedFeatures` is called nowhere else.
- **Long-press: every production caller passes `{}`** (`AvailabilityCompactMapUi.kt`, `AvailabilityWideLayoutUi.kt`, `CartographyEntryReportScreen.kt`, `CentrePinLocationPicker.kt`; also stated at `SightingsMap.kt:89-95`, `MapSlot.kt:249-255`).

## The map's interface

- `MapSlot` (`ui/map/MapSlot.kt:263-309`) has 9 parameters; **at 10 the Compose compiler crashes** (`:14-26`, `:315-320`), so new layer state must live inside `MapOverlayContent` (`:140-230`, one named field per marker kind) or `MapRenderMode` (`:40-138`). `SightingsMapSlot` maps them by hand onto `SightingsMap`'s 26 parameters.
- **No user layer toggles exist.** The map's "Layers" button (`ui/map/MapChrome.kt:438-450`) opens `MapModePicker` (`:127-190`): three chips choosing the basemap. Night Maps is a Settings checkbox. Markers are hidden only by passing empty lists; no `visibility` property is used anywhere.

## What a forecast layer must respect

- Night mode inverts only the basemap raster (`BasemapStyles.kt:56-61, :86`), so overlays are not inverted; on the offline style `applyOfflineNightRecolour` (`SightingsMap.kt:1203-1238`) recolours every layer present, safe for overlays only because it runs before they are added (`:459-460`). `nightColorOf` (`ui/map/NightColour.kt:39`) can derive night variants.
- `MapPalette` (`ui/theme/MapPalette.kt:47-111`) holds 13 marker roles per mode, mostly purples and magentas; a forecast ramp through purple would collide (inferred). Map chrome follows the app's dark theme, not the map's night mode (`MapChrome.kt:218-238`).
- Attribution: a single-string caption at bottom-start (`SightingsMap.kt:594-603`, `mapAttributionFor`, `BasemapStyles.kt:130-131`) plus MapLibre's own button; a forecast credit needs the caption to hold several. **No legend exists** anywhere.

## Forecast data the app has

**All of it is for one point, the search region's centre**; nothing produces values over an area. `GetTodaysForecastUseCase`, `GetConditionsUseCase`, `ComputeTripWindowsUseCase` (14 observed plus 7 forecast days), `ComputeFruitingLagDistributionUseCase`, `PredictAvailabilityUseCase` (species ranked by relative frequency; its own doc calls it a description of the past, not a weather-style forecast), and `ForagingWeatherGuidance`. Thresholds in `domain/FruitingPatternAssumptions.kt` are rules of thumb, not fitted (:8). Open-Meteo is asked for one latitude and longitude (`data/repository/OpenMeteoWeatherProvider.kt:51-52`): daily precipitation and ET0, hourly soil moisture and temperature at several depths, 14 past and 7 forecast days.

## Tiles and stored data

No raster, image, vector-overlay, heatmap or hillshade source exists; the only fill is the offline-region circle at fixed opacity. No path downloads and stores GeoJSON for the map. The app has no client PMTiles protocol; PMTiles lives only in the Cloudflare worker. Offline downloads are keyed to the one offline style's sources (`map/OfflineStyle.kt:3-16`), consistent with forager-forecast D55/D56 (inferred from the keying, not tested against MapLibre).

## Tests

Map classes cannot be built on the JVM (`SightingsMapOverlayDataTest.kt:20-54`), so tests cover pure builders, expressions, `LineLayerSpec` descriptions and style-selection functions; screen tests stub the whole map. A framework keeps headless: the layer list as data (ids, order, type, palette role), cell-to-feature and cell-to-class as pure functions, the unscored-cell rule, the legend model, visibility decisions, and loading and staleness of stored GeoJSON behind a project-owned interface. `SightingsMap` stays the only place specs become native layers.

## Constraints

The 10-parameter ceiling; surfaces over the map swallow touches (CLAUDE.md) and need coordinate-touch tests; one click listener to extend with a precedence order (a cell fill under every marker would otherwise catch every missed tap); the sighting bubble's re-positioning on camera idle; B2's landscape corners and the attribution caption; the one data effect (a large forecast collection needs its own keyed effect); nothing enforces layer order.

## Correction to the plan

The M1 addendum in `docs/plans/journal-redesign.md` says long-press "drops a point today (`SightingsMap.kt:334`)". It does not: the listener exists but every production caller passes `{}`. Recorded in the plan as a correction.

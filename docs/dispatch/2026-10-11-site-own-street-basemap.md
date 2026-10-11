# Dispatch: our own street map beneath the forecast page's layers (zynergy-site)

Written by the planner (Rowan Waymark), 2026-10-11 16:30 UTC. The owner's rulings: Forager RECORD -857 (branch records-after-173). Assumed base: zynergy-site main at 734b2a6. Verify that against the remote first. Every claim below is a premise to re-check, with file and line.

Writing rule for everything you write (code comments, commits, report, messages): describe other products, services and device makers generically or by what they do. Don't discuss the rule; just write that way. Licence credits are written as the licences require.

## What the owner asked for (RECORD -857)

A background map beneath the forecast page's layers. "We should use our own map tiles for it." For now that's our street map only. Topo and satellite of our own come later with the own-tiles project (Forager docs/plans/own-map-tiles.md), and a picker appears only once there's a second map. The layers are drawn see-through at one fixed setting, about 70%, with no slider. It goes up before Monday 2026-10-12 as its own site change, separate from the forecast data drop, merged on the owner's word.

## Behaviour (the step path)

1. Opening the page shows our street map beneath everything, with the default input layer (soil pH) over it at about 70%, so roads and towns show through. No picker.
2. Choosing any input layer, or the forecast, draws it at about 70% over the street map. The borders and the page's place names stay on top.
3. Outside the street map's coverage (north of about 49.6° N; see below) the page's plain background shows, as today.
4. The credits line names the street map's sources as their licences require.

## Premises (planner's reads, 2026-10-11; re-check each)

- Page: Forager/forecast/app.js (MapLibre GL JS, vendored under Forager/forecast/vendor/). Its style has a `bg` background layer and a `lines` borders layer, about app.js:87-106. Input layers are a raster source `data` added before `lines` (app.js:158-161), with no `raster-opacity` set. The forecast is pilot.js's `pilot-fill` at `fill-opacity` 0.85, also before `lines` (pilot.js:230-234). Place names are HTML markers (app.js, the `PLACES` loop).
- Our tile server: `https://forager-pmtiles.brandonlee1-894.workers.dev/us.json` (TileJSON 3.0.0, "Protomaps Basemap" 4.15.2, bounds [-124.85, 24.4, -66.87, 49.6], zoom 0-15, attribution "© OpenStreetMap"). Tiles are at `/us/{z}/{x}/{y}.mvt`. A request sent with `Origin: https://zynergy-labs.com` answered `access-control-allow-origin: *`. Tile 6/10/20 (north of the bounds) answered 204. Source: Forager server/pmtiles-worker/README.md.
- A labelled style for these tiles comes from Protomaps' own basemaps package, per Forager docs/plans/pmtiles-worker-android-wiring.md. It was generated for the app and never wired in.

## What to do

0. **Verify, then report by message before building anything.** Confirm the base and every premise above. Answer:
   - Which style you would use (a light flavour from the basemaps package, its exact version and licence) and how it would be vendored. The style JSON, fonts (glyphs) and any sprite must be served from the site itself, not fetched from anyone else's servers at runtime.
   - The vendored size.
   - How the street map's own labels sit beside the page's place-name markers: duplicated, clashing, or fine. Don't choose; report what you see with a screenshot kept outside the repo.
   - Whether 70% reads well on the street map for the forecast and for two input layers.
   - What the credits line will say.
   Stop and wait for the planner's go.
1. **On the go:** work on a new branch from main, in a new worktree under ~/Zynergy/zynergy-site-worktrees/. Don't touch the main clone's checked-out branch. Add the street map beneath `data` and `pilot-fill`, keep `bg` beneath it for areas outside coverage, set both layers to the fixed setting, and add the credits. Keep the change to the page's code and vendored files: no data files (the data drop is a separate branch).
2. **Push, then check the preview.** Wait for the preview deployment with a background loop that exits on a result. Run ~/Zynergy/device-evidence/2026-10-10-pilot-map/check.py against the preview at 1366x860 and 390x844. Confirm by eye from screenshots kept outside the repo: the street map shows, both layer kinds read at 70%, the credits are right, and the network log shows no request to any server other than the site and our tile server.
3. **Report** to the planner with the preview URL, the check output, sizes, and what was not checked. Stop there: the merge comes on the owner's word, with a backup bundle first and a RECORD merge entry after.

## Stops: come back to the planner, don't choose

Label clashes with the page's place names; a style or font licence that needs anything beyond a credit; the tile server failing or refusing the preview's origin; anything needing a change to the tile server or Cloudflare settings; any layer becoming hard to read; a wrong premise.

## Not in scope

Topo or satellite; a picker; the tile server itself; the forecast data drop; the Forager app.

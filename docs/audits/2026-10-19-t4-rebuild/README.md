# T4 rebuild, 2026-10-19: re-downloaded and rebuilt, matching the filed record

Answers `docs/dispatch/2026-10-19-t4-rebuild.md` with its Amendment 1. Ash Transect, branch t4-rebuild, code at origin/main 80f61a8 (T4's code is unchanged from b78ab5c; step-0 report). Environment: rasterio 1.5.1, GDAL 3.12.4, PROJ 9.8.1, numpy 2.5.3 (`step0/environment.out.txt`), the same versions as the 2026-10-06 build.

## Result

| Check | Result | Evidence |
|---|---|---|
| Nine VRTs against ISRIC's checksum file fetched today, and against the 2026-10-06 values | 9 of 9 equal to both | `compare_fetch.out.txt` section 2 |
| `request.json`, every field except `requested_at` | ETag, Last-Modified, Content-Length, pixel window, source grid, no-data value, ISRIC checksums: all equal. The nine `layers[i].sha256` values differ, as predicted: they hash files carrying today's `requested_at` tag | `compare_fetch.out.txt` section 1 |
| Each subset, re-written in scratch with its filed `source` and `requested_at` | 9 of 9 equal to the filed sha256 (full hashes) | `compare_fetch.out.txt` section 3 |
| `master.tif` | `9fe55bc231cabbdac923dc40aa5f0e47fb7b13325295605174e843bb5aefe72f`, 14,685,784 bytes: equal | `filed_outputs_check.out.txt`, `stored_sha256.txt` |
| Archive | `84905e335c0390b2b7c32348ace86fc25fa372101b53530ea9af6c4d1ea0ee34`, 891,388 bytes, 78 tiles, zooms 5 to 9: equal | the same, and `build.json` |
| Ten-cell check | exit 0; output byte-identical to `2026-10-06-t4-build/ten_cells_real.json` | `ten_cells_rebuild.json`, `ten_cells_cmp.out.txt` |

So the publisher's pixels in T4's window are unchanged since 2026-10-06, and the rebuilt master grid and archive are the 2026-10-06 files byte for byte.

## A wrong first attempt, kept

The first comparison (`compare_fetch_v1.py.txt`, output `compare_fetch_v1.out.txt`) got 0 of 9. It took the CRS from the stored GeoTIFF, but `fetch_layer` takes it from the VRT (`src.crs`, `src/forager_forecast/soilgrids.py:150-158`), and a GeoTIFF's CRS does not round-trip byte for byte. `rewrite_fidelity.py.txt` showed this on the real files before any fix: re-writing today's subsets with their own tags reproduced them only with the CRS from the VRT (9 of 9), never from the GeoTIFF (0 of 9). The step-0 synthetic probe had missed this because its source was a GeoTIFF. After that one correction, `compare_fetch.py.txt` matched 9 of 9.

## Stored

`~/Zynergy/forecast-data/t4/`, 58 MB: 24 files at 0444 and 4 folders at 0555. Every file's size and sha256 is in `stored_sizes.txt` and `stored_sha256.txt`. The subsets carry today's `requested_at` tag, as written. Registered in `docs/planning/DATA_REGISTER.md`, the row after SoilGrids, with ISRIC's licence as read at source today.

## Runs

- **Fetch:** unit `t4-rebuild-fetch`, 21:52:14 to 21:57:21 UTC, 208.7 MB peak (journal).
- **Build:** unit `t4-rebuild-build`, 21:58:50 to about 22:00:50 UTC, Result=success, exit 0, regrid 113 s (`build.json`).
- **Limits:** both units ran with MemoryMax 5G, MemorySwapMax 0, Nice 10 and idle I/O.
- **Errors:** stderr was empty for both.
- **Not touched:** t6b-night.

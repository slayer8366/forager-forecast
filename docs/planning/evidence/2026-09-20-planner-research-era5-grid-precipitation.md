# Planner research note: ERA5 grids and the precipitation convention

Written by the planning session on 2026-09-20, after the Cowork report read 22:27 to 22:33 PDT.
Project: forager-forecast. For filing in docs/planning/evidence/.

Every fact below is from a public page read by the planner through web search on 2026-09-20. Quotes are short and each carries its URL. Facts marked "memory" were not verified against a page and should not be cited.

## 1. ERA5 hourly data on single levels is on a 0.25° grid

Source: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview, and https://www.ecmwf.int/en/forecasts/datasets/era5-hourly-data-single-levels-1940-present

The overview states the data "has been regridded to a regular lat-lon grid of 0.25 degrees for the reanalysis". ERA5-Land is 0.1°. Any variable taken from ERA5 single levels sits on a grid 2.5 times coarser than the temperature grid.

## 2. ERA5-Land accumulations run from 00 UTC, and the 00 UTC value of day d+1 is the total for day d

Source: ECMWF, "Conversion table for accumulated variables (total precipitation/fluxes)", https://confluence.ecmwf.int/pages/viewpage.action?pageId=197702790

Quoted: accumulations in ERA5-Land "are accumulated from the beginning of the forecast to the end of the forecast step" and "the maximum accumulation is over 24 hours, i.e., from day=D, time=0 to day=D+1,time=0 (step=24)".

Consequences:
- Daily total precipitation for UTC day d is the single value stamped 00:00 on day d+1. It is not the sum of the 24 hourly values, which is roughly a factor of twelve too large.
- The UTC day is the accumulation boundary. This answers D24's open items V3 (precipitation convention) and V4 (UTC day boundary) for ERA5-Land.
- A request for daily precipitation needs only the 00:00 step of each day, so it is one value per day per cell.

Corroborated by ECMWF's user forum, https://forum.ecmwf.int/t/total-precipitation-values-not-in-range-era5-land-hourly-data-from-1981-to-present/1128, where support staff give the same rule and users report the daysum error.

## 3. ERA5-Land's 0.1° grid points sit at multiples of 0.1°, for full-grid files

Sources:
- NCAR GDEX mirror of ERA5-Land, https://gdex.ucar.edu/datasets/d633008/, gives the coverage as "0.1° x 0.1° from 0E to 359.9E and 90N to 90S (3600 x 1801 Latitude/Longitude)".
- A THREDDS coordinate listing of a delivered ERA5-Land file, https://thredds.climate.ncsu.edu/thredds/ncss/grid/ecmwf/era5land/TEMP/hourly/era5_land_202412.nc/dataset.html, shows latitude "start=90.000000 end=-90.000000 ... resolution=-0.100000 (npts=1801)" and longitude "start=0.000000 end=359.900000 ... resolution=0.100000 (npts=3600)".

Both describe full-globe files. For area requests, the Cowork report of 2026-09-20 records ECMWF's change of 25 February 2026: the store now crops the grid instead of re-interpolating onto a grid anchored at the request's south-west corner. Cropping preserves the global points, so area requests made after that date should also sit at multiples of 0.1°. This is a deduction from two sources, not a statement either makes. The delivered file's coordinate arrays settle it for any given pull, and that check stays as D46's method.

Longitudes are delivered in the range 0 to 360. Source: ECMWF, "ERA5: What is the spatial reference", https://confluence.ecmwf.int/display/CKB/ERA5:+What+is+the+spatial+reference, which states longitude values are "in the range [0;360] referenced to the Greenwich Prime Meridian". Any nearest-point code must convert western hemisphere longitudes before matching.

## 4. Not verified (memory)

- That ERA5-Land's total precipitation is the ERA5 forcing field regridded to 0.1°, carrying no information beyond ERA5's. Plausible from the ERA5-Land description as "a replay of the land component of ERA5", but not stated on any page read today.
- Where Open-Meteo's ERA5-Land grid points sit. Cowork found no statement. Open-Meteo returns the centre of the cell it used, so one pinned request answers it.

## Recommendation carried to the owner

Take daily precipitation from ERA5-Land hourly, 00:00 step only, on the same 0.1° grid as temperature, rather than from the ERA5 single-levels daily statistics on 0.25°. D19 names ERA5 for precipitation; the reason D19 gives should be read before this becomes a row.

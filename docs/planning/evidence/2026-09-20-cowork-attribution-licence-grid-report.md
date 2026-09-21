# Report: attribution wording, licence version and grid point positions

Written 2026-09-20 by Claude (Cowork session), in answer to the planning session's dispatch
"three reads from the Copernicus and Open-Meteo pages" (2026-09-20, about 22:15 PDT).

All pages were read on 2026-09-20 between 22:27 and 22:33 PDT, in the built-in browser, with the text
taken straight from each page and not through a summarising tool. Everything below is **observed**
unless marked **not found**. No account actions, no downloads, no repository writes.

Two findings matter most:

- Open-Meteo does not pick the nearest grid point by default, and it adjusts values for elevation by
  default. This bears on D46 and on the pinned-request equivalence test. See Part 3.
- The ERA5-Land daily-statistics dataset omits accumulated variables, including total precipitation.
  See "What a release must carry".

## Part 1: attribution wording and DOIs

Every dataset's "Citation and attribution" pop-up opens with the same rule: in addition to the
applicable licence, users must cite the CDS catalogue entry, and must give clear and visible
attribution to the Copernicus programme and to each data product used. The text under each heading
follows, copied exactly, including the pages' own typos and placeholders.

### reanalysis-era5-land

Read about 22:28 PDT. DOI shown on the page: 10.24381/cds.e2161bac. Observed.

Citing the CDS catalogue entry:

> Copernicus Climate Change Service (C3S)(2019): ERA5-Land hourly data from 1950 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS). DOI: 10.24381/cds.e2161bac (Accessed on DD-MMM-YYYY)

Attribution, Copernicus programme:

> Generated using or contains modified Copernicus Climate Change Service information <2019>. Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.

Citing the data:

> Muñoz Sabater, J. (2019): ERA5-Land hourly data from 1950 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS). DOI: 10.24381/cds.e2161bac (Accessed on DD-MMM-YYYY)

### reanalysis-era5-single-levels

Read 22:28 PDT. DOI shown on the page: 10.24381/cds.adbb2d47. Observed.

Citing the CDS catalogue entry:

> Copernicus Climate Change Service, Climate Data Store, (2023): ERA5 hourly data on single levels from 1940 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS). DOI: 10.24381/cds.adbb2d47 (Accessed on DD-MMM-YYYY)

Attribution, Copernicus programme:

> Generated using or contains modified Copernicus Climate Change Service information . Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.

The year is missing from that sentence on the page itself, leaving a space before the full stop. That
is not a copying error.

Citing the data (the page's heading reads "Citing the data::", with a double colon):

> Hersbach, H., Bell, B., Berrisford, P., Biavati, G., Horányi, A., Muñoz Sabater, J., Nicolas, J., Peubey, C., Radu, R., Rozum, I., Schepers, D., Simmons, A., Soci, C., Dee, D., Thépaut, J-N. (2023): ERA5 hourly data on single levels from 1940 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS), DOI: 10.24381/cds.adbb2d47 (Accessed on DD-MMM-YYYY)

### derived-era5-land-daily-statistics

Read 22:29 PDT. DOI shown in the page's DOI field: 10.24381/cds.e9c9c792. Observed. The page also
links 10.24381/cds.e2161bac, but only where it describes the hourly source data.

Citing the CDS catalogue entry:

> Copernicus Climate Change Service, Climate Data Store, (2024): ERA5-land post-processed daily-statistics from 1950 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS), DOI: 10.24381/cds.e9c9c792 (Accessed on DD-MMM-YYYY)

Attribution, Copernicus programme:

> [Generated using/Contains modified] Copernicus Climate Change Service information [year]. Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.

Data:

> Muñoz Sabater, J., Comyn-Platt, E., Hersbach, H., Bell, B., Berrisford, P., Biavati, G., Horányi, A., Muñoz Sabater, J., Nicolas, J., Peubey, C., Radu, R., Rozum, I., Schepers, D., Simmons, A., Soci, C., Dee, D., Thépaut, J-N., Cagnazo, C., Cucchi, M. (2024): ERA5-land post-processed daily-statistics from 1950 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS), DOI: 10.24381/cds.e9c9c792 (Accessed on DD-MMM-YYYY)

The author list contains "Muñoz Sabater, J." twice. That is on the page.

### derived-era5-single-levels-daily-statistics

Read 22:29 PDT. DOI shown in the page's DOI field: 10.24381/cds.4991cf48. Observed. The
10.24381/cds.adbb2d47 links on that page sit in the description of the hourly source.

Citing the CDS catalogue entry:

> Copernicus Climate Change Service, Climate Data Store, (2024): ERA5 post-processed daily-statistics on single levels from 1940 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS), DOI: 10.24381/cds.4991cf48 (Accessed on DD-MMM-YYYY)

Attribution, Copernicus programme:

> [Generated using/Contains modified] Copernicus Climate Change Service information [year]. Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.

Data:

> Hersbach, H., Comyn-Platt, E., Bell, B., Berrisford, P., Biavati, G., Horányi, A., Muñoz Sabater, J., Nicolas, J., Peubey, C., Radu, R., Rozum, I., Schepers, D., Simmons, A., Soci, C., Dee, D., Thépaut, J-N., Cagnazo, C., Cucchi, M. (2023): ERA5 post-processed daily-statistics on pressure levels from 1940 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS), DOI: 10.24381/cds.4991cf48 (Accessed on DD-MMM-YYYY)

That data citation says "pressure levels" on the single-levels page, while its DOI and its
catalogue-entry citation are for single levels. It looks like an error on the page. Someone should
decide which wording the project uses, and it should not be quietly corrected.

## Part 2: licence version

The licence pop-up was opened on each of the three remaining datasets, the same way as for ERA5-Land
on 2026-09-19. All three are **observed** and all three are identical:

- The text reads "This dataset is released for use under the CC-BY licence."
- It links to https://creativecommons.org/licenses/by/4.0/ and
  https://creativecommons.org/licenses/by/4.0/legalcode.
- Its "Access licence" button points to https://spdx.org/licenses/CC-BY-4.0.

| Dataset | Version linked | Read |
|---|---|---|
| reanalysis-era5-single-levels | CC BY 4.0 | 22:28 PDT, observed |
| derived-era5-land-daily-statistics | CC BY 4.0 | 22:29 PDT, observed |
| derived-era5-single-levels-daily-statistics | CC BY 4.0 | 22:29 PDT, observed |

ERA5-Land's pop-up was re-read tonight and is unchanged. CC BY 4.0 is now observed on all four
datasets, not inferred for three.

## Part 3: grid point positions

### 4. Copernicus, both ERA5-Land datasets

The grid is stated. Where its points sit is **not found**.

- Both overview tables give the grid as "Regular latitude-longitude grid" and the horizontal
  resolution as "0.1° x 0.1°; Native resolution is 9 km." Observed at 22:30 PDT on
  reanalysis-era5-land and at 22:32 PDT on derived-era5-land-daily-statistics.
- ECMWF's ERA5-Land documentation, at
  https://confluence.ecmwf.int/display/CKB/ERA5-Land%3A+data+documentation, read 22:31 PDT, says:
  "Currently, the data can only be downloaded on a regular latitude/longitude grid of 0.1°x0.1° via
  the CDS catalogue."
- The same page gives the native grid: "The ERA5-Land HRES dataset has been produced at a resolution
  of 9 km, (~0.08°) and in a (octahedral) reduced Gaussian grid (represented as TCo1279)." So the
  0.1° grid is itself an interpolation from the native grid.
- Neither page says whether the 0.1° points sit at multiples of 0.1° or half a step off.

### 5. Open-Meteo, ERA5-Land

Resolution only. Point positions **not found**.

- Source: https://open-meteo.com/en/docs/historical-weather-api, read 22:32 PDT.
- Its data table lists ERA5-Land at "0.1° (~11 km)", hourly, 1950 to present.
- It does not say where its grid points sit. It does not say whether it keeps the Copernicus 0.1°
  grid or regrids.

Two statements on that page matter more for D46 than the grid itself:

- The cell_selection parameter defaults to land. The page says: "The default land finds a suitable
  grid-cell on land with similar elevation to the requested coordinates using a 90-meter digital
  elevation model. sea prefers grid-cells on sea. nearest selects the nearest possible grid-cell."
- By default the API also applies statistical downscaling to a 90-metre elevation. The page says:
  "If &elevation=nan is specified, downscaling will be disabled and the API uses the average
  grid-cell height."

So unless a request sets cell_selection=nearest and elevation=nan, the value Open-Meteo returns is
neither the nearest grid point's value nor an unmodified ERA5-Land value.

The page also says the response's latitude and longitude are the "WGS84 of the center of the weather
grid-cell which was used to generate this forecast." A single request would therefore show where
Open-Meteo's points sit. None was made, because this dispatch was read-only pages.

### 6. Summary

Neither source states where its grid points sit. Nothing here infers it.

## What a release must carry

- **Accumulated variables in the daily statistics.** The ERA5-Land daily-statistics page says: "Note
  that the accumulated variables are omitted (e.g. total precipitation, runoff, etc...)."
  Precipitation cannot come from that dataset. The ERA5 single-levels daily-statistics page instead
  offers "The daily sum" for accumulated variables.
- **Daily statistics are computed at request time.** Both daily-statistics pages say the daily
  aggregation "is calculated during the retrieval process and is not part of a permanently archived
  dataset." They also say "The input data is the hourly ERA5-land data available when the daily
  statistics are requested, therefore users should be aware of the difference between ERA5-Land and
  ERA5-Land-T." The single-levels page says the same with ERA5 and ERA5T. A redo under the business
  account can therefore differ from a test-account pull covering recent dates. The release should
  record the request date with every pull.
- **The UTC day boundary is a request option.** Both daily-statistics pages say: "no shift means the
  statistic is computed from UTC+00:00". This is one of D24's open verify-first items, and it should be
  pinned in every request.
- **Area extraction changed on 25 February 2026.** ECMWF's article "Software upgrade for geographical
  area extraction from data on regular lat-lon grids" (last modified 28 January 2026), at
  https://confluence.ecmwf.int/spaces/CKB/pages/621027006, read 22:31 PDT, says that before 25/02/26
  an area request "triggered an interpolation onto a new grid whose south west corner is that given
  in the user supplied area". The store now crops, and output points "may change, shifting by at most
  one grid length." Any CDS output from before that date may sit on shifted points, depending on its
  area. The release should not mix pre- and post-change outputs without checking.
- **Open-Meteo's attribution text is stale.** Open-Meteo cites ERA5-Land as "from 2001 to present"
  and uses "information 2022". Neither matches the store's current wording, so the store's text in
  Part 1 should be the release's source of truth.
- **Open-Meteo's footnote does not match D19's variable list.** Open-Meteo documents ERA5-Seamless as
  "merging temperature and humidity from ERA5-Land with wind and solar radiation from ERA5". D19
  describes the product as ERA5-Land for temperature and soil, and ERA5 for precipitation. The page
  does not say where soil or precipitation come from. The equivalence test should check this, not
  assume it.
- **Open-Meteo's usage terms were not read.** The API page shows a "Usage licence" choice of
  Non-Commercial, Commercial or Self-Hosted. Its licence and terms pages were not opened, and D24's
  paid-plan fallback depends on them.

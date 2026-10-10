"""Attribution names exactly the sources each output read (planner, 2026-10-10; D53, D61)."""

import pytest

from forager_forecast import pilot_output as po

GBIF = "GBIF.org (6 October 2026) GBIF Occurrence Download https://doi.org/10.15468/dl.8jxmeb"


def test_calendar_cites_the_gbif_download_and_nothing_else():
    text, details = po.attribution({"gbif_download"})
    assert GBIF in text
    assert "Copernicus" not in text and "Open-Meteo" not in text
    assert "Copernicus" not in " ".join(details) and "Open-Meteo" not in " ".join(details)
    assert any("10.15468/dl.8jxmeb" in d for d in details)


def test_full_cites_gbif_and_the_two_daily_statistics_products_read():
    accessed = {"era5_land_daily": "10-Oct-2026", "era5_daily_sum": "10-Oct-2026"}
    text, details = po.attribution({"gbif_download", "era5_land_daily", "era5_daily_sum"}, accessed)
    assert GBIF in text
    assert po.COPERNICUS_DAILY in text
    assert "Open-Meteo" not in text + " ".join(details)
    joined = " ".join(details)
    assert "10.24381/cds.e9c9c792" in joined and "10.24381/cds.4991cf48" in joined
    # D53: "single levels" where the page reads "pressure levels"; the hourly datasets not read.
    assert "pressure levels" not in joined
    assert "10.24381/cds.e2161bac" not in joined and "10.24381/cds.adbb2d47" not in joined
    assert "DD-MMM-YYYY" not in joined and "(Accessed on 10-Oct-2026)" in joined


def test_hourly_era5_land_route_is_cited_only_when_read():
    accessed = {k: "10-Oct-2026" for k in ("era5_land_hourly", "era5_daily_sum")}
    _text, details = po.attribution(
        {"gbif_download", "era5_land_hourly", "era5_daily_sum"}, accessed
    )
    joined = " ".join(details)
    assert "10.24381/cds.e2161bac" in joined and "10.24381/cds.e9c9c792" not in joined


def test_open_meteo_is_credited_only_when_read():
    text, _ = po.attribution({"gbif_download", "open_meteo"})
    assert "Open-Meteo" in text


def test_a_copernicus_source_without_an_access_date_is_refused():
    with pytest.raises(ValueError, match="access date"):
        po.attribution({"gbif_download", "era5_daily_sum"})


def test_an_unknown_source_is_refused():
    with pytest.raises(ValueError, match="unknown"):
        po.attribution({"gbif_download", "daymet"})

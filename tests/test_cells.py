from datetime import date

import pytest

from forager_forecast.cells import Cell, IsoWeek, cell_for, iso_week_of


def test_a_grid_point_maps_to_the_cell_centred_on_it():
    assert cell_for(47.0, -123.0) == Cell(lat_tenths=470, lon_tenths=-1230)
    assert cell_for(47.0, -123.0).center_latitude == 47.0
    assert cell_for(47.0, -123.0).center_longitude == -123.0
    assert cell_for(47.0, -123.0).id == "470_-1230"


@pytest.mark.parametrize(
    ("latitude", "longitude", "expected"),
    [
        # Observed from Open-Meteo's archive on 2026-09-18 (models=era5_seamless): the grid
        # point each requested coordinate came back from.
        (47.04, -123.04, Cell(470, -1230)),
        (47.049, -123.049, Cell(470, -1230)),
        (47.05, -123.05, Cell(471, -1231)),
        (47.051, -123.051, Cell(471, -1231)),
        (47.06, -123.06, Cell(471, -1231)),
        (47.14, -122.96, Cell(471, -1230)),
        (46.96, -123.04, Cell(470, -1230)),
    ],
)
def test_nearest_grid_point_with_halves_away_from_zero_matches_the_archive(
    latitude, longitude, expected
):
    assert cell_for(latitude, longitude) == expected


def test_halves_are_not_rounded_to_even():
    # round(47.05, 1) in Python is 47.0 (float representation) and round(0.25, 1) is 0.2
    # (half to even). Neither is the rule the archive applies.
    assert cell_for(47.05, 0.25) == Cell(471, 3)
    assert cell_for(-47.05, -0.25) == Cell(-471, -3)


@pytest.mark.parametrize(("latitude", "longitude"), [(90.1, 0.0), (-90.1, 0.0), (0.0, 180.1)])
def test_out_of_range_coordinates_are_refused(latitude, longitude):
    with pytest.raises(ValueError):
        cell_for(latitude, longitude)


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        # ISO 8601 edge cases: the first days of a year can belong to the previous ISO year
        # and the last days to the next.
        (date(2021, 1, 1), IsoWeek(2020, 53)),
        (date(2021, 1, 4), IsoWeek(2021, 1)),
        (date(2024, 12, 30), IsoWeek(2025, 1)),
        (date(2024, 9, 1), IsoWeek(2024, 35)),
        (date(2024, 9, 2), IsoWeek(2024, 36)),
    ],
)
def test_iso_week_follows_the_standard(day, expected):
    assert iso_week_of(day) == expected


def test_iso_week_id_and_monday():
    week = iso_week_of(date(2024, 9, 5))
    assert week.id == "2024-W36"
    assert week.monday() == date(2024, 9, 2)
    assert iso_week_of(week.monday()) == week

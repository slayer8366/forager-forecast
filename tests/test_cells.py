from datetime import date

import pytest

from forager_forecast.cells import (
    Cell,
    IsoWeek,
    QuarterCell,
    cell_for,
    iso_week_of,
    quarter_cell_for,
)


def test_a_grid_point_maps_to_the_cell_centred_on_it():
    assert cell_for(47.0, -123.0) == Cell(lat_tenths=470, lon_tenths=-1230)
    assert cell_for(47.0, -123.0).center_latitude == 47.0
    assert cell_for(47.0, -123.0).center_longitude == -123.0
    assert cell_for(47.0, -123.0).id == "470_-1230"


@pytest.mark.parametrize(
    ("latitude", "longitude", "expected"),
    [
        # Observed from Open-Meteo's archive on 2026-09-18 (models=era5_seamless): the grid
        # point each requested coordinate came back from. Every one is off a half.
        (47.04, -123.04, Cell(470, -1230)),
        (47.049, -123.049, Cell(470, -1230)),
        (47.051, -123.051, Cell(471, -1231)),
        (47.06, -123.06, Cell(471, -1231)),
        (47.14, -122.96, Cell(471, -1230)),
        (46.96, -123.04, Cell(470, -1230)),
    ],
)
def test_nearest_grid_point_matches_the_archive_off_the_halves(latitude, longitude, expected):
    assert cell_for(latitude, longitude) == expected


@pytest.mark.parametrize(
    ("latitude", "longitude", "expected"),
    [
        # D63: an exact tie goes toward +infinity on each axis, as both sources did at every
        # probed exact tie (grid positions part 2 report): north on latitude, east on longitude.
        (47.25, -123.22, Cell(473, -1232)),
        (47.22, -123.25, Cell(472, -1232)),
        (47.25, -123.25, Cell(473, -1232)),
        (49.25, -120.75, Cell(493, -1207)),
        # Not probed at a source, but the same rule: toward +infinity is south-to-north and
        # west-to-east on every side of zero.
        (-47.25, 123.25, Cell(-472, 1233)),
        (0.05, -0.05, Cell(1, 0)),
        # D64: a tie is read on the decimal value GBIF reports, not on the binary double.
        # Open-Meteo returned -123.1 for this point on 2026-09-18; D64 rules -123.0.
        (47.05, -123.05, Cell(471, -1230)),
    ],
)
def test_exact_ties_go_toward_plus_infinity_on_both_axes(latitude, longitude, expected):
    assert cell_for(latitude, longitude) == expected


def test_halves_are_not_rounded_to_even():
    # round(47.05, 1) in Python is 47.0 (float representation) and round(0.25, 1) is 0.2
    # (half to even). Neither is the rule D63 sets.
    assert cell_for(47.05, 0.25) == Cell(471, 3)
    assert cell_for(-47.05, -0.25) == Cell(-470, -2)


@pytest.mark.parametrize(
    ("latitude", "longitude", "center"),
    [
        # Observed from Open-Meteo models=era5 (0.25 degree) on 2026-09-23, grid positions part 2.
        (47.1, -123.1, (47.0, -123.0)),
        (47.125, -123.1, (47.25, -123.0)),
        (47.375, -123.1, (47.5, -123.0)),
        (47.1, -123.125, (47.0, -123.0)),
        (47.1, -123.375, (47.0, -123.25)),
        (47.125, -123.125, (47.25, -123.0)),
        (48.625, -120.875, (48.75, -120.75)),
        # Same rule on the other sides of zero.
        (-47.125, 123.125, (-47.0, 123.25)),
    ],
)
def test_quarter_degree_cell_is_the_nearest_era5_point_with_ties_toward_plus_infinity(
    latitude, longitude, center
):
    cell = quarter_cell_for(latitude, longitude)
    assert (cell.center_latitude, cell.center_longitude) == center


def test_quarter_degree_cell_is_named_in_quarters():
    assert quarter_cell_for(47.25, -123.0) == QuarterCell(lat_quarters=189, lon_quarters=-492)
    assert quarter_cell_for(47.25, -123.0).id == "q189_-492"


@pytest.mark.parametrize(("latitude", "longitude"), [(90.1, 0.0), (-90.1, 0.0), (0.0, 180.1)])
def test_quarter_degree_cell_refuses_out_of_range_coordinates(latitude, longitude):
    with pytest.raises(ValueError):
        quarter_cell_for(latitude, longitude)


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

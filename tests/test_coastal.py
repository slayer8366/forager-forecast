"""coastal.land_point: own point first, else the nearest land neighbour, ties north then east."""

from forager_forecast.coastal import land_point


def test_own_point_when_it_has_values():
    assert land_point((470, -1230), {(470, -1230), (470, -1229)}) == ((470, -1230), False)


def test_nearest_neighbour_by_great_circle_distance():
    # At 47 N a 0.1° step east or west is about 7.6 km, north or south about 11.1 km, so the
    # east neighbour beats the north one.
    assert land_point((470, -1230), {(471, -1230), (470, -1229)}) == ((470, -1229), True)
    # A diagonal (about 13.5 km) loses to the north neighbour.
    assert land_point((470, -1230), {(471, -1229), (471, -1230)}) == ((471, -1230), True)


def test_tie_goes_east_then_north():
    # East and west are exactly as far: east wins (toward +infinity, as D63).
    assert land_point((470, -1230), {(470, -1231), (470, -1229)}) == ((470, -1229), True)


def test_no_land_neighbour_means_no_point():
    assert land_point((470, -1230), {(472, -1230)}) is None

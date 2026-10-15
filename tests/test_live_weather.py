"""Live weather for the PNW pilot's scoring (src/forager_forecast/live_weather.py). No network."""

from datetime import UTC, date, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from forager_forecast import live_weather as lw
from forager_forecast.cells import Cell, IsoWeek
from forager_forecast.open_meteo import archive_request_url
from forager_forecast.t1_design import BOXES


def test_pnw_box_cells_are_every_tenth_degree_centre_inside_the_box():
    pnw = next(b for b in BOXES if b.name == "pnw")
    cells = lw.box_cells(pnw)
    # 42.0 to 49.5 N is 76 centres, 125.0 to 121.0 W is 41 centres, both edges inclusive.
    assert len(cells) == 76 * 41
    assert len(set(cells)) == len(cells)
    assert Cell(420, -1250) in cells and Cell(495, -1210) in cells
    assert Cell(419, -1250) not in cells and Cell(420, -1209) not in cells
    assert all(pnw.contains(c.center_latitude, c.center_longitude) for c in cells)


def test_window_span_ends_the_day_before_the_scored_monday_and_covers_the_longest_window():
    start, end = lw.window_span(IsoWeek(2026, 41))
    assert end == date(2026, 10, 4)  # Monday 2026-10-05 is the scored date
    assert (end - start).days + 1 == 90
    assert start == date(2026, 7, 7)


def test_multi_location_url_pins_every_parameter_the_single_cell_request_pins():
    cells = [Cell(470, -1230), Cell(455, -1225), Cell(420, -1250)]
    url = lw.multi_archive_url(cells, date(2026, 7, 7), date(2026, 10, 4))
    q = parse_qs(urlparse(url).query)
    single = parse_qs(
        urlparse(archive_request_url(cells[0], date(2026, 7, 7), date(2026, 10, 4))).query
    )
    assert url.startswith(lw.ARCHIVE_URL + "?")
    assert q["latitude"] == ["47.0,45.5,42.0"]
    assert q["longitude"] == ["-123.0,-122.5,-125.0"]
    # One elevation per location, or Open-Meteo refuses the request (seen live 2026-10-10).
    assert q["elevation"] == ["nan,nan,nan"]
    for key in (
        "models",
        "cell_selection",
        "timezone",
        "daily",
        "hourly",
        "start_date",
        "end_date",
    ):
        assert q[key] == single[key], key
    assert q["models"] == ["era5_seamless"]
    assert q["cell_selection"] == ["nearest"]


def test_request_cost_is_locations_times_the_pricing_page_weight():
    # 90 days and 4 variables: max(1, 90/14) per location.
    assert lw.request_cost(50, date(2026, 7, 7), date(2026, 10, 4)) == pytest.approx(50 * 90 / 14)
    assert lw.request_cost(1, date(2026, 10, 1), date(2026, 10, 4)) == pytest.approx(1.0)


def _at(minutes: float) -> datetime:
    return datetime(2026, 10, 10, 20, 0, tzinfo=UTC) + timedelta(minutes=minutes)


def test_budget_waits_until_the_minute_window_has_room():
    budget = lw.Budget(per_minute=400, per_hour=4000, per_day=8000)
    ledger = [(_at(0), 300.0)]
    assert budget.wait_seconds(ledger, _at(0.5), 300.0) == pytest.approx(30.0)
    assert budget.wait_seconds(ledger, _at(1.01), 300.0) == 0.0


def test_budget_waits_for_the_hour_window():
    budget = lw.Budget(per_minute=400, per_hour=4000, per_day=8000)
    ledger = [(_at(i * 2), 320.0) for i in range(12)]  # 3,840 in 22 minutes
    wait = budget.wait_seconds(ledger, _at(23), 320.0)
    assert wait == pytest.approx(37 * 60)  # until the first entry (minute 0) is an hour old


def test_budget_waits_for_the_utc_day_to_turn():
    budget = lw.Budget(per_minute=400, per_hour=4000, per_day=8000)
    day = datetime(2026, 10, 10, 1, 0, tzinfo=UTC)
    ledger = [(day + timedelta(minutes=50 * i), 320.0) for i in range(24)]  # last at 20:10
    now = datetime(2026, 10, 10, 23, 30, tzinfo=UTC)
    assert sum(c for _t, c in ledger) == 7680
    assert budget.wait_seconds(ledger, now, 330.0) == pytest.approx(30 * 60)


def test_budget_refuses_a_request_larger_than_a_window():
    budget = lw.Budget(per_minute=400, per_hour=4000, per_day=8000)
    with pytest.raises(ValueError, match="per_minute"):
        budget.wait_seconds([], _at(0), 401.0)


def test_rate_limit_answers_are_recognised_as_stop_conditions():
    assert lw.is_rate_limited(429, {"error": True, "reason": "Minutely API request limit exceeded"})
    assert lw.is_rate_limited(400, {"error": True, "reason": "Daily API request limit exceeded."})
    assert not lw.is_rate_limited(200, [{"latitude": 47.0}])
    assert not lw.is_rate_limited(400, {"error": True, "reason": "Parameter 'elevation' ..."})


def test_responses_are_matched_to_cells_by_their_echoed_grid_point():
    cells = [Cell(470, -1230), Cell(455, -1225)]
    body = [
        {"latitude": 47.0, "longitude": -123.0, "daily": {}},
        {"latitude": 45.5, "longitude": -122.5, "location_id": 1, "daily": {}},
    ]
    assert lw.split_by_cell(cells, body) == {cells[0]: body[0], cells[1]: body[1]}
    # A single-location request comes back as one object, not a list.
    assert lw.split_by_cell(cells[:1], body[0]) == {cells[0]: body[0]}


def test_a_response_on_another_grid_point_is_refused_not_reassigned():
    cells = [Cell(470, -1230)]
    with pytest.raises(lw.WrongCell, match="470_-1230"):
        lw.split_by_cell(cells, [{"latitude": 47.1, "longitude": -123.0}])

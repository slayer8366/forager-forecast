"""scripts/pnw_equivalence.py: the span shape (review S5), the restated bounds (review B2, RECORD
-818) and the request's pins (D19, D25). Synthetic bodies only; no request is made."""

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import pnw_equivalence as eq  # noqa: E402

from forager_forecast.cells import Cell  # noqa: E402


def body(days: int = 8) -> dict:
    hours = days * 24
    return {
        "daily": {
            "time": [f"2019-01-{d + 1:02d}" for d in range(days)],
            "temperature_2m_mean": [float(d) for d in range(days)],
            "precipitation_sum": [0.1 * d for d in range(days)],
        },
        "hourly": {
            "time": [f"2019-01-{h // 24 + 1:02d}T{h % 24:02d}:00" for h in range(hours)],
            "temperature_2m": [0.0] * hours,
            "soil_temperature_0_to_7cm": [float(h // 24) for h in range(hours)],
            "soil_moisture_0_to_7cm": [0.3] * hours,
            "precipitation": [0.1] * hours,
        },
    }


def test_an_eight_day_body_gives_seven_days_and_all_192_hours():
    days, hours, stamps = eq.split_span(body())
    assert len(days["temperature"]) == 7 and len(days["precipitation"]) == 7
    assert days["soil_temperature"] == pytest.approx(np.arange(7.0))
    assert len(hours["precipitation"]) == 192 and len(stamps) == 192


def test_any_other_span_is_refused():
    with pytest.raises(ValueError):
        eq.split_span(body(7))


def test_bounds_are_the_restated_ones():
    assert eq.TOL == pytest.approx(
        {"temperature": 0.075, "precipitation": 1.25, "soil_temperature": 0.075,
         "soil_moisture": 0.001}
    )  # fmt: skip
    assert eq.HOURLY_TOL == pytest.approx({"t2m": 0.075, "stl1": 0.075, "swvl1": 0.001})


def test_request_keeps_the_pins_and_asks_eight_days_of_hours():
    url = eq.request_url(Cell(470, -1230), date(2019, 1, 1))
    for pin in ("models=era5_seamless", "elevation=nan", "cell_selection=nearest", "timezone=UTC"):
        assert pin in url
    assert "start_date=2019-01-01" in url and "end_date=2019-01-08" in url
    assert "hourly=temperature_2m%2Csoil_temperature_0_to_7cm%2Csoil_moisture_0_to_7cm%2C" in url

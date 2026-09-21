"""One test per filter step, the pipeline's counting, and the promise that the source is untouched.

The fixture rows are synthetic and shaped like GBIF DWCA occurrence.txt rows: the field names are
Darwin Core, the values are text. The obscured row copies the informationWithheld wording seen on
GBIF record 5006980885 on 2026-09-18.
"""

import copy
from types import MappingProxyType

import pytest

from forager_forecast.records import filters as f

OBSCURED_TEXT = "Coordinate uncertainty increased to 26775m at the request of the observer"


def row(**overrides: str) -> dict[str, str]:
    base = {
        "gbifID": "1",
        "recordedBy": "observer_a",
        "decimalLatitude": "47.05",
        "decimalLongitude": "-123.05",
        "coordinateUncertaintyInMeters": "8",
        "informationWithheld": "",
        "dataGeneralizations": "",
        "eventDate": "2024-09-14T10:15:00",
        "year": "2024",
        "genusKey": "9623860",
    }
    base.update(overrides)
    return base


# Step 1: user_obscured


def test_information_withheld_marks_a_record_obscured():
    assert f.is_user_obscured(row(informationWithheld=OBSCURED_TEXT))


def test_data_generalizations_marks_a_record_obscured():
    assert f.is_user_obscured(row(dataGeneralizations="coordinates rounded to 0.1 degree"))


def test_open_record_is_not_obscured():
    assert not f.is_user_obscured(row())
    assert not f.is_user_obscured(row(informationWithheld="   "))


# Step 2: coordinate_uncertainty (R6)


@pytest.mark.parametrize(
    ("uncertainty", "dropped"),
    [
        ("8", False),
        ("250", False),
        ("250.0", False),
        ("250.5", True),
        ("251", True),
        ("26775", True),
        ("", True),
        ("unknown", True),
        ("nan", True),
    ],
)
def test_uncertainty_above_250_or_missing_is_dropped(uncertainty: str, dropped: bool):
    assert f.exceeds_r6_uncertainty(row(coordinateUncertaintyInMeters=uncertainty)) is dropped


def test_r6_threshold_is_250_m():
    assert f.R6_MAX_COORDINATE_UNCERTAINTY_M == 250


# Step 3: default_first_of_month_date


@pytest.mark.parametrize(
    ("event_date", "dropped"),
    [
        ("2024-09-01", True),
        ("2024-09-01T00:00:00", True),
        ("2024-09-01T00:00:00Z", True),
        ("2024-09-01T00:00:00-08:00", True),
        ("2024-09-01T13:24:27", False),
        ("2024-09-14", False),
        ("2024-09-14T00:00:00", False),
        ("2024-09", False),
        ("2024-09-01/2024-09-30", False),
        ("", False),
    ],
)
def test_first_of_month_without_a_real_time_is_dropped(event_date: str, dropped: bool):
    assert f.is_default_first_of_month_date(row(eventDate=event_date)) is dropped


# Step 4: duplicate_observer_cell_day


def test_weather_cell_is_the_0_1_degree_floor():
    assert f.WEATHER_CELL_DEGREES == 0.1
    assert f.weather_cell(47.05, -123.05) == (470, -1231)
    assert f.weather_cell(47.8, -122.28) == (478, -1223)
    assert f.weather_cell(47.09999, -123.00001) == (470, -1231)
    assert f.weather_cell(47.1, -123.0) == (471, -1230)


def test_second_record_of_same_observer_cell_and_day_is_dropped():
    step = f.DuplicateObserverCellDay()
    first = row(gbifID="1", eventDate="2024-09-14T10:15:00")
    second = row(gbifID="2", eventDate="2024-09-14T16:40:00", decimalLatitude="47.09")
    assert step(first) is False
    assert step(second) is True


@pytest.mark.parametrize(
    "change",
    [
        {"recordedBy": "observer_b"},
        {"decimalLatitude": "47.15"},
        {"decimalLongitude": "-122.95"},
        {"eventDate": "2024-09-15T10:15:00"},
    ],
)
def test_different_observer_cell_or_day_is_kept(change: dict[str, str]):
    step = f.DuplicateObserverCellDay()
    assert step(row(gbifID="1")) is False
    assert step(row(gbifID="2", **change)) is False


def test_default_steps_are_the_dispatch_order_with_fresh_state():
    names = [step.name for step in f.default_steps()]
    assert names == [
        "user_obscured",
        "coordinate_uncertainty",
        "default_first_of_month_date",
        "duplicate_observer_cell_day",
    ]
    a = f.default_steps()[3].drops
    b = f.default_steps()[3].drops
    assert a(row()) is False
    assert b(row()) is False, "a second pipeline must not remember the first pipeline's records"


# The pipeline


def fixture_rows() -> list[dict[str, str]]:
    return [
        row(gbifID="1"),
        row(gbifID="2", informationWithheld=OBSCURED_TEXT, coordinateUncertaintyInMeters="26775"),
        row(gbifID="3", coordinateUncertaintyInMeters="300"),
        row(gbifID="4", coordinateUncertaintyInMeters=""),
        row(gbifID="5", eventDate="2024-09-01"),
        row(gbifID="6", eventDate="2024-09-14T18:00:00"),
        row(gbifID="7", recordedBy="observer_b"),
    ]


def test_pipeline_counts_every_step_and_the_counts_chain():
    pipeline = f.Pipeline()
    kept = list(pipeline.run(fixture_rows()))
    assert [r["gbifID"] for r in kept] == ["1", "7"]
    assert pipeline.source_count == 7
    by_name = {c.step: c for c in pipeline.counts}
    assert (by_name["user_obscured"].before, by_name["user_obscured"].dropped) == (7, 1)
    assert (
        by_name["coordinate_uncertainty"].before,
        by_name["coordinate_uncertainty"].dropped,
    ) == (
        6,
        2,
    )
    assert (
        by_name["default_first_of_month_date"].before,
        by_name["default_first_of_month_date"].dropped,
    ) == (4, 1)
    assert (
        by_name["duplicate_observer_cell_day"].before,
        by_name["duplicate_observer_cell_day"].dropped,
    ) == (3, 1)
    for earlier, later in zip(pipeline.counts[:-1], pipeline.counts[1:], strict=True):
        assert later.before == earlier.after
    assert pipeline.counts[-1].after == len(kept)


def test_a_record_is_counted_under_the_first_step_that_drops_it():
    obscured_and_far = row(
        informationWithheld=OBSCURED_TEXT,
        coordinateUncertaintyInMeters="26775",
        eventDate="2024-09-01",
    )
    pipeline = f.Pipeline()
    assert list(pipeline.run([obscured_and_far])) == []
    assert [c.dropped for c in pipeline.counts] == [1, 0, 0, 0]


def test_source_records_are_never_modified():
    rows = fixture_rows()
    before = copy.deepcopy(rows)
    frozen = [MappingProxyType(r) for r in rows]
    kept = list(f.Pipeline().run(frozen))
    assert rows == before
    assert len(kept) == 2
    assert all(any(k is fr for fr in frozen) for k in kept), "survivors are the input objects"


def test_on_pass_sees_source_then_each_cleared_stage():
    seen: list[tuple[str, str]] = []
    pipeline = f.Pipeline(on_pass=lambda stage, r: seen.append((stage, r["gbifID"])))
    list(pipeline.run([row(gbifID="1"), row(gbifID="3", coordinateUncertaintyInMeters="300")]))
    assert seen == [
        ("source", "1"),
        ("user_obscured", "1"),
        ("coordinate_uncertainty", "1"),
        ("default_first_of_month_date", "1"),
        ("duplicate_observer_cell_day", "1"),
        ("source", "3"),
        ("user_obscured", "3"),
    ]


def test_repeated_step_names_are_refused():
    with pytest.raises(ValueError):
        f.Pipeline(steps=[f.FilterStep("x", lambda r: False), f.FilterStep("x", lambda r: False)])


def test_read_occurrence_table_streams_tab_rows_without_quoting(tmp_path):
    table = tmp_path / "occurrence.txt"
    table.write_text(
        'gbifID\trecordedBy\toccurrenceRemarks\n1\tsomeone\tsaid "very soggy"\n2\telse\t\n',
        encoding="utf-8",
    )
    rows = list(f.read_occurrence_table(table))
    assert rows == [
        {"gbifID": "1", "recordedBy": "someone", "occurrenceRemarks": 'said "very soggy"'},
        {"gbifID": "2", "recordedBy": "else", "occurrenceRemarks": ""},
    ]

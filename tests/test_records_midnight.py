"""D28's midnight check, measured (docs/audits/2026-10-06-d28-midnight-measure.md, commit 00d23f6).

Per dataset: midnight (00:00:00 as written) on the 1st against midnight on any day; expected day-1
share 12/365.2425; at least 300 midnight records; one-sided exact binomial at a family level of
0.01, Bonferroni over the datasets tested; "clear" also needs the 95% lower end at twice expected.
"""

from collections import Counter
from fractions import Fraction

import pytest

from forager_forecast.records import filters as f
from forager_forecast.records import midnight as mn
from forager_forecast.records.occurrence import OccurrenceLoader

DATASET_A = "aaaaaaaa-0000-0000-0000-000000000001"
DATASET_B = "bbbbbbbb-0000-0000-0000-000000000002"


def row(gbif_id: int, event_date: str, dataset: str = DATASET_A, **overrides: str) -> dict:
    base = {
        "gbifID": str(gbif_id),
        "acceptedTaxonKey": str(1000 + gbif_id),
        "genusKey": "9623860",
        "decimalLatitude": "47.02",
        "decimalLongitude": "-123.02",
        "coordinateUncertaintyInMeters": "8",
        "eventDate": event_date,
        "license": "CC_BY_NC_4_0",
        "datasetKey": dataset,
        "recordedBy": "observer_a",
        "informationWithheld": "",
        "dataGeneralizations": "",
    }
    base.update(overrides)
    return base


def load(rows):
    return list(OccurrenceLoader().load(rows))


@pytest.mark.parametrize(
    ("event_date", "midnight"),
    [
        ("2021-06-01T00:00:00", True),
        ("2021-06-01T00:00", True),
        ("2021-06-14T00:00:00Z", True),
        ("2021-06-14T00:00:00-07:00", True),  # as written, not converted
        ("2021-06-14T00:00:00.500", False),
        ("2021-06-14T00:00:01", False),
        ("2021-06-14", False),  # date-only is not midnight
    ],
)
def test_midnight_is_the_clock_half_of_the_default_date_rule(event_date, midnight):
    (record,) = load([row(1, event_date)])
    assert mn.is_midnight(record) is midnight
    first = load([row(2, "2021-06-01" + event_date[10:])])[0]
    if first.event_time is not None:
        assert f.is_default_date(first) is mn.is_midnight(first)


def test_the_table_counts_timed_records_and_midnight_by_day_at_the_source_stage():
    rows = [
        row(1, "2021-06-01T00:00:00"),
        row(2, "2021-07-01T00:00:00", coordinateUncertaintyInMeters="5000"),
        row(3, "2021-07-15T00:00:00"),
        row(4, "2021-07-01T09:30:00"),
        row(5, "2021-07-02T09:30:00"),
        row(6, "2021-07-01"),  # date-only: not a timed record
        row(7, "2021-08-31T00:00:00", dataset=DATASET_B),
    ]
    table = mn.MidnightTable()
    f.Pipeline(f.r6_audit_steps(), on_pass=table.add).run(load(rows))
    a, b = table.datasets()[DATASET_A], table.datasets()[DATASET_B]
    assert (a.timed, a.m, a.k) == (5, 3, 2)
    assert dict(a.midnight_by_day) == {1: 2, 15: 1}
    assert (a.timed_not_midnight, a.timed_not_midnight_on_first) == (2, 1)
    assert (b.timed, b.m, b.k) == (1, 1, 0)


def test_reaching_the_date_step_matches_a_real_pipeline_run_for_both_lists():
    rows = [
        row(1, "2021-06-01T00:00:00"),  # reaches the date step in both lists
        row(2, "2021-06-01T00:00:00", coordinateUncertaintyInMeters="500"),  # T1 only
        row(3, "2021-06-01T00:00:00", decimalLatitude="30.0"),  # R6 only (outside T1 boxes)
        row(4, "2021-06-01T00:00:00", informationWithheld="obscured"),  # neither
        row(5, "2021-06-02T00:00:00"),  # not the 1st: not counted
    ]
    lists = {"t1": f.t1_steps(), "r6": f.r6_audit_steps()}
    table = mn.MidnightTable(lists)
    for record in load(rows):
        table.add(f.SOURCE_STAGE, record)
    reached = table.datasets()[DATASET_A].first_midnight_reaching_date_step
    for name, steps in lists.items():
        before_date = steps.filters[f.date_step_position(steps) - 1].name
        seen = Counter()

        def sink(stage, record, seen=seen, before_date=before_date):
            if stage == before_date and record.event_date.day == 1 and mn.is_midnight(record):
                seen["n"] += 1

        f.Pipeline(steps, on_pass=sink).run(load(rows))
        assert reached[name] == seen["n"], name
    assert dict(reached) == {"t1": 2, "r6": 2}


def test_expected_share_is_the_calendar_share_of_the_1st():
    assert mn.EXPECTED_SHARE == 12 / 365.2425
    assert mn.MIN_MIDNIGHT == 300


def _ds(key, m, k, timed=None, other_first=0, other=0):
    d = mn.DatasetMidnight(key)
    d.midnight_by_day[1] = k
    d.midnight_by_day[15] = m - k
    d.timed = timed if timed is not None else m + other
    d.timed_not_midnight = other
    d.timed_not_midnight_on_first = other_first
    return d


def _exact_tail(k, n, p):
    p = Fraction(p)
    from math import comb

    return float(sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1)))


def test_verdicts_follow_the_measure_and_bonferroni_counts_only_tested_datasets():
    rows = [
        _ds("clear", 300, 40),  # share 0.133; lower end well above 2 x 0.0329
        _ds("small", 300, 21),  # significant at 0.01/4, lower end under 0.0657
        _ds("common", 300, 10),  # about expected
        _ds("few", 299, 299),  # under 300: never tested, and not in the split
        _ds("deficit", 1000, 0),  # one-sided: a deficit is "common", not special
    ]
    out = {a.dataset_key: a for a in mn.assess_midnight(rows)}
    assert out["clear"].verdict == mn.CLEAR
    assert out["small"].verdict == mn.SMALL
    assert out["common"].verdict == mn.COMMON
    assert out["few"].verdict == mn.TOO_FEW and out["few"].level_each is None
    assert out["deficit"].verdict == mn.COMMON
    assert out["clear"].level_each == pytest.approx(0.01 / 4)
    small = out["small"]
    assert small.p_value == pytest.approx(_exact_tail(21, 300, 12 / 365.2425), rel=1e-9)
    assert small.p_value < 0.01 / 4 and small.interval[0] < 2 * mn.EXPECTED_SHARE


def test_the_split_decides_a_borderline_dataset():
    # 19 of 300: p about 0.0054, significant at 0.01 alone, not at 0.01 / 2.
    alone = mn.assess_midnight([_ds("x", 300, 19)])[0]
    split = mn.assess_midnight([_ds("x", 300, 19), _ds("y", 300, 10)])[0]
    assert alone.level_each == pytest.approx(0.01) and alone.verdict == mn.SMALL
    assert split.level_each == pytest.approx(0.005) and split.verdict == mn.COMMON


def test_shares_beside_the_verdict():
    d = _ds("a", 300, 10, other=700, other_first=35)
    (a,) = mn.assess_midnight([d])
    assert a.any_day_share == pytest.approx(300 / 1000)
    assert a.share_on_first == pytest.approx(10 / 300)
    assert a.ratio_to_expected == pytest.approx((10 / 300) / (12 / 365.2425))
    assert a.ratio_to_one_in_thirty == pytest.approx(1.0)
    assert a.own_calendar_share == pytest.approx(35 / 700)


def test_pooled_row_adds_every_dataset():
    p = mn.pooled([_ds("a", 300, 10, other=5, other_first=1), _ds("b", 20, 2)])
    assert (p.m, p.k, p.timed, p.timed_not_midnight, p.timed_not_midnight_on_first) == (
        320,
        12,
        325,
        5,
        1,
    )


def test_a_list_without_a_date_step_is_refused():
    steps = f.r6_audit_steps()
    no_date = f.Steps(
        filters=tuple(s for s in steps.filters if s.drops not in f.DATE_STEP_RULES),
        duplicate=steps.duplicate,
    )
    with pytest.raises(ValueError):
        mn.MidnightTable({"x": no_date})

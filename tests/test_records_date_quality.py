"""D28: the day-of-month table for date-only records by dataset, its test, and the candidate rules.

The test was fixed before any count was read (docs/audits/2026-10-06-d27-d29-verify-report.md,
section 3, commit ea579c2): reference share 1/30; at least 300 date-only records; a one-sided exact
binomial test at a family level of 0.01, Bonferroni over the datasets tested; "clear excess" also
needs the 95% Clopper-Pearson lower end at 2/30 or more.
"""

import math
from collections import Counter
from fractions import Fraction

import pytest

from forager_forecast.records import date_quality as dq
from forager_forecast.records import filters as f
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


# What a date-only record is, read through the loader


@pytest.mark.parametrize(
    ("event_date", "date_only"),
    [
        ("2021-06-01", True),
        ("2021-06-01/2021-06-01", True),
        ("2021-06-01T00:00:00", False),
        ("2021-06-01T00:00", False),
        ("2021-06-14T10:15:00Z", False),
    ],
)
def test_date_only_means_the_event_date_carries_no_clock_time(event_date, date_only):
    (record,) = load([row(1, event_date)])
    assert dq.is_date_only(record) is date_only


# The table, fed by the pipeline's on_pass at the source stage


def test_the_table_counts_date_only_records_by_dataset_and_day_at_the_source_stage():
    rows = [
        row(1, "2021-06-01"),
        row(2, "2021-07-01"),
        row(3, "2021-07-15"),
        row(4, "2021-07-01T00:00:00"),  # midnight on the 1st with a clock time: not date-only
        row(5, "2021-07-01T09:30:00"),
        row(6, "2021-08-31", dataset=DATASET_B),
        row(7, "2021-08-01", dataset=DATASET_B, coordinateUncertaintyInMeters="5000"),
    ]
    table = dq.DayOfMonthTable()
    f.Pipeline(f.r6_audit_steps(), on_pass=table.add).run(load(rows))
    a, b = table.datasets()[DATASET_A], table.datasets()[DATASET_B]
    assert (a.loaded, a.n, a.k, a.midnight_first_with_clock) == (5, 3, 2, 1)
    assert a.date_only_by_day == Counter({1: 2, 15: 1})
    # The table is the source stage: a record a later step drops is still counted.
    assert (b.loaded, b.n, b.k, b.midnight_first_with_clock) == (2, 2, 1, 0)
    assert b.date_only_by_day == Counter({31: 1, 1: 1})


# The exact binomial test and the exact interval, against independent arithmetic


def exact_tail(k: int, n: int, p: Fraction) -> float:
    return float(sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1)))


@pytest.mark.parametrize("n", [1, 7, 50, 300])
def test_upper_tail_equals_the_exact_sum(n):
    for k in sorted({0, 1, n // 30, n // 10, n // 2, n}):
        expected = exact_tail(k, n, Fraction(1, 30))
        assert dq.binomial_upper_tail(k, n, 1 / 30) == pytest.approx(expected, rel=1e-9, abs=1e-300)


def log_space_tail(k: int, n: int, p: float, terms: int) -> float:
    """P(X >= k) summed term by term in log space, over the first `terms` terms from k."""
    logs = [
        math.lgamma(n + 1)
        - math.lgamma(i + 1)
        - math.lgamma(n - i + 1)
        + i * math.log(p)
        + (n - i) * math.log1p(-p)
        for i in range(k, min(n, k + terms) + 1)
    ]
    top = max(logs)
    return math.exp(top) * sum(math.exp(v - top) for v in logs)


def test_upper_tail_holds_at_the_size_of_a_large_dataset():
    n, k, p = 200_000, 7_000, 1 / 30
    expected = log_space_tail(k, n, p, terms=3000)
    assert dq.binomial_upper_tail(k, n, p) == pytest.approx(expected, rel=1e-7)


def test_clopper_pearson_at_the_ends_has_the_closed_form():
    lo, hi = dq.clopper_pearson(0, 10)
    assert lo == 0.0
    assert hi == pytest.approx(1 - 0.025 ** (1 / 10), rel=1e-9)
    lo, hi = dq.clopper_pearson(10, 10)
    assert lo == pytest.approx(0.025 ** (1 / 10), rel=1e-9)
    assert hi == 1.0


def test_clopper_pearson_lower_end_is_where_the_upper_tail_is_two_and_a_half_percent():
    k, n = 48, 1000
    lo, hi = dq.clopper_pearson(k, n)
    assert log_space_tail(k, n, lo, terms=n) == pytest.approx(0.025, rel=1e-6)
    assert 1 - log_space_tail(k + 1, n, hi, terms=n) == pytest.approx(0.025, rel=1e-6)


# The verdicts, as fixed before any count


def days(key: str, n: int, k: int) -> dq.DatasetDays:
    return dq.DatasetDays(dataset_key=key, loaded=n, date_only_by_day=Counter({1: k, 15: n - k}))


def verdicts(*rows: dq.DatasetDays) -> dict[str, str]:
    return {a.dataset_key: a.verdict for a in dq.assess(rows)}


def test_the_fixed_constants():
    assert dq.REFERENCE_SHARE == 1 / 30
    assert dq.CALENDAR_SHARE == 12 / 365.2425
    assert dq.MIN_DATE_ONLY == 300
    assert dq.FAMILY_LEVEL == 0.01
    assert dq.CLEAR_EXCESS_SHARE == 2 / 30


def test_below_three_hundred_date_only_records_is_too_few_to_test_whatever_the_share():
    assert verdicts(days("small", 299, 299)) == {"small": dq.TOO_FEW}
    assert verdicts(days("enough", 300, 10)) == {"enough": dq.CLOSE}


def test_a_share_near_one_in_thirty_is_close():
    assert verdicts(days("a", 3000, 100)) == {"a": dq.CLOSE}


def test_a_share_far_above_twice_one_in_thirty_is_a_clear_excess():
    assert verdicts(days("a", 3000, 400)) == {"a": dq.CLEAR}


def test_a_significant_excess_under_twice_one_in_thirty_is_a_small_excess():
    assert verdicts(days("a", 100_000, 4000)) == {"a": dq.SMALL}


def test_a_share_above_twice_one_in_thirty_is_not_clear_unless_its_interval_is():
    """25 of 300: the share is 0.083, above 2/30, but the interval's lower end is not."""
    (a,) = dq.assess([days("a", 300, 25)])
    assert a.share > dq.CLEAR_EXCESS_SHARE > a.interval[0]
    assert a.p_value < a.level_each
    assert a.verdict == dq.SMALL


def test_the_level_is_split_over_the_datasets_tested_and_only_those():
    # 48 of 1,000 on the 1st: upper tail 0.00876, under 0.01 and over 0.005.
    assert verdicts(days("a", 1000, 48)) == {"a": dq.SMALL}
    assert verdicts(days("a", 1000, 48), days("tiny", 10, 0)) == {"a": dq.SMALL, "tiny": dq.TOO_FEW}
    assert verdicts(days("a", 1000, 48), days("b", 1000, 33))["a"] == dq.CLOSE
    (assessed, _) = dq.assess([days("a", 1000, 48), days("b", 1000, 33)])
    assert assessed.level_each == pytest.approx(0.005)


def test_an_assessment_carries_both_reference_shares_and_the_excess():
    (a,) = dq.assess([days("a", 3000, 400)])
    assert a.share == pytest.approx(400 / 3000)
    assert a.ratio_to_reference == pytest.approx(400 / 3000 * 30)
    assert a.ratio_to_calendar == pytest.approx((400 / 3000) / (12 / 365.2425))
    assert a.excess_on_first == pytest.approx(400 - 3000 / 30)
    assert a.p_value == pytest.approx(dq.binomial_upper_tail(400, 3000, 1 / 30))
    assert a.interval == pytest.approx(dq.clopper_pearson(400, 3000))


# The candidate rules, as step lists the pipeline runs


def records_for_rules():
    return load(
        [
            row(1, "2021-06-01", dataset=DATASET_A),  # date-only on the 1st, flagged dataset
            row(2, "2021-06-01", dataset=DATASET_B),  # date-only on the 1st, other dataset
            row(3, "2021-06-01T00:00:00", dataset=DATASET_B),  # midnight on the 1st, clock time
            row(4, "2021-06-01T10:15:00", dataset=DATASET_A),  # the 1st, a real clock time
            row(5, "2021-06-14", dataset=DATASET_A),  # date-only, not the 1st
        ]
    )


def survivors(steps: f.Steps) -> set[int]:
    return {r.gbif_id for r in f.Pipeline(steps).run(records_for_rules())}


@pytest.mark.parametrize("make_steps", [f.t1_steps, f.r6_audit_steps], ids=["t1", "r6"])
def test_each_candidate_rule_drops_what_it_says(make_steps):
    steps = make_steps()
    assert survivors(dq.with_date_rule(steps, dq.DROP_ALL)) == {4, 5}
    assert survivors(dq.with_date_rule(steps, dq.KEEP_ALL)) == {1, 2, 4, 5}
    per_dataset = dq.DefaultDateInDatasets(frozenset({DATASET_A}))
    assert survivors(dq.with_date_rule(steps, per_dataset)) == {2, 4, 5}


@pytest.mark.parametrize("make_steps", [f.t1_steps, f.r6_audit_steps], ids=["t1", "r6"])
def test_drop_all_is_the_provisional_rule_already_in_the_step_lists(make_steps):
    steps = make_steps()
    assert dq.DROP_ALL is f.is_default_date
    assert survivors(dq.with_date_rule(steps, dq.DROP_ALL)) == survivors(steps)


def test_a_rule_replaces_only_the_date_step():
    steps = f.r6_audit_steps()
    changed = dq.with_date_rule(steps, dq.KEEP_ALL)
    assert changed.names() == steps.names()
    assert [s.drops for s in changed.filters] == [
        f.is_user_obscured,
        steps.filters[1].drops,
        dq.KEEP_ALL,
    ]
    assert changed.duplicate == steps.duplicate


def test_a_step_list_with_no_date_step_is_refused():
    steps = f.Steps(
        filters=(f.FilterStep("obscured", f.is_user_obscured),),
        duplicate=f.r6_audit_steps().duplicate,
    )
    with pytest.raises(ValueError, match="no default-date step"):
        dq.with_date_rule(steps, dq.KEEP_ALL)

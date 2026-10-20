"""T8's jump check (plan section 2): each branch of the reading rule on synthetic tallies."""

import pytest

from forager_forecast.t8 import jump as jp

CANTH = 9623860
GENERA = {"Boletus": 1, "Hydnum": 2, "Russula": 3, "Lactarius": 4, "Suillus": 5, "Amanita": 6}
MAIN = "inat"


def reading(**kw):
    base = dict(
        baseline_year=2023,
        rise_years=(2024,),
        new_observer=jp.NEW_SINCE_BASELINE,
        concentration=jp.CONCENTRATION_BOTH,
        genera=GENERA,
    )
    base.update(kw)
    return jp.JumpReading(**base)


def rec(
    year, observer, i, dataset=MAIN, week=None, cell=None, genus=CANTH, species=True, unit_year=0
):
    """A record spread over 20 weeks and 40 cells unless pinned; in a T1 unit of its own year
    unless unit_year says otherwise (None: in no T1 unit)."""
    week = 30 + i % 20 if week is None else week
    cell = f"c{i % 40}" if cell is None else cell
    return jp.JumpRecord(
        year=year,
        observer=observer,
        dataset=dataset,
        iso_week=week,
        cell=cell,
        unit=f"{cell}@{year}-{week}",
        genus_key=genus,
        has_species=species,
        unit_year=year if unit_year == 0 else unit_year,
    )


def baseline(n=100, observers=50):
    return [rec(2023, f"old{i % observers}", i) for i in range(n)]


def spread_rise(n=300, observers=150, prefix="r"):
    """Rise-year records from many light observers, spread over weeks and cells, main dataset."""
    return [rec(2024, f"{prefix}{i % observers}", i) for i in range(n)]


def genus_records(year, genus, n):
    return [rec(year, f"g{i}", i, genus=GENERA[genus], cell=f"g{i}", week=40) for i in range(n)]


UNITS = {2023: 1000, 2024: 1000}


def verdict(records, r=None):
    t = jp.tally(records, UNITS, CANTH, r or reading())
    return jp.read_jump(t), t


def test_new_heavy_observers_carrying_over_half_the_rise_is_reporting_led():
    rise = spread_rise(150, 150)
    # 3 new observers with 40 records each = 120 of a rise of 170 (270 - 100).
    rise += [rec(2024, f"heavy{k}", 1000 + k * 40 + i) for k in range(3) for i in range(40)]
    v, t = verdict(baseline() + rise)
    assert t.per_rise_year[2024].rise == 170
    assert t.per_rise_year[2024].new_heavy_records == 120
    assert v.label == jp.REPORTING_LED
    assert any("new observers" in reason for reason in v.reasons)


def test_nine_records_each_is_not_heavy():
    rise = spread_rise(150, 150)
    rise += [rec(2024, f"heavy{k}", 1000 + k * 9 + i) for k in range(14) for i in range(9)]
    v, t = verdict(baseline() + rise)
    assert t.per_rise_year[2024].new_heavy_records == 0
    assert v.label != jp.REPORTING_LED


def test_one_dataset_other_than_the_main_one_carrying_over_half_is_reporting_led():
    rise = spread_rise(100, 100)
    rise += [rec(2024, f"o{i}", 500 + i, dataset="club") for i in range(110)]
    v, t = verdict(baseline() + rise)
    tally = t.per_rise_year[2024]
    assert tally.main_dataset == MAIN
    assert tally.top_other_dataset == ("club", pytest.approx(110 / 110))
    assert v.label == jp.REPORTING_LED
    assert any("dataset club" in reason for reason in v.reasons)


def test_the_main_dataset_carrying_the_rise_is_not_reporting_led_by_dataset():
    v, t = verdict(baseline() + spread_rise(300, 150))
    assert t.per_rise_year[2024].top_other_dataset[0] == ""
    assert not any("dataset" in reason for reason in v.reasons)


def concentrated_rise():
    """A rise of 200, 150 of it in 3 weeks and 5 cells, from 150 light observers."""
    rise = spread_rise(150, 150)
    rise += [rec(2024, f"e{i}", 900 + i, week=40 + i % 3, cell=f"hot{i % 5}") for i in range(150)]
    return baseline() + rise


def test_a_rise_in_three_weeks_and_five_cells_is_reporting_led():
    v, t = verdict(concentrated_rise())
    tally = t.per_rise_year[2024]
    assert tally.top_weeks_share > 0.5 and tally.top_cells_share > 0.5
    assert v.label == jp.REPORTING_LED
    assert any("concentrated" in reason for reason in v.reasons)


def test_concentration_in_weeks_alone_is_led_only_under_the_either_reading():
    rise = spread_rise(150, 150)
    rise += [rec(2024, f"e{i}", 900 + i, week=40 + i % 3) for i in range(150)]
    records = baseline() + rise
    both, _ = verdict(records)
    either, t = verdict(records, reading(concentration=jp.CONCENTRATION_EITHER))
    assert t.per_rise_year[2024].top_weeks_share > 0.5
    assert t.per_rise_year[2024].top_cells_share <= 0.5
    assert not any("concentrated" in r for r in both.reasons)
    assert either.label == jp.REPORTING_LED


def test_block_reading_counts_the_rise_inside_top_weeks_by_top_cells():
    _v, t = verdict(concentrated_rise(), reading(concentration=jp.CONCENTRATION_BLOCK))
    tally = t.per_rise_year[2024]
    assert tally.block_rise >= 150
    assert tally.block_share > 0.5


def surge_records():
    """Observers more than double (50 to 150), the rise is spread, 4 of 6 genera rise 1.5x."""
    records = baseline() + spread_rise(300, 150)
    for g in ("Boletus", "Hydnum", "Russula", "Lactarius"):
        records += genus_records(2023, g, 10) + genus_records(2024, g, 15)
    for g in ("Suillus", "Amanita"):
        records += genus_records(2023, g, 10) + genus_records(2024, g, 14)
    return records


def test_doubled_observers_and_four_genera_rising_is_surge_consistent():
    v, t = verdict(surge_records())
    tally = t.per_rise_year[2024]
    assert (tally.baseline_observers, tally.rise_observers) == (50, 150)
    assert tally.genus_ratio["Boletus"] == pytest.approx(1.5)
    assert tally.genus_ratio["Suillus"] == pytest.approx(1.4)
    assert v.label == jp.SURGE_CONSISTENT


def test_three_genera_rising_is_undetermined():
    records = baseline() + spread_rise(300, 150)
    for g in ("Boletus", "Hydnum", "Russula"):
        records += genus_records(2023, g, 10) + genus_records(2024, g, 15)
    for g in ("Lactarius", "Suillus", "Amanita"):
        records += genus_records(2023, g, 10) + genus_records(2024, g, 10)
    v, _t = verdict(records)
    assert v.label == jp.UNDETERMINED


def test_observers_short_of_doubling_is_undetermined():
    records = baseline() + spread_rise(300, 99)
    for g in GENERA:
        records += genus_records(2023, g, 10) + genus_records(2024, g, 20)
    v, t = verdict(records)
    assert t.per_rise_year[2024].rise_observers == 99
    assert v.label == jp.UNDETERMINED


def test_no_rise_is_undetermined():
    v, _t = verdict(baseline(100) + spread_rise(90, 80))
    assert v.label == jp.UNDETERMINED
    assert "no rise" in v.reasons[0]


def test_two_rise_years_need_the_condition_in_both():
    records = concentrated_rise()  # 2024 concentrated
    records += [rec(2025, f"s{i % 150}", i) for i in range(300)]  # 2025 spread
    v, _t = verdict(records, reading(rise_years=(2024, 2025)))
    assert v.label != jp.REPORTING_LED


def test_new_observer_reading_all_prior_excludes_observers_seen_in_earlier_years():
    rise = spread_rise(150, 150)
    rise += [rec(2024, f"heavy{k}", 1000 + k * 40 + i) for k in range(3) for i in range(40)]
    earlier = [rec(2020, "heavy0", 5000 + i) for i in range(2)]
    _v, t = verdict(baseline() + rise + earlier, reading(new_observer=jp.NEW_SINCE_ALL_PRIOR))
    assert t.per_rise_year[2024].new_heavy_observers == 2


def test_species_share_and_rates_by_year():
    records = [rec(2023, "a", i, species=i < 3) for i in range(4)]
    records += genus_records(2023, "Boletus", 5)
    t = jp.tally(records, {2023: 50, 2024: 10}, CANTH, reading())
    assert t.species_share_by_year[2023] == pytest.approx(0.75)
    assert t.genus_rate_by_year["Boletus"][2023] == pytest.approx(0.1)


def test_j5_counts_genus_cell_weeks_by_the_units_iso_year_and_only_in_t1_units():
    """J5's rate is T1-unit cell-weeks with the genus over T1's units of that ISO year, so its
    numerator takes the unit's ISO year (a record of 2024-12-30 is in 2025-W01) and skips records
    in no T1 unit (sea units), which the denominator does not hold."""
    records = genus_records(2023, "Boletus", 5)
    records.append(rec(2024, "late", 900, genus=GENERA["Boletus"], cell="x", unit_year=2025))
    records.append(rec(2023, "sea", 901, genus=GENERA["Boletus"], cell="s", unit_year=None))
    t = jp.tally(records, {2023: 50, 2024: 10, 2025: 20}, CANTH, reading())
    assert t.genus_rate_by_year["Boletus"][2023] == pytest.approx(5 / 50)
    assert t.genus_rate_by_year["Boletus"][2024] == 0.0
    assert t.genus_rate_by_year["Boletus"][2025] == pytest.approx(1 / 20)


def test_a_reading_must_name_six_genera_and_distinct_years():
    with pytest.raises(ValueError, match="six"):
        reading(genera={"Boletus": 1})
    with pytest.raises(ValueError, match="differ"):
        reading(rise_years=(2023,))
    with pytest.raises(ValueError, match="Cantharellus"):
        jp.tally([], UNITS, 1, reading())


def one_year_cause_world():
    """2024's rise is carried by new heavy observers (a reporting cause); 2025's is spread over
    many light observers. Observers at least double and five genera rise 1.5x in both years."""
    records = baseline()
    records += [rec(2024, f"heavy{i % 22}", i) for i in range(220)]  # 22 new, 10 records each
    records += [rec(2024, f"light{i}", 1000 + i) for i in range(100)]
    records += [rec(2025, f"spread{i % 150}", 2000 + i) for i in range(300)]
    for g in list(GENERA)[:5]:
        records += genus_records(2023, g, 10) + genus_records(2024, g, 20)
        records += genus_records(2025, g, 20)
    return records


D134_UNITS = {2023: 1000, 2024: 1000, 2025: 1000}


def test_d134_a_cause_shown_in_one_comparison_only_reads_undetermined():
    t = jp.tally(one_year_cause_world(), D134_UNITS, CANTH, jp.ruled_reading(GENERA))
    assert t.reading.rise_years == (2024, 2025)
    v = jp.read_jump(t)
    assert v.label == jp.UNDETERMINED
    assert any("one comparison only" in r for r in v.reasons)


def test_d134_each_comparison_is_also_read_alone_and_reported():
    t = jp.tally(one_year_cause_world(), D134_UNITS, CANTH, jp.ruled_reading(GENERA))
    each = jp.read_each_comparison(t)
    assert {y: v.label for y, v in each.items()} == {
        2024: jp.REPORTING_LED,
        2025: jp.SURGE_CONSISTENT,
    }

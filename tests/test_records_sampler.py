"""The seeded hand-check sampler on a synthetic candidate pool.

The dispatch's own test is here: re-running the sampler with the same seed gives the same 200
records. The observation fixtures copy the shape of /v1/observations results read on 2026-09-18
(observation 1175887: quality_grade needs_id, taxon rank genus, identifications with current,
taxon and user).
"""

import csv
import random

import pytest

from forager_forecast.records import sampler as s


def identification(login: str, taxon_id: int, current: bool = True) -> dict:
    return {"current": current, "taxon": {"id": taxon_id, "name": "x"}, "user": {"login": login}}


def observation(obs_id: int, **overrides) -> dict:
    base = {
        "id": obs_id,
        "quality_grade": "needs_id",
        "observed_on": "2015-01-11",
        "taxon": {"id": s.CANTHARELLUS_INAT_TAXON_ID, "name": "Cantharellus", "rank": "genus"},
        "photos": [
            {"id": 1483729, "url": "https://static.inaturalist.org/photos/1483729/square.jpg"}
        ],
        "place_ids": [1, 14, 97394],
        "identifications": [
            identification("pdvmushroom", s.CANTHARELLUS_INAT_TAXON_ID),
            identification("rosawoodsii", s.CANTHARELLUS_INAT_TAXON_ID),
        ],
    }
    base.update(overrides)
    return base


STATES = {14: "California"}


def test_population_query_is_the_stated_pull():
    assert s.population_query() == {
        "taxon_id": "47348",
        "place_id": "97394",
        "lrank": "genus",
        "hrank": "genus",
        "quality_grade": "needs_id",
        "identifications": "most_agree",
        "verifiable": "true",
        "d1": "2015-01-01",
        "d2": "2025-12-31",
    }


def test_eligible_observation():
    assert s.is_eligible(observation(1))


def test_research_grade_is_not_eligible():
    assert not s.is_eligible(observation(1, quality_grade="research"))


def test_species_level_is_not_eligible():
    assert not s.is_eligible(
        observation(1, taxon={"id": 120443, "name": "Cantharellus formosus", "rank": "species"})
    )


def test_one_agreeing_identifier_is_not_enough():
    assert not s.is_eligible(observation(1, identifications=[identification("pdvmushroom", 47348)]))


def test_withdrawn_identification_does_not_count():
    assert not s.is_eligible(
        observation(
            1,
            identifications=[
                identification("pdvmushroom", 47348),
                identification("rosawoodsii", 47348, current=False),
            ],
        )
    )


def test_same_user_twice_is_one_identifier():
    assert not s.is_eligible(
        observation(
            1,
            identifications=[
                identification("pdvmushroom", 47348),
                identification("pdvmushroom", 47348),
            ],
        )
    )


def test_identification_at_another_taxon_does_not_agree():
    assert not s.is_eligible(
        observation(
            1,
            identifications=[identification("a", 47348), identification("b", 47349)],
        )
    )


def test_no_photo_is_not_eligible():
    assert not s.is_eligible(observation(1, photos=[]))


def test_candidate_links_date_and_state():
    cand = s.candidate_from_observation(observation(1175887), STATES)
    assert cand == s.Candidate(
        record_id=1175887,
        record_link="https://www.inaturalist.org/observations/1175887",
        photo_link="https://www.inaturalist.org/photos/1483729",
        date="2015-01-11",
        state_or_province="California",
    )


def test_unknown_state_is_left_empty_not_guessed():
    cand = s.candidate_from_observation(
        observation(5, place_ids=[1, 97394], place_guess="Boerne, TX"), STATES
    )
    assert cand.state_or_province == ""


def pool(n: int = 300) -> list[s.Candidate]:
    return [s.candidate_from_observation(observation(1000 + i), STATES) for i in range(n)]


def test_same_seed_gives_the_same_200_records():
    first = s.sample(pool(), seed=20260918)
    second = s.sample(pool(), seed=20260918)
    assert len(first) == 200
    assert [c.record_id for c in first] == [c.record_id for c in second]


def test_input_order_does_not_change_the_draw():
    shuffled = pool()
    random.Random(1).shuffle(shuffled)
    assert s.sample(shuffled, seed=20260918) == s.sample(pool(), seed=20260918)


def test_a_different_seed_gives_a_different_draw():
    assert s.sample(pool(), seed=20260918) != s.sample(pool(), seed=20260919)


def test_draw_has_no_repeats_and_only_pool_members():
    drawn = s.sample(pool(), seed=7)
    ids = [c.record_id for c in drawn]
    assert len(set(ids)) == 200
    assert set(ids) <= {c.record_id for c in pool()}


def test_too_few_candidates_is_an_error_not_a_short_file():
    with pytest.raises(s.TooFewCandidates, match="199 eligible candidates, 200 needed"):
        s.sample(pool(199), seed=1)


def test_hand_check_csv_columns_and_empty_verdicts(tmp_path):
    path = tmp_path / "hand-check.csv"
    drawn = s.sample(pool(), seed=20260918)
    s.write_hand_check_csv(path, drawn)
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0].keys()) == [
        "record_link",
        "photo_link",
        "date",
        "state_or_province",
        "verdict",
        "notes",
    ]
    assert len(rows) == 200
    assert all(r["verdict"] == "" and r["notes"] == "" for r in rows)
    assert rows[0]["record_link"].startswith("https://www.inaturalist.org/observations/")
    assert rows[0]["photo_link"].startswith("https://www.inaturalist.org/photos/")
    assert rows[0]["state_or_province"] == "California"

"""The 200-record hand-check sample: genus-level Cantharellus, two agreeing identifiers, not
research grade.

These records do not exist on GBIF. The iNaturalist dataset GBIF serves is research grade only
(dataset 50c9509d-22c7-4a22-a47d-8c48425ef4a7, description: "Achieved one of following
iNaturalist quality grades: Research", read 2026-09-18), so a not-research-grade record can only
come from iNaturalist itself. The candidates this module samples from are therefore iNaturalist
observation JSON objects, as /v1/observations returns them. Pulling them is a proposal for the
owner (T2 report, "Owner items"), since SPEC.md limits the iNaturalist API to counts and spot
checks; population_query() states the exact pull so the proposal is concrete.

The sampler itself is plain: sort the eligible candidates by observation id, then draw 200 with
random.Random(seed). The same seed on the same candidates gives the same 200 whatever order they
arrived in, and fewer than 200 candidates is an error, never a shorter file presented as done.
"""

from __future__ import annotations

import csv
import random
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANTHARELLUS_INAT_TAXON_ID = 47348  # /v1/taxa?q=Cantharellus, rank genus, read 2026-09-18
NORTH_AMERICA_INAT_PLACE_ID = 97394  # the place scripts/inat_counts.py counts against
RESEARCH_GRADE = "research"
MIN_AGREEING_IDENTIFIERS = 2
SAMPLE_SIZE = 200
INAT_STATE_ADMIN_LEVEL = 10  # iNaturalist places: admin_level 10 is state or province

HAND_CHECK_COLUMNS = (
    "record_link",
    "photo_link",
    "date",
    "state_or_province",
    "verdict",
    "notes",
)

Observation = Mapping[str, Any]


def population_query() -> dict[str, str]:
    """The /v1/observations parameters that name the candidate population, for the owner.

    On 2026-09-18 this query counted 17,165 observations (per_page=0, total_results). It is the
    smallest pull that carries identification agreement: the search result itself lists every
    identification with its taxon and user, so no per-record call is needed.
    """
    return {
        "taxon_id": str(CANTHARELLUS_INAT_TAXON_ID),
        "place_id": str(NORTH_AMERICA_INAT_PLACE_ID),
        "lrank": "genus",
        "hrank": "genus",
        "quality_grade": "needs_id",
        "identifications": "most_agree",
        "verifiable": "true",
        "d1": "2015-01-01",
        "d2": "2025-12-31",
    }


def agreeing_identifiers(observation: Observation) -> set[str]:
    """Logins of users whose current identification is the genus Cantharellus itself."""
    logins: set[str] = set()
    for identification in observation.get("identifications", ()):
        if not identification.get("current"):
            continue
        taxon = identification.get("taxon") or {}
        if taxon.get("id") != CANTHARELLUS_INAT_TAXON_ID:
            continue
        login = (identification.get("user") or {}).get("login")
        if login:
            logins.add(login)
    return logins


def is_eligible(observation: Observation) -> bool:
    """Genus-level Cantharellus, not research grade, two or more agreeing identifiers, a photo."""
    if observation.get("quality_grade") == RESEARCH_GRADE:
        return False
    taxon = observation.get("taxon") or {}
    if taxon.get("id") != CANTHARELLUS_INAT_TAXON_ID or taxon.get("rank") != "genus":
        return False
    if not observation.get("photos"):
        return False
    return len(agreeing_identifiers(observation)) >= MIN_AGREEING_IDENTIFIERS


@dataclass(frozen=True, order=True)
class Candidate:
    record_id: int
    record_link: str
    photo_link: str
    date: str
    state_or_province: str


def state_or_province(observation: Observation, state_names: Mapping[int, str]) -> str:
    """The state or province name among the observation's place_ids, or "" when none is known.

    state_names maps iNaturalist place id to name for places at admin level 10. It is fetched
    once for the distinct ids in the sample, not per record. An empty result is left empty and
    counted by the caller; nothing is guessed from place_guess, which is the observer's free text.
    """
    for place_id in observation.get("place_ids", ()):
        name = state_names.get(place_id)
        if name:
            return name
    return ""


def candidate_from_observation(
    observation: Observation, state_names: Mapping[int, str]
) -> Candidate:
    record_id = int(observation["id"])
    photos = observation.get("photos") or []
    photo_link = f"https://www.inaturalist.org/photos/{photos[0]['id']}" if photos else ""
    return Candidate(
        record_id=record_id,
        record_link=f"https://www.inaturalist.org/observations/{record_id}",
        photo_link=photo_link,
        date=str(observation.get("observed_on") or ""),
        state_or_province=state_or_province(observation, state_names),
    )


class TooFewCandidates(ValueError):
    pass


def sample(candidates: Iterable[Candidate], seed: int, size: int = SAMPLE_SIZE) -> list[Candidate]:
    """size distinct candidates, the same ones for the same seed and candidate set."""
    ordered = sorted(set(candidates), key=lambda c: c.record_id)
    if len(ordered) < size:
        raise TooFewCandidates(f"{len(ordered)} eligible candidates, {size} needed")
    drawn = random.Random(seed).sample(ordered, size)
    return sorted(drawn, key=lambda c: c.record_id)


def write_hand_check_csv(path: Path, drawn: Iterable[Candidate]) -> None:
    """The sheet a person fills in: the dispatch's columns, verdict and notes left empty."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HAND_CHECK_COLUMNS)
        for candidate in drawn:
            writer.writerow(
                (
                    candidate.record_link,
                    candidate.photo_link,
                    candidate.date,
                    candidate.state_or_province,
                    "",
                    "",
                )
            )

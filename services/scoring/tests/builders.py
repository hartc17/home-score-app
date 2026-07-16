from __future__ import annotations

from app.schemas import (
    CategoryWeights,
    ListingFacts,
    ListingObservations,
    ObservationItem,
    PhotoObservations,
    Rubric,
    RubricArchetype,
    RubricDirections,
    RubricGates,
)


def make_rubric(
    *,
    item_weights: dict[str, float] | None = None,
    directions: RubricDirections | None = None,
    category_weights: CategoryWeights | None = None,
    gates: RubricGates | None = None,
    confidence: dict[str, float] | None = None,
) -> Rubric:
    return Rubric(
        version="1.0",
        gates=gates,
        category_weights=category_weights
        or CategoryWeights(bones=20, warmth=20, finish=20, outdoor=20, value=10, age=10),
        item_weights=item_weights or {},
        directions=directions or RubricDirections(),
        archetype=RubricArchetype(name="x", blend={"x": 1.0}),
        confidence=confidence or {},
    )


def make_gates(**overrides: object) -> RubricGates:
    fields: dict[str, object] = {
        "budget_max": 1_000_000,
        "districts": [],
        "min_beds": 0,
        "min_baths": 0,
        "min_garage": 0,
        "exclude_main_road": False,
        "home_types": [],
    }
    fields.update(overrides)
    return RubricGates(**fields)  # type: ignore[arg-type]


def make_facts(**overrides: object) -> ListingFacts:
    return ListingFacts(url="https://example.com", photo_urls=[], **overrides)  # type: ignore[arg-type]


def single_photo(
    observations: dict[str, ObservationItem],
    *,
    room_type: str = "room",
    flags: list[str] | None = None,
) -> ListingObservations:
    return ListingObservations(
        photos=[PhotoObservations(room_type=room_type, observations=observations)],
        flags=flags or [],
        model="stub",
        schema_version="1.0",
    )


def empty_observations(*, flags: list[str] | None = None) -> ListingObservations:
    return ListingObservations(photos=[], flags=flags or [], model="stub", schema_version="1.0")

import pytest

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
from app.scoring.engine import score


def _base_rubric(**overrides) -> Rubric:
    return Rubric(
        version="1.0",
        category_weights=CategoryWeights(
            bones=25, warmth=20, finish=20, outdoor=15, value=10, age=10
        ),
        item_weights={"tone_warmth": 10.0, "condition": 5.0},
        directions=RubricDirections(tone="warm"),
        archetype=RubricArchetype(name="cozy", blend={"cozy": 1.0}),
        confidence={},
        **overrides,
    )


def _empty_observations() -> ListingObservations:
    return ListingObservations(
        photos=[],
        flags=[],
        model="stub",
        schema_version="1.0",
    )


def _base_facts(**overrides) -> ListingFacts:
    return ListingFacts(url="https://example.com", photo_urls=[], **overrides)


def test_score_disqualified_by_price_returns_disqualified_gate():
    rubric = _base_rubric(
        gates=RubricGates(
            budget_max=500_000,
            districts=[],
            min_beds=3,
            min_baths=2,
            min_garage=1,
            exclude_main_road=False,
            home_types=[],
        )
    )
    facts = _base_facts(price=600_000, beds=3, baths=2, garage=1)
    result = score(rubric, _empty_observations(), facts)

    assert result.gate == "disqualified"
    assert result.total == 0.0
    assert result.verdict == "weak"
    assert "budget_max" in (result.disqualified_reason or "")


def test_score_disqualified_by_beds_returns_disqualified_gate():
    rubric = _base_rubric(
        gates=RubricGates(
            budget_max=1_000_000,
            districts=[],
            min_beds=4,
            min_baths=2,
            min_garage=0,
            exclude_main_road=False,
            home_types=[],
        )
    )
    facts = _base_facts(price=400_000, beds=3, baths=2, garage=2)
    result = score(rubric, _empty_observations(), facts)

    assert result.gate == "disqualified"
    assert "min_beds" in (result.disqualified_reason or "")


def test_score_no_gates_passes_gate():
    rubric = _base_rubric()
    result = score(rubric, _empty_observations(), _base_facts())

    assert result.gate == "pass"


def test_score_warm_direction_high_warmth_scores_high():
    rubric = _base_rubric()
    obs = ListingObservations(
        photos=[
            PhotoObservations(
                room_type="living",
                observations={
                    "tone_warmth": ObservationItem(value=9.0, confidence=1.0),
                },
            )
        ],
        flags=[],
        model="stub",
        schema_version="1.0",
    )
    result = score(rubric, obs, _base_facts())

    assert result.gate == "pass"
    assert result.total > 5.0
    assert "tone_warmth" in result.observation_trace


def test_score_warm_direction_low_warmth_scores_low():
    rubric = _base_rubric()
    obs = ListingObservations(
        photos=[
            PhotoObservations(
                room_type="living",
                observations={
                    "tone_warmth": ObservationItem(value=1.0, confidence=1.0),
                },
            )
        ],
        flags=[],
        model="stub",
        schema_version="1.0",
    )
    result_low = score(rubric, obs, _base_facts())

    obs_high = ListingObservations(
        photos=[
            PhotoObservations(
                room_type="living",
                observations={
                    "tone_warmth": ObservationItem(value=9.0, confidence=1.0),
                },
            )
        ],
        flags=[],
        model="stub",
        schema_version="1.0",
    )
    result_high = score(rubric, obs_high, _base_facts())

    assert result_low.total < result_high.total


def test_score_verdict_pursue_when_total_above_80():
    rubric = Rubric(
        version="1.0",
        category_weights=CategoryWeights(
            bones=25, warmth=20, finish=20, outdoor=15, value=10, age=10
        ),
        item_weights={
            "tone_warmth": 20.0,
            "ceiling_height": 25.0,
            "condition": 20.0,
            "curb_appeal": 15.0,
        },
        directions=RubricDirections(tone="warm"),
        archetype=RubricArchetype(name="cozy", blend={"cozy": 1.0}),
        confidence={},
    )
    obs = ListingObservations(
        photos=[
            PhotoObservations(
                room_type="living",
                observations={
                    "tone_warmth": ObservationItem(value=10.0, confidence=1.0),
                    "ceiling_height": ObservationItem(value=10.0, confidence=1.0),
                    "condition": ObservationItem(value=10.0, confidence=1.0),
                    "curb_appeal": ObservationItem(value=10.0, confidence=1.0),
                },
            )
        ],
        flags=[],
        model="stub",
        schema_version="1.0",
    )
    result = score(rubric, obs, _base_facts())
    assert result.verdict == "pursue"


def test_score_verdict_weak_when_total_below_50():
    rubric = _base_rubric()
    result = score(rubric, _empty_observations(), _base_facts())
    assert result.verdict == "weak"
    assert result.total == 0.0


def test_score_propagates_flags_from_observations():
    rubric = _base_rubric()
    obs = _empty_observations()
    obs.flags = ["roof_concern", "deferred_maintenance"]
    result = score(rubric, obs, _base_facts())

    assert result.flags == ["roof_concern", "deferred_maintenance"]

from app.schemas import CategoryWeights, ObservationItem, RubricDirections
from app.scoring.engine import score
from tests.builders import empty_observations, make_facts, make_gates, make_rubric, single_photo

_WARM_WEIGHTS = CategoryWeights(bones=25, warmth=20, finish=20, outdoor=15, value=10, age=10)


def _warm_rubric(**overrides):
    return make_rubric(
        item_weights={"tone_warmth": 10.0, "condition": 5.0},
        directions=RubricDirections(tone="warm"),
        category_weights=_WARM_WEIGHTS,
        **overrides,
    )


def _tone(value: float) -> dict[str, ObservationItem]:
    return {"tone_warmth": ObservationItem(value=value, confidence=1.0)}


def test_score_disqualified_by_price_returns_disqualified_gate():
    rubric = _warm_rubric(gates=make_gates(budget_max=500_000, min_beds=3, min_baths=2, min_garage=1))
    facts = make_facts(price=600_000, beds=3, baths=2, garage=1)
    result = score(rubric, empty_observations(), facts)

    assert result.gate == "disqualified"
    assert result.total == 0.0
    assert result.verdict == "weak"
    assert "budget_max" in (result.disqualified_reason or "")


def test_score_disqualified_by_beds_returns_disqualified_gate():
    rubric = _warm_rubric(gates=make_gates(min_beds=4, min_baths=2))
    facts = make_facts(price=400_000, beds=3, baths=2, garage=2)
    result = score(rubric, empty_observations(), facts)

    assert result.gate == "disqualified"
    assert "min_beds" in (result.disqualified_reason or "")


def test_score_no_gates_passes_gate():
    result = score(_warm_rubric(), empty_observations(), make_facts())
    assert result.gate == "pass"


def test_score_warm_direction_high_warmth_scores_high():
    result = score(_warm_rubric(), single_photo(_tone(9.0), room_type="living"), make_facts())

    assert result.gate == "pass"
    assert result.total > 5.0
    assert "tone_warmth" in result.observation_trace


def test_score_warm_direction_low_warmth_scores_lower_than_high():
    rubric = _warm_rubric()
    low = score(rubric, single_photo(_tone(1.0), room_type="living"), make_facts())
    high = score(rubric, single_photo(_tone(9.0), room_type="living"), make_facts())

    assert low.total < high.total


def test_score_verdict_pursue_when_total_above_80():
    rubric = make_rubric(
        item_weights={"tone_warmth": 20.0, "ceiling_height": 25.0, "condition": 20.0, "curb_appeal": 15.0},
        directions=RubricDirections(tone="warm"),
        category_weights=_WARM_WEIGHTS,
    )
    obs = single_photo(
        {
            "tone_warmth": ObservationItem(value=10.0, confidence=1.0),
            "ceiling_height": ObservationItem(value=10.0, confidence=1.0),
            "condition": ObservationItem(value=10.0, confidence=1.0),
            "curb_appeal": ObservationItem(value=10.0, confidence=1.0),
        },
        room_type="living",
    )
    assert score(rubric, obs, make_facts()).verdict == "pursue"


def test_score_verdict_weak_when_total_below_50():
    result = score(_warm_rubric(), empty_observations(), make_facts())
    assert result.verdict == "weak"
    assert result.total == 0.0


def test_score_propagates_flags_from_observations():
    obs = empty_observations(flags=["roof_concern", "deferred_maintenance"])
    result = score(_warm_rubric(), obs, make_facts())
    assert result.flags == ["roof_concern", "deferred_maintenance"]

from app.rubrics.merge import compose_forward, has_quiz_signal, merge_gates
from app.schemas import CategoryWeights, Rubric, RubricArchetype, RubricDirections, RubricGates


def _quiz_rubric() -> Rubric:
    return Rubric(
        version="1.0",
        category_weights=CategoryWeights(bones=20, warmth=30, finish=20, outdoor=20, value=5, age=5),
        item_weights={"tone_warmth": 10.0, "flooring": 8.0},
        directions=RubricDirections(tone="warm", era="traditional"),
        archetype=RubricArchetype(name="The Hearthkeeper", blend={"farmhouse": 0.6}),
        confidence={"warmth": 0.9},
    )


def _empty_rubric() -> Rubric:
    return Rubric(
        version="1.0",
        category_weights=CategoryWeights(bones=17, warmth=17, finish=16, outdoor=17, value=17, age=16),
        item_weights={},
        directions=RubricDirections(),
        archetype=RubricArchetype(name="none", blend={}),
        confidence={},
    )


_GATES = RubricGates(
    budget_max=600000,
    districts=["Saratoga Springs"],
    min_beds=3,
    min_baths=2,
    min_garage=2,
    exclude_main_road=True,
    home_types=["single_family"],
)


def test_merge_gates_keeps_quiz_parts():
    merged = merge_gates(_quiz_rubric(), _GATES)
    assert merged.gates == _GATES
    assert merged.item_weights == _quiz_rubric().item_weights
    assert merged.directions.tone == "warm"


def test_compose_keeps_quiz_parts_and_account_gates():
    account = merge_gates(_empty_rubric(), _GATES)
    merged = compose_forward(_quiz_rubric(), account)
    assert merged.item_weights == _quiz_rubric().item_weights
    assert merged.gates == _GATES


def test_compose_does_not_overwrite_quiz_with_empty_account():
    merged = compose_forward(_quiz_rubric(), _empty_rubric())
    assert merged.archetype.name == "The Hearthkeeper"


def test_compose_preserves_account_quiz_when_anonymous_has_none():
    account = merge_gates(_quiz_rubric(), _GATES)
    merged = compose_forward(_empty_rubric(), account)
    assert merged.item_weights == _quiz_rubric().item_weights
    assert merged.gates == _GATES


def test_has_quiz_signal_detects_empty():
    assert has_quiz_signal(_quiz_rubric()) is True
    assert has_quiz_signal(_empty_rubric()) is False

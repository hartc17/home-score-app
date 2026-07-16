from app.rubrics.merge import merge_gates
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

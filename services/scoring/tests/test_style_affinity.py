from app.schemas import (
    ListingObservations,
    ObservationItem,
    Rubric,
    RubricDirections,
    StyleClassification,
)
from app.scoring.engine import score
from tests.builders import make_facts as _facts
from tests.builders import make_rubric, single_photo

WARM_TRAD = RubricDirections(tone="warm", era="traditional", ornament="ornate", naturalness="natural")
COOL_MODERN = RubricDirections(tone="cool", era="modern", ornament="minimal", naturalness="engineered")


def _rubric(item_weights: dict[str, float], directions: RubricDirections) -> Rubric:
    return make_rubric(item_weights=item_weights, directions=directions)


def _obs(item_key: str, value: object, confidence: float = 0.9) -> ListingObservations:
    return single_photo({item_key: ObservationItem(value=value, confidence=confidence)})


def _styles(*pairs: tuple[str, float]) -> list[StyleClassification]:
    return [StyleClassification(style=s, confidence=c) for s, c in pairs]


def test_style_affinity_farmhouse_scores_higher_for_warm_traditional_rubric():
    obs = _obs("exterior_style", _styles(("farmhouse", 0.9)))
    warm = score(_rubric({"exterior_style": 10.0}, WARM_TRAD), obs, _facts()).total
    cool = score(_rubric({"exterior_style": 10.0}, COOL_MODERN), obs, _facts()).total
    assert warm > cool
    assert warm > 60
    assert cool < 40


def test_style_affinity_modern_listing_prefers_modern_rubric():
    obs = _obs("interior_style", _styles(("modern", 0.9)))
    modern = score(_rubric({"interior_style": 10.0}, COOL_MODERN), obs, _facts()).total
    trad = score(_rubric({"interior_style": 10.0}, WARM_TRAD), obs, _facts()).total
    assert modern > trad


def test_style_affinity_interior_style_scores_in_finish_category():
    obs = _obs("interior_style", _styles(("scandinavian", 0.9)))
    result = score(_rubric({"interior_style": 10.0}, COOL_MODERN), obs, _facts())
    assert "finish" in result.category_scores


def test_style_affinity_no_directions_yields_no_style_contribution():
    obs = _obs("exterior_style", _styles(("farmhouse", 0.9)))
    result = score(_rubric({"exterior_style": 10.0}, RubricDirections()), obs, _facts())
    assert "outdoor" not in result.category_scores
    assert result.total == 0.0


def test_style_affinity_pure_style_beats_mixed_blend_for_matching_rubric():
    pure = _obs("exterior_style", _styles(("farmhouse", 0.9)))
    blend = _obs("exterior_style", _styles(("farmhouse", 0.5), ("modern", 0.5)))
    rubric = _rubric({"exterior_style": 10.0}, WARM_TRAD)
    assert score(rubric, pure, _facts()).total > score(rubric, blend, _facts()).total


def test_style_affinity_accepts_plain_string_value():
    obs = _obs("exterior_style", "farmhouse")
    result = score(_rubric({"exterior_style": 10.0}, WARM_TRAD), obs, _facts())
    assert result.total > 60


def test_style_affinity_unknown_style_is_ignored():
    obs = _obs("exterior_style", _styles(("not_a_real_style", 0.9)))
    result = score(_rubric({"exterior_style": 10.0}, WARM_TRAD), obs, _facts())
    assert result.total == 0.0


def test_style_affinity_trace_names_top_style():
    obs = _obs("exterior_style", _styles(("farmhouse", 0.8), ("craftsman", 0.2)))
    result = score(_rubric({"exterior_style": 10.0}, WARM_TRAD), obs, _facts())
    assert "farmhouse" in result.observation_trace["exterior_style"]

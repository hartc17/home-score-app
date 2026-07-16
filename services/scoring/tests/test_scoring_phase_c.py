from app.schemas import (
    CategoryWeights,
    ListingObservations,
    ObservationItem,
    Rubric,
    RubricDirections,
    RubricGates,
)
from app.scoring.config import get_config
from app.scoring.engine import score
from tests.builders import make_facts as _facts
from tests.builders import make_rubric, single_photo


def _rubric(
    item_weights: dict[str, float],
    directions: RubricDirections,
    category_weights: CategoryWeights | None = None,
    gates: RubricGates | None = None,
) -> Rubric:
    return make_rubric(
        item_weights=item_weights, directions=directions, category_weights=category_weights, gates=gates
    )


def _obs(observations: dict[str, ObservationItem], flags: list[str] | None = None) -> ListingObservations:
    return single_photo(observations, flags=flags)


def test_score_two_rubrics_opposite_tone_produce_different_totals():
    obs = _obs({"tone_warmth": ObservationItem(value=9.0, confidence=1.0)})
    warm = _rubric({"tone_warmth": 10.0}, RubricDirections(tone="warm"))
    cool = _rubric({"tone_warmth": 10.0}, RubricDirections(tone="cool"))

    warm_total = score(warm, obs, _facts()).total
    cool_total = score(cool, obs, _facts()).total

    assert warm_total > 80
    assert cool_total < 20
    assert abs(warm_total - cool_total) > 50


def test_score_different_category_weights_produce_different_totals():
    obs = _obs(
        {
            "tone_warmth": ObservationItem(value=10.0, confidence=1.0),
            "condition": ObservationItem(value=2.0, confidence=1.0),
        }
    )
    warmth_heavy = _rubric(
        {"tone_warmth": 20.0, "condition": 20.0},
        RubricDirections(tone="warm"),
        CategoryWeights(bones=10, warmth=60, finish=10, outdoor=10, value=5, age=5),
    )
    finish_heavy = _rubric(
        {"tone_warmth": 20.0, "condition": 20.0},
        RubricDirections(tone="warm"),
        CategoryWeights(bones=10, warmth=10, finish=60, outdoor=10, value=5, age=5),
    )

    # Warmth is perfect and finish is poor, so the warmth-heavy taste scores higher.
    assert score(warmth_heavy, obs, _facts()).total > score(finish_heavy, obs, _facts()).total


def test_score_low_confidence_does_not_change_total_but_adds_dd_item():
    rubric = _rubric({"tone_warmth": 10.0}, RubricDirections(tone="warm"))
    high = score(rubric, _obs({"tone_warmth": ObservationItem(value=9.0, confidence=0.9)}), _facts())
    low = score(rubric, _obs({"tone_warmth": ObservationItem(value=9.0, confidence=0.3)}), _facts())

    assert high.total == low.total
    assert not any("tone_warmth" in d for d in high.dd_items)
    assert any("tone_warmth" in d and "low confidence" in d for d in low.dd_items)


def test_score_cabinets_match_governed_by_walls_direction():
    obs = _obs({"cabinets": ObservationItem(value="painted_white", confidence=1.0)})
    white = _rubric({"cabinets": 10.0}, RubricDirections(walls="white_preferred"))
    color = _rubric({"cabinets": 10.0}, RubricDirections(walls="color_preferred"))

    assert score(white, obs, _facts()).total > score(color, obs, _facts()).total


def test_score_flooring_hardwood_scores_higher_than_carpet():
    rubric = _rubric({"flooring": 10.0}, RubricDirections())
    hardwood = score(rubric, _obs({"flooring": ObservationItem(value="hardwood", confidence=1.0)}), _facts())
    carpet = score(rubric, _obs({"flooring": ObservationItem(value="carpet", confidence=1.0)}), _facts())

    assert hardwood.total > carpet.total


def test_score_value_stub_uses_budget_headroom():
    rubric = _rubric(
        {},
        RubricDirections(),
        gates=RubricGates(
            budget_max=500_000,
            districts=[],
            min_beds=0,
            min_baths=0,
            min_garage=0,
            exclude_main_road=False,
            home_types=[],
        ),
    )
    under = score(rubric, _obs({}), _facts(price=400_000))
    near = score(rubric, _obs({}), _facts(price=495_000))

    assert "value" in under.category_scores
    assert under.total > near.total


def test_score_not_observed_item_adds_verify_dd_item():
    rubric = _rubric({"fireplace": 10.0}, RubricDirections(tone="warm"))
    obs = _obs({"fireplace": ObservationItem(value=None, confidence=0.2, not_observed=True)})
    result = score(rubric, obs, _facts())

    assert any("fireplace" in d for d in result.dd_items)
    assert "warmth" not in result.category_scores


def test_score_flag_on_item_adds_verify_dd_item():
    rubric = _rubric({"fireplace": 10.0}, RubricDirections(tone="warm"))
    obs = _obs(
        {"fireplace": ObservationItem(value="unverified_wood", confidence=0.4, flag="wood_vs_gas_unverified")}
    )
    result = score(rubric, obs, _facts())

    assert any("wood_vs_gas_unverified" in d for d in result.dd_items)


def test_config_loads_match_tables_from_json():
    cfg = get_config()
    assert "flooring" in cfg.categorical_match
    assert cfg.confidence_threshold == 0.5
    assert cfg.item_category["tone_warmth"] == "warmth"

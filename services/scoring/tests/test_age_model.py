from app.scoring.config import get_config
from app.scoring.engine import _age_fraction, _home_age, score
from tests.builders import empty_observations, make_facts, make_rubric

CFG = get_config()
REF = CFG.reference_year


def _age_of(result) -> float | None:
    return result.category_scores.get("age")


def test_age_scored_from_year_built_and_included_in_total():
    result = score(make_rubric(), empty_observations(), make_facts(year_built=REF - 5))
    assert "age" in result.category_scores
    assert result.total > 0


def test_age_excluded_when_year_built_missing():
    result = score(make_rubric(), empty_observations(), make_facts(year_built=None))
    assert "age" not in result.category_scores


def test_newer_home_scores_higher_on_age_than_older():
    new = score(make_rubric(), empty_observations(), make_facts(year_built=REF - 3))
    old = score(make_rubric(), empty_observations(), make_facts(year_built=REF - 90))
    assert _age_of(new) > _age_of(old)


def test_old_home_adds_systems_due_diligence():
    result = score(make_rubric(), empty_observations(), make_facts(year_built=REF - 60))
    assert any("roof, HVAC, electrical" in item for item in result.dd_items)


def test_recent_home_has_no_systems_due_diligence():
    result = score(make_rubric(), empty_observations(), make_facts(year_built=REF - 5))
    assert not any("roof, HVAC, electrical" in item for item in result.dd_items)


def test_future_year_built_is_treated_as_new_construction():
    result = score(make_rubric(), empty_observations(), make_facts(year_built=REF + 1))
    assert _home_age(make_facts(year_built=REF + 1), CFG) == 0
    assert _age_of(result) == _age_of(score(make_rubric(), empty_observations(), make_facts(year_built=REF)))
    assert not any("roof, HVAC, electrical" in item for item in result.dd_items)


def test_age_fraction_bands_are_monotonic_non_increasing():
    fractions = [_age_fraction(age, CFG) for age in (5, 20, 40, 70, 150)]
    assert fractions == sorted(fractions, reverse=True)


def test_age_trace_names_the_build_year():
    result = score(make_rubric(), empty_observations(), make_facts(year_built=1975))
    assert "1975" in result.observation_trace["age"]

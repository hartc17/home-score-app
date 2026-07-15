from pathlib import Path

from fastapi.testclient import TestClient

from app.listings.parser import parse_listing_html
from app.main import app
from app.schemas import (
    CategoryWeights,
    ListingObservations,
    ObservationItem,
    PhotoObservations,
    Rubric,
    RubricArchetype,
    RubricDirections,
)
from app.scoring.engine import score

_FIXTURE = (Path(__file__).parent / "fixtures" / "sample_listing.html").read_text()
client = TestClient(app)


def _observations() -> ListingObservations:
    # Hand-authored as the vision layer would produce, so the deterministic chain
    # can be exercised while real vision remains pending scoring-contract.md.
    return ListingObservations(
        photos=[
            PhotoObservations(
                room_type="living",
                observations={
                    "tone_warmth": ObservationItem(value=8.0, confidence=0.9),
                    "flooring": ObservationItem(value="hardwood", confidence=0.8),
                    "condition": ObservationItem(value=8.0, confidence=0.9),
                },
            ),
            PhotoObservations(
                room_type="exterior",
                observations={"curb_appeal": ObservationItem(value=7.0, confidence=0.9)},
            ),
        ],
        flags=[],
        model="stub",
        schema_version="1.0",
    )


def _rubric(directions: RubricDirections) -> Rubric:
    return Rubric(
        version="1.0",
        category_weights=CategoryWeights(bones=15, warmth=30, finish=25, outdoor=20, value=5, age=5),
        item_weights={"tone_warmth": 20.0, "flooring": 15.0, "condition": 10.0, "curb_appeal": 20.0},
        directions=directions,
        archetype=RubricArchetype(name="x", blend={"x": 1.0}),
        confidence={},
    )


def test_pipeline_parse_then_score_produces_full_result():
    facts = parse_listing_html("https://example.com/42-maple", _FIXTURE)
    result = score(_rubric(RubricDirections(tone="warm")), _observations(), facts)

    assert result.gate == "pass"
    assert result.total > 0
    assert result.verdict in {"pursue", "showing", "conditional", "weak"}
    assert "tone_warmth" in result.observation_trace
    assert "warmth" in result.observation_trace


def test_pipeline_two_rubrics_differ_on_same_listing():
    facts = parse_listing_html("https://example.com/42-maple", _FIXTURE)
    obs = _observations()
    warm = score(_rubric(RubricDirections(tone="warm")), obs, facts).total
    cool = score(_rubric(RubricDirections(tone="cool")), obs, facts).total

    assert warm != cool


def test_score_route_returns_full_result_over_http():
    payload = {
        "rubric": _rubric(RubricDirections(tone="warm")).model_dump(),
        "observations": _observations().model_dump(),
        "facts": parse_listing_html("https://example.com/42-maple", _FIXTURE).model_dump(),
    }
    response = client.post("/score", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["gate"] == "pass"
    assert body["total"] > 0
    assert "tone_warmth" in body["observation_trace"]

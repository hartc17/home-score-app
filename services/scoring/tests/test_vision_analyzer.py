import json

from app.photos.analyzer import StubAnalyzer, resolve_analyzer
from app.photos.vision import ClaudeVisionAnalyzer, build_user_prompt
from app.schemas import (
    CategoryWeights,
    ListingFacts,
    Rubric,
    RubricArchetype,
    RubricDirections,
    StyleClassification,
)
from app.scoring.engine import score


class _Block:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _Response:
    def __init__(self, text: str, model: str = "claude-opus-4-8") -> None:
        self.content = [_Block(text)]
        self.model = model


class _Messages:
    def __init__(self, text: str) -> None:
        self._text = text
        self.calls: list[dict] = []

    def create(self, **kwargs) -> _Response:
        self.calls.append(kwargs)
        return _Response(self._text)


class _Client:
    def __init__(self, text: str) -> None:
        self.messages = _Messages(text)


_VISION_JSON = json.dumps(
    {
        "schema_version": "1.0",
        "photos": [
            {
                "room_type": "living",
                "observations": {
                    "tone_warmth": {"value": 8, "confidence": 0.9},
                    "interior_style": {"value": [{"style": "farmhouse", "confidence": 0.7}], "confidence": 0.7},
                },
            },
            {
                "room_type": "exterior_front",
                "observations": {
                    "exterior_style": {"value": [{"style": "modern_farmhouse", "confidence": 0.8}], "confidence": 0.8},
                    "curb_appeal": {"value": 7, "confidence": 0.8},
                },
            },
        ],
        "overall_style": {"value": [{"style": "farmhouse", "confidence": 0.6}], "confidence": 0.6},
        "flags": ["district_not_determined"],
    }
)


def _facts(photo_urls) -> ListingFacts:
    return ListingFacts(url="https://example.com", photo_urls=photo_urls)


def test_analyze_parses_photos_styles_and_flags():
    analyzer = ClaudeVisionAnalyzer(client=_Client(_VISION_JSON))
    result = analyzer.analyze(_facts(["a.jpg", "b.jpg"]))

    assert len(result.photos) == 2
    living = result.photos[0].observations
    assert living["tone_warmth"].value == 8
    assert isinstance(living["interior_style"].value, list)
    assert isinstance(living["interior_style"].value[0], StyleClassification)
    assert living["interior_style"].value[0].style == "farmhouse"
    assert "district_not_determined" in result.flags
    assert result.overall_style is not None
    assert result.model == "claude-opus-4-8"


def test_analyze_empty_photos_skips_model_call():
    client = _Client(_VISION_JSON)
    result = ClaudeVisionAnalyzer(client=client).analyze(_facts([]))

    assert result.flags == ["no_photos"]
    assert client.messages.calls == []


def test_analyze_caps_photo_count_at_15():
    client = _Client(_VISION_JSON)
    ClaudeVisionAnalyzer(client=client).analyze(_facts([f"p{i}.jpg" for i in range(20)]))

    content = client.messages.calls[0]["messages"][0]["content"]
    images = [block for block in content if block["type"] == "image"]
    assert len(images) == 15


def test_analyze_handles_code_fenced_json():
    fenced = f"```json\n{_VISION_JSON}\n```"
    result = ClaudeVisionAnalyzer(client=_Client(fenced)).analyze(_facts(["a.jpg"]))
    assert len(result.photos) == 2


def test_vision_output_feeds_scoring_engine():
    observations = ClaudeVisionAnalyzer(client=_Client(_VISION_JSON)).analyze(_facts(["a.jpg"]))
    rubric = Rubric(
        version="1.0",
        category_weights=CategoryWeights(bones=15, warmth=25, finish=20, outdoor=25, value=10, age=5),
        item_weights={"tone_warmth": 15.0, "interior_style": 10.0, "exterior_style": 15.0, "curb_appeal": 10.0},
        directions=RubricDirections(tone="warm", era="traditional", ornament="ornate", naturalness="natural"),
        archetype=RubricArchetype(name="x", blend={"x": 1.0}),
        confidence={},
    )
    result = score(rubric, observations, _facts(["a.jpg"]))
    assert result.gate == "pass"
    assert result.total > 0


def test_build_user_prompt_includes_style_vocab():
    prompt = build_user_prompt(3)
    assert "farmhouse" in prompt
    assert "room_type" in prompt


def test_resolve_analyzer_uses_stub_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert isinstance(resolve_analyzer(), StubAnalyzer)


def test_resolve_analyzer_uses_vision_with_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert isinstance(resolve_analyzer(), ClaudeVisionAnalyzer)

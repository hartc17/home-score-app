import json

from app.photos.analyzer import StubAnalyzer, resolve_analyzer
from app.photos.vision import (
    DEFAULT_ANALYSIS_MODEL,
    DEFAULT_TRIAGE_MODEL,
    ClaudeVisionAnalyzer,
    build_triage_prompt,
    build_user_prompt,
)
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
    def __init__(self, text: str, model: str) -> None:
        self.content = [_Block(text)]
        self.model = model


class _Messages:
    def __init__(self, analysis_text: str, triage_text: str | None) -> None:
        self._analysis = analysis_text
        self._triage = triage_text
        self.calls: list[dict] = []

    def create(self, **kwargs) -> _Response:
        self.calls.append(kwargs)
        if kwargs["model"] == DEFAULT_TRIAGE_MODEL and self._triage is not None:
            return _Response(self._triage, DEFAULT_TRIAGE_MODEL)
        return _Response(self._analysis, DEFAULT_ANALYSIS_MODEL)


class _Client:
    def __init__(self, analysis_text: str, triage_text: str | None = None) -> None:
        self.messages = _Messages(analysis_text, triage_text)


def _fail_fetch(_: str) -> bytes:
    # Keep photos as URL blocks so image-count assertions do not depend on PIL.
    raise OSError("no fetch in test")


def _analyzer(analysis_text: str, triage_text: str | None = None, **kwargs) -> ClaudeVisionAnalyzer:
    return ClaudeVisionAnalyzer(
        client=_Client(analysis_text, triage_text), fetch_image=_fail_fetch, **kwargs
    )


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


def _analysis_call(client: _Client) -> dict:
    return next(c for c in client.messages.calls if c["model"] == DEFAULT_ANALYSIS_MODEL)


def _images(call: dict) -> list[dict]:
    return [b for b in call["messages"][0]["content"] if b["type"] == "image"]


def test_analyze_parses_photos_styles_and_flags():
    analyzer = _analyzer(_VISION_JSON)
    result = analyzer.analyze(_facts(["https://x/a.jpg", "https://x/b.jpg"]))

    assert len(result.photos) == 2
    living = result.photos[0].observations
    assert living["tone_warmth"].value == 8
    assert isinstance(living["interior_style"].value[0], StyleClassification)
    assert living["interior_style"].value[0].style == "farmhouse"
    assert "district_not_determined" in result.flags
    assert result.overall_style is not None
    assert result.model == DEFAULT_ANALYSIS_MODEL


def test_analyze_empty_photos_skips_model_call():
    client = _Client(_VISION_JSON)
    result = ClaudeVisionAnalyzer(client=client, fetch_image=_fail_fetch).analyze(_facts([]))

    assert result.flags == ["no_photos"]
    assert client.messages.calls == []


def test_small_listing_skips_triage_and_sends_all_photos():
    client = _Client(_VISION_JSON, triage_text='{"rooms": []}')
    ClaudeVisionAnalyzer(client=client, fetch_image=_fail_fetch).analyze(
        _facts([f"https://x/p{i}.jpg" for i in range(5)])
    )

    assert [c["model"] for c in client.messages.calls] == [DEFAULT_ANALYSIS_MODEL]
    assert len(_images(_analysis_call(client))) == 5


def test_triage_dedups_near_duplicate_rooms_before_analysis():
    # Twenty photos, sixteen of them kitchens: triage keeps a few per room and
    # backfills to the cap rather than sending sixteen kitchens.
    rooms = ["kitchen"] * 16 + ["living", "bedroom", "yard", "exterior_front"]
    client = _Client(_VISION_JSON, triage_text=json.dumps({"rooms": rooms}))
    ClaudeVisionAnalyzer(client=client, fetch_image=_fail_fetch).analyze(
        _facts([f"https://x/p{i}.jpg" for i in range(20)])
    )

    models = [c["model"] for c in client.messages.calls]
    assert models == [DEFAULT_TRIAGE_MODEL, DEFAULT_ANALYSIS_MODEL]
    assert len(_images(_analysis_call(client))) == 15


def test_triage_parse_failure_falls_back_to_simple_cap():
    client = _Client(_VISION_JSON, triage_text="not json")
    ClaudeVisionAnalyzer(client=client, fetch_image=_fail_fetch).analyze(
        _facts([f"https://x/p{i}.jpg" for i in range(20)])
    )

    assert len(_images(_analysis_call(client))) == 15


def test_triage_can_be_disabled():
    client = _Client(_VISION_JSON, triage_text=json.dumps({"rooms": ["kitchen"] * 20}))
    ClaudeVisionAnalyzer(client=client, fetch_image=_fail_fetch, enable_triage=False).analyze(
        _facts([f"https://x/p{i}.jpg" for i in range(20)])
    )

    assert [c["model"] for c in client.messages.calls] == [DEFAULT_ANALYSIS_MODEL]
    assert len(_images(_analysis_call(client))) == 15


def test_analyze_handles_code_fenced_json():
    result = _analyzer(f"```json\n{_VISION_JSON}\n```").analyze(_facts(["https://x/a.jpg"]))
    assert len(result.photos) == 2


def test_vision_output_feeds_scoring_engine():
    observations = _analyzer(_VISION_JSON).analyze(_facts(["https://x/a.jpg"]))
    rubric = Rubric(
        version="1.0",
        category_weights=CategoryWeights(bones=15, warmth=25, finish=20, outdoor=25, value=10, age=5),
        item_weights={"tone_warmth": 15.0, "interior_style": 10.0, "exterior_style": 15.0, "curb_appeal": 10.0},
        directions=RubricDirections(tone="warm", era="traditional", ornament="ornate", naturalness="natural"),
        archetype=RubricArchetype(name="x", blend={"x": 1.0}),
        confidence={},
    )
    result = score(rubric, observations, _facts(["https://x/a.jpg"]))
    assert result.gate == "pass"
    assert result.total > 0


def test_build_user_prompt_includes_style_vocab():
    prompt = build_user_prompt(3)
    assert "farmhouse" in prompt
    assert "room_type" in prompt


def test_build_triage_prompt_lists_room_vocab_and_count():
    prompt = build_triage_prompt(7)
    assert "7 photographs" in prompt
    assert "exterior_front" in prompt


def test_resolve_analyzer_uses_stub_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert isinstance(resolve_analyzer(), StubAnalyzer)


def test_resolve_analyzer_uses_vision_with_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert isinstance(resolve_analyzer(), ClaudeVisionAnalyzer)

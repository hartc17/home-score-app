from app.photos.analyzer import (
    SCHEMA_VERSION,
    ListingObservations,
    StubAnalyzer,
    analyze_photoset,
    clear_cache,
    photoset_hash,
)
from app.schemas import ListingFacts


def _facts(photo_urls) -> ListingFacts:
    return ListingFacts(url="https://example.com", photo_urls=photo_urls)


def test_photoset_hash_is_order_independent():
    assert photoset_hash(["a.jpg", "b.jpg"]) == photoset_hash(["b.jpg", "a.jpg"])


def test_photoset_hash_differs_for_different_sets():
    assert photoset_hash(["a.jpg"]) != photoset_hash(["a.jpg", "b.jpg"])


def test_analyze_photoset_caches_by_hash():
    clear_cache()

    class CountingAnalyzer:
        model = "counting"

        def __init__(self):
            self.calls = 0

        def analyze(self, facts):
            self.calls += 1
            return ListingObservations(
                photos=[], flags=[], model=self.model, schema_version=SCHEMA_VERSION
            )

    analyzer = CountingAnalyzer()
    facts = _facts(["x.jpg", "y.jpg"])
    analyze_photoset(facts, analyzer)
    analyze_photoset(facts, analyzer)

    assert analyzer.calls == 1


def test_stub_analyzer_flags_vision_unconfigured():
    result = StubAnalyzer().analyze(_facts(["x.jpg"]))
    assert result.photos == []
    assert "vision_unconfigured" in result.flags
    assert result.schema_version == SCHEMA_VERSION

from __future__ import annotations

import hashlib
import os
from typing import Protocol

from app.schemas import ListingFacts, ListingObservations

SCHEMA_VERSION = "1.0"


def photoset_hash(photo_urls: list[str]) -> str:
    joined = "\n".join(sorted(photo_urls))
    return hashlib.sha256(joined.encode()).hexdigest()


class Analyzer(Protocol):
    model: str

    def analyze(self, facts: ListingFacts) -> ListingObservations: ...


class StubAnalyzer:
    # Honest placeholder: emits no observations and flags that vision is not wired.
    # Real analysis is blocked on scoring-contract.md (the preference-neutral vision
    # prompt + observation schema). Swapping in a real analyzer is a one-line change
    # at the analyze_photoset call site.
    model = "stub"

    def analyze(self, facts: ListingFacts) -> ListingObservations:
        return ListingObservations(
            photos=[],
            overall_tone_warmth=None,
            condition_summary=None,
            flags=["vision_unconfigured"],
            model=self.model,
            schema_version=SCHEMA_VERSION,
        )


def resolve_analyzer() -> Analyzer:
    # Use real Claude vision when configured, otherwise the honest stub.
    if os.environ.get("ANTHROPIC_API_KEY"):
        from app.photos.vision import ClaudeVisionAnalyzer

        return ClaudeVisionAnalyzer()
    return StubAnalyzer()


_CACHE: dict[str, ListingObservations] = {}
_CACHE_MAX_ENTRIES = 512


def analyze_photoset(facts: ListingFacts, analyzer: Analyzer | None = None) -> ListingObservations:
    active = analyzer if analyzer is not None else resolve_analyzer()
    key = f"{active.model}:{photoset_hash(facts.photo_urls)}"
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    result = active.analyze(facts)
    _CACHE[key] = result
    if len(_CACHE) > _CACHE_MAX_ENTRIES:
        del _CACHE[next(iter(_CACHE))]
    return result


def clear_cache() -> None:
    _CACHE.clear()

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "scoring_config.json"


@dataclass(frozen=True)
class ScoringConfig:
    confidence_threshold: float
    unknown_match_default: float
    min_coverage_categories: int
    tax_rate_flag: float
    verdict_tiers: list[tuple[float, str]]
    value_bands: list[tuple[float, float]]
    item_category: dict[str, str]
    continuous_items: set[str]
    always_higher_better: set[str]
    continuous_ranges: dict[str, tuple[float, float]]
    categorical_governed_by: dict[str, dict]
    categorical_match: dict[str, dict[str, dict[str, float]]]


@lru_cache(maxsize=1)
def get_config() -> ScoringConfig:
    raw = json.loads(_CONFIG_PATH.read_text())
    return ScoringConfig(
        confidence_threshold=raw["confidence_threshold"],
        unknown_match_default=raw["unknown_match_default"],
        min_coverage_categories=raw["min_coverage_categories"],
        tax_rate_flag=raw["tax_rate_flag"],
        verdict_tiers=[(float(t), v) for t, v in raw["verdict_tiers"]],
        value_bands=[(float(a), float(b)) for a, b in raw["value_bands"]],
        item_category=raw["item_category"],
        continuous_items=set(raw["continuous_items"]),
        always_higher_better=set(raw["always_higher_better"]),
        continuous_ranges={k: (float(a), float(b)) for k, (a, b) in raw["continuous_ranges"].items()},
        categorical_governed_by=raw["categorical_governed_by"],
        categorical_match=raw["categorical_match"],
    )

from __future__ import annotations

from app.schemas import ListingFacts, ListingObservations, ObservationItem, Rubric, RubricDirections
from app.schemas import ScoreResult
from app.scoring.config import ScoringConfig, get_config

# Categories scored from photo observations. `value` comes from facts (MVP stub);
# `age` is deferred until a facts-based age model lands, so it is excluded from the
# total rather than counted as zero (which would silently cap every score).
OBSERVED_CATEGORIES = ["bones", "warmth", "finish", "outdoor"]


def _fmt(value: float | str) -> str:
    return f"{value:g}" if isinstance(value, (int, float)) else str(value)


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _match_continuous(item_key: str, value: float, directions: RubricDirections, cfg: ScoringConfig) -> float:
    lo, hi = cfg.continuous_ranges.get(item_key, (0.0, 10.0))
    scaled = _clamp((value - lo) / (hi - lo)) if hi > lo else 0.0
    if item_key in cfg.always_higher_better:
        return scaled
    # Bipolar continuous axis (tone_warmth): the direction flips the match, and
    # nothing else does. An unstated direction expresses no preference.
    direction = directions.tone
    if direction == "warm":
        return scaled
    if direction == "cool":
        return 1.0 - scaled
    return 0.5


def _match_categorical(item_key: str, obs: str, directions: RubricDirections, cfg: ScoringConfig) -> float:
    gov = cfg.categorical_governed_by.get(item_key)
    table = cfg.categorical_match.get(item_key, {})
    pref: str | None = None
    if gov is not None:
        axis = gov.get("axis")
        if axis:
            dval = getattr(directions, axis, None)
            pref = gov.get("map", {}).get(dval, gov["default"])
        else:
            pref = gov["default"]
    row = table.get(pref) if pref is not None else None
    if row is None:
        row = next(iter(table.values()), {})
    return row.get(obs, cfg.unknown_match_default)


def _match(item_key: str, value: float | str, directions: RubricDirections, cfg: ScoringConfig) -> float | None:
    if item_key in cfg.continuous_items and isinstance(value, (int, float)):
        return _match_continuous(item_key, float(value), directions, cfg)
    if isinstance(value, str):
        return _match_categorical(item_key, value, directions, cfg)
    return None


def _taste_vector(directions: RubricDirections, cfg: ScoringConfig) -> dict[str, float]:
    # The buyer's point in style-axis space, built only from stated directions.
    # An axis with no stated direction is absent, so it imposes nothing.
    vec: dict[str, float] = {}
    for field, spec in cfg.direction_to_axis.items():
        value = getattr(directions, field, None)
        if value is None:
            continue
        mapped = spec["map"].get(value)
        if mapped is not None:
            vec[spec["axis"]] = float(mapped)
    return vec


def _style_match(style: str, taste: dict[str, float], cfg: ScoringConfig) -> float | None:
    coords = cfg.style_coordinates.get(style)
    if coords is None:
        return None
    axes = [a for a in taste if a in coords]
    if not axes:
        return None
    return sum(1.0 - abs(taste[a] - coords[a]) / 2.0 for a in axes) / len(axes)


def _classifications(value: object, confidence: float) -> list[tuple[str, float]]:
    if isinstance(value, list):
        return [(c.style, c.confidence) for c in value]
    if isinstance(value, str):
        return [(value, confidence)]
    return []


def _style_affinity(item: ObservationItem, taste: dict[str, float], cfg: ScoringConfig) -> float | None:
    if not taste:
        return None
    num = 0.0
    den = 0.0
    for style, conf in _classifications(item.value, item.confidence):
        match = _style_match(style, taste, cfg)
        if match is None:
            continue
        num += match * conf
        den += conf
    return (num / den) if den > 0 else None


def _top_style(item: ObservationItem) -> str:
    classes = _classifications(item.value, item.confidence)
    if not classes:
        return "unknown"
    return max(classes, key=lambda c: c[1])[0]


def _check_gates(facts: ListingFacts, rubric: Rubric) -> tuple[str, str | None]:
    gates = rubric.gates
    if gates is None:
        return "pass", None
    if facts.price is not None and facts.price > gates.budget_max:
        return "disqualified", f"price {facts.price:g} exceeds budget_max {gates.budget_max:g}"
    if facts.beds is not None and facts.beds < gates.min_beds:
        return "disqualified", f"beds {facts.beds:g} < min_beds {gates.min_beds:g}"
    if facts.baths is not None and facts.baths < gates.min_baths:
        return "disqualified", f"baths {facts.baths:g} < min_baths {gates.min_baths:g}"
    if facts.garage is not None and facts.garage < gates.min_garage:
        return "disqualified", f"garage {facts.garage:g} < min_garage {gates.min_garage:g}"
    if gates.home_types and facts.home_type and facts.home_type not in gates.home_types:
        return "disqualified", f"home_type {facts.home_type!r} not in {gates.home_types}"
    return "pass", None


def _value_fraction(facts: ListingFacts, rubric: Rubric) -> float | None:
    # MVP stub: headroom against the stated budget only. The reno estimator will
    # later supply an all-in cost that replaces this seam (see docs/plans).
    gates = rubric.gates
    if gates is None or facts.price is None or gates.budget_max <= 0:
        return None
    headroom = facts.price / gates.budget_max
    for threshold, frac in get_config().value_bands:
        if headroom <= threshold:
            return frac
    return 0.5


def _verdict(total: float, cfg: ScoringConfig) -> str:
    for threshold, name in cfg.verdict_tiers:
        if total >= threshold:
            return name
    return cfg.verdict_tiers[-1][1]


def _flatten(observations: ListingObservations) -> tuple[dict[str, ObservationItem], set[str]]:
    observed: dict[str, ObservationItem] = {}
    missing: set[str] = set()
    for photo in observations.photos:
        for key, item in photo.observations.items():
            if item.not_observed or item.value is None:
                missing.add(key)
            else:
                observed[key] = item
    tone = observations.overall_tone_warmth
    if tone is not None and not tone.not_observed and tone.value is not None:
        observed["tone_warmth"] = tone
    return observed, {k for k in missing if k not in observed}


def _disqualified(reason: str | None, observations: ListingObservations) -> ScoreResult:
    return ScoreResult(
        gate="disqualified",
        disqualified_reason=reason,
        category_scores={},
        total=0.0,
        verdict="weak",
        flags=observations.flags,
        dd_items=[],
        observation_trace={},
    )


def score(
    rubric: Rubric,
    observations: ListingObservations,
    facts: ListingFacts,
) -> ScoreResult:
    cfg = get_config()
    gate_status, reason = _check_gates(facts, rubric)
    if gate_status == "disqualified":
        return _disqualified(reason, observations)

    observed, missing = _flatten(observations)
    taste = _taste_vector(rubric.directions, cfg)

    trace: dict[str, str] = {}
    dd_items: list[str] = []
    cat_num: dict[str, float] = {c: 0.0 for c in OBSERVED_CATEGORIES}
    cat_den: dict[str, float] = {c: 0.0 for c in OBSERVED_CATEGORIES}

    for item_key, weight in rubric.item_weights.items():
        category = cfg.item_category.get(item_key)
        if category is None:
            continue
        if item_key not in observed:
            if item_key in missing:
                dd_items.append(f"Verify {item_key}: not visible in the available photos")
            continue
        item = observed[item_key]
        if item_key in cfg.style_items:
            match = _style_affinity(item, taste, cfg)
            described = _top_style(item)
        else:
            match = _match(item_key, item.value, rubric.directions, cfg)
            described = _fmt(item.value)
        if match is None:
            continue
        cat_num[category] += match * weight
        cat_den[category] += weight
        # Frozen confidence rule: score at the observed value regardless of
        # confidence, and add a verify item when confidence is below threshold.
        if item.confidence < cfg.confidence_threshold:
            dd_items.append(
                f"Verify {item_key}: observed {described} at low confidence ({item.confidence:.2f})"
            )
        if item.flag:
            dd_items.append(f"Verify {item_key}: {item.flag}")
        trace[item_key] = (
            f"match {match:.2f} x weight {weight:g} = {match * weight:.2f} "
            f"(obs {described}, conf {item.confidence:.2f})"
        )

    weights = rubric.category_weights
    category_scores: dict[str, float] = {}
    total_num = 0.0
    total_den = 0.0
    assessed = 0

    for category in OBSERVED_CATEGORIES:
        if cat_den[category] <= 0:
            continue
        fraction = cat_num[category] / cat_den[category]
        weight = getattr(weights, category)
        category_scores[category] = round(fraction * weight, 2)
        trace[category] = f"{category_scores[category]:g} / {weight:g} ({int(round(fraction * 100))}% match)"
        total_num += fraction * weight
        total_den += weight
        assessed += 1

    value_fraction = _value_fraction(facts, rubric)
    if value_fraction is not None:
        weight = weights.value
        category_scores["value"] = round(value_fraction * weight, 2)
        trace["value"] = f"{category_scores['value']:g} / {weight:g} (headroom vs budget)"
        total_num += value_fraction * weight
        total_den += weight
        assessed += 1
        if facts.taxes_annual and facts.price and facts.taxes_annual / facts.price > cfg.tax_rate_flag:
            dd_items.append("Verify tax assessment: annual taxes look high relative to list price")

    total = round(100.0 * total_num / total_den, 2) if total_den > 0 else 0.0

    if 0 < assessed < cfg.min_coverage_categories:
        dd_items.append(
            f"Score is based on partial evidence: only {assessed} of the taste categories could be assessed"
        )

    return ScoreResult(
        gate="pass",
        category_scores=category_scores,
        total=total,
        verdict=_verdict(total, cfg),
        flags=observations.flags,
        dd_items=dd_items,
        observation_trace=trace,
    )

from __future__ import annotations

from app.schemas import ListingFacts, ListingObservations, Rubric, ScoreResult

CATEGORICAL_MATCH: dict[str, dict[str, dict[str, float]]] = {
    "flooring": {
        "hardwood": {"hardwood": 1.0, "tile": 0.6, "laminate": 0.4, "vinyl": 0.3, "carpet": 0.2},
        "tile": {"tile": 1.0, "hardwood": 0.6, "laminate": 0.4, "vinyl": 0.3, "carpet": 0.2},
    },
    "fireplace": {
        "wood": {"wood": 1.0, "unverified_wood": 0.7, "gas": 0.5, "electric": 0.2, "none": 0.0},
        "none": {"none": 1.0, "electric": 0.8, "gas": 0.6, "wood": 0.3, "unverified_wood": 0.3},
    },
    "counters": {
        "quartz": {"quartz": 1.0, "marble": 0.9, "granite": 0.8, "tile": 0.4, "laminate": 0.2},
        "granite": {"granite": 1.0, "quartz": 0.8, "marble": 0.8, "tile": 0.4, "laminate": 0.2},
    },
    "cabinets": {
        "painted_white": {
            "painted_white": 1.0,
            "painted_color": 0.5,
            "wood_stained": 0.4,
            "dated": 0.1,
        },
        "wood_stained": {
            "wood_stained": 1.0,
            "painted_white": 0.5,
            "painted_color": 0.4,
            "dated": 0.2,
        },
    },
    "appliances": {
        "stainless": {"stainless": 1.0, "black": 0.6, "white": 0.4, "mixed": 0.3},
        "white": {"white": 1.0, "stainless": 0.5, "black": 0.4, "mixed": 0.3},
    },
    "exterior_style": {
        "farmhouse": {
            "farmhouse": 1.0,
            "craftsman": 0.7,
            "colonial": 0.5,
            "ranch": 0.4,
            "modern": 0.2,
            "tudor": 0.3,
            "cape_cod": 0.5,
        },
        "modern": {
            "modern": 1.0,
            "ranch": 0.5,
            "craftsman": 0.3,
            "colonial": 0.2,
            "farmhouse": 0.1,
            "tudor": 0.1,
            "cape_cod": 0.2,
        },
    },
}

CONTINUOUS_ITEMS = {"tone_warmth", "natural_light", "condition", "curb_appeal", "ceiling_height"}

ITEM_CATEGORY: dict[str, str] = {
    "tone_warmth": "warmth",
    "fireplace": "warmth",
    "flooring": "finish",
    "counters": "finish",
    "cabinets": "finish",
    "appliances": "finish",
    "natural_light": "finish",
    "condition": "finish",
    "ceiling_height": "bones",
    "curb_appeal": "outdoor",
    "exterior_style": "outdoor",
    "lot_character": "outdoor",
    "deck_patio": "outdoor",
}

CATEGORY_BUDGETS: dict[str, float] = {
    "bones": 25.0,
    "warmth": 20.0,
    "finish": 20.0,
    "outdoor": 15.0,
    "value": 10.0,
    "age": 10.0,
}

ITEM_CATEGORY: dict[str, str] = {
    "ceiling_height": "bones",
    "natural_light": "bones",
    "tone_warmth": "warmth",
    "fireplace": "warmth",
    "flooring": "finish",
    "counters": "finish",
    "cabinets": "finish",
    "appliances": "finish",
    "condition": "finish",
    "curb_appeal": "outdoor",
    "lot_character": "outdoor",
    "deck_patio": "outdoor",
    "garage_type": "outdoor",
    "exterior_style": "outdoor",
}


def _match_continuous(value: float, direction: str | None, item_key: str) -> float:
    if direction == "warm" or item_key in {"natural_light", "curb_appeal", "condition"}:
        return max(0.0, min(1.0, value / 10.0))
    if direction == "cool":
        return max(0.0, min(1.0, (10.0 - value) / 10.0))
    return max(0.0, min(1.0, value / 10.0))


def _match_categorical(item_key: str, obs_value: str, direction: str | None) -> float:
    preferred = direction or ""
    table = CATEGORICAL_MATCH.get(item_key, {})
    row = table.get(preferred, {})
    return row.get(obs_value, 0.5)


def _check_gates(facts: ListingFacts, rubric: Rubric) -> tuple[str, str | None]:
    gates = rubric.gates
    if gates is None:
        return "pass", None

    if facts.price is not None and facts.price > gates.budget_max:
        return "disqualified", f"price {facts.price} exceeds budget_max {gates.budget_max}"

    if facts.beds is not None and facts.beds < gates.min_beds:
        return "disqualified", f"beds {facts.beds} < min_beds {gates.min_beds}"

    if facts.baths is not None and facts.baths < gates.min_baths:
        return "disqualified", f"baths {facts.baths} < min_baths {gates.min_baths}"

    if facts.garage is not None and facts.garage < gates.min_garage:
        return "disqualified", f"garage {facts.garage} < min_garage {gates.min_garage}"

    if gates.home_types and facts.home_type and facts.home_type not in gates.home_types:
        return "disqualified", f"home_type {facts.home_type!r} not in {gates.home_types}"

    return "pass", None


def _verdict(total: float) -> str:
    if total >= 80:
        return "pursue"
    if total >= 65:
        return "showing"
    if total >= 50:
        return "conditional"
    return "weak"


def score(
    rubric: Rubric,
    observations: ListingObservations,
    facts: ListingFacts,
) -> ScoreResult:
    gate_status, disqualified_reason = _check_gates(facts, rubric)

    if gate_status == "disqualified":
        return ScoreResult(
            gate="disqualified",
            disqualified_reason=disqualified_reason,
            category_scores={k: 0.0 for k in CATEGORY_BUDGETS},
            total=0.0,
            verdict="weak",
            flags=observations.flags,
            dd_items=[],
            observation_trace={},
        )

    flat_obs: dict[str, tuple[float | str | None, float]] = {}
    for photo in observations.photos:
        for key, item in photo.observations.items():
            if not item.not_observed and item.value is not None:
                flat_obs[key] = (item.value, item.confidence)

    if observations.overall_tone_warmth and not observations.overall_tone_warmth.not_observed:
        flat_obs["tone_warmth"] = (
            observations.overall_tone_warmth.value,
            observations.overall_tone_warmth.confidence,
        )

    trace: dict[str, str] = {}
    item_contribs: dict[str, float] = {}

    for item_key, weight in rubric.item_weights.items():
        if item_key not in flat_obs:
            continue
        obs_value, confidence = flat_obs[item_key]
        direction = getattr(rubric.directions, item_key.replace("tone_warmth", "tone"), None)
        if direction is None and item_key == "tone_warmth":
            direction = rubric.directions.tone

        if item_key in CONTINUOUS_ITEMS and isinstance(obs_value, (int, float)):
            match = _match_continuous(float(obs_value), direction, item_key)
        elif isinstance(obs_value, str):
            match = _match_categorical(item_key, obs_value, direction)
        else:
            continue

        contrib = match * weight * confidence
        item_contribs[item_key] = contrib
        trace[item_key] = f"match={match:.3f} weight={weight} conf={confidence:.2f} contrib={contrib:.3f}"

    category_item_map: dict[str, list[str]] = {cat: [] for cat in CATEGORY_BUDGETS}
    for item_key in item_contribs:
        cat = ITEM_CATEGORY.get(item_key, "finish")
        category_item_map[cat].append(item_key)

    category_scores: dict[str, float] = {}
    for cat, budget in CATEGORY_BUDGETS.items():
        raw = sum(item_contribs.get(k, 0.0) for k in category_item_map[cat])
        category_scores[cat] = min(raw, budget)

    total = sum(category_scores.values())

    return ScoreResult(
        gate="pass",
        category_scores=category_scores,
        total=round(total, 2),
        verdict=_verdict(total),
        flags=observations.flags,
        dd_items=[],
        observation_trace=trace,
    )

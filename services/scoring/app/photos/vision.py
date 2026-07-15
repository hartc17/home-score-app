from __future__ import annotations

import json
import os
from typing import Any

from app.photos.analyzer import SCHEMA_VERSION
from app.schemas import (
    ListingFacts,
    ListingObservations,
    ObservationItem,
    PhotoObservations,
    StyleClassification,
)
from app.scoring.config import get_config

# The real Claude vision analyzer, implemented against docs/scoring-contract.md.
# It is gated on ANTHROPIC_API_KEY: without a key the service falls back to the
# stub (see app/photos/analyzer.resolve_analyzer). Photos are passed by URL and
# capped in count; resizing to a ~1300px long edge and the cheap triage-model
# dedup pass (contract section 8) are seams left for a follow-up.

MAX_PHOTOS = 15
DEFAULT_ANALYSIS_MODEL = "claude-opus-4-8"
DEFAULT_TRIAGE_MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = (
    "You are a real estate photo analyst. You report only what is visible in the "
    "photographs, as neutral observations and ratings. You never judge whether a "
    "feature is desirable, attractive, or valuable, because different buyers want "
    "different things. You return a single JSON object conforming to the schema you "
    "are given, and nothing else. Every finding includes a confidence from 0 to 1. "
    "If a feature is not visible, mark it not_observed with a flag rather than "
    "guessing. If a fireplace cannot be confirmed as wood-burning, report "
    "unverified_wood with low confidence and a flag. Any value inferred from "
    "perspective rather than measured is flagged as estimated."
)

_SCHEMA_HINT = """
Return one JSON object:
{
  "schema_version": "1.0",
  "photos": [
    {
      "room_type": "living | kitchen | dining | bedroom | bathroom | exterior_front | exterior_rear | yard | other",
      "observations": {
        // Each leaf is { "value": ..., "confidence": 0-1, "not_observed"?: bool, "flag"?: string }.
        // Scalars are 0-10 unless noted. Style values are a list of {"style","confidence"}.
        "interior_style"?: [{"style": "...", "confidence": 0-1}],   // interior photos
        "exterior_style"?: [{"style": "...", "confidence": 0-1}],   // exterior photos (architectural style)
        "tone_warmth"?: 0-10 (0 cool .. 10 warm),
        "natural_light"?: 0-10,
        "ornamentation"?: 0-10 (0 minimal .. 10 ornate),
        "wall_lightness"?: 0-10 (0 dark .. 10 light),
        "ceiling_height"?: feet,
        "condition"?: 0-10,
        "flooring"?: "hardwood|engineered_wood|tile|stone|laminate|vinyl|carpet|concrete",
        "counters"?: "quartz|granite|marble|butcher_block|tile|laminate|concrete|stainless",
        "cabinets"?: "painted_white|painted_color|wood_stained|wood_natural|dated|flat_slab|shaker",
        "appliances"?: "stainless|white|black|panel_integrated|mixed|dated",
        "fireplace"?: "wood|gas|electric|none|unverified_wood",
        "curb_appeal"?: 0-10,
        "roof_type"?: "gable|hip|flat|low_slope|gambrel|mansard|complex",
        "siding_material"?: "board_and_batten|shiplap|clapboard|brick|stone|stucco|vinyl|shingle|fiber_cement|mixed",
        "lot_character"?: "wooded|landscaped|open|minimal|waterfront",
        "deck_patio"?: "deck_wood|deck_composite|patio_stone|patio_concrete|none",
        "garage_type"?: "attached|detached|carport|none"
      }
    }
  ],
  "overall_tone_warmth"?: {"value": 0-10, "confidence": 0-1},
  "overall_style"?: {"value": [{"style": "...", "confidence": 0-1}], "confidence": 0-1},
  "condition_summary"?: {"value": 0-10, "confidence": 0-1},
  "flags": ["..."]
}
Return only the JSON object.
""".strip()


def build_user_prompt(photo_count: int) -> str:
    styles = ", ".join(sorted(get_config().style_coordinates.keys()))
    return (
        f"Analyze these {photo_count} photographs of one listing. "
        "For each photo, identify the room_type and report the observations that apply to that room. "
        "Classify architectural style on exterior photos and interior style on interior photos, "
        "returning the top one to three styles with confidence rather than a single label. "
        "Use only the enumerations provided.\n\n"
        f"Allowed style values: {styles}\n\n"
        f"{_SCHEMA_HINT}"
    )


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    return text[start : end + 1] if start != -1 and end != -1 else text


def _to_item(raw: dict[str, Any]) -> ObservationItem:
    value = raw.get("value")
    if isinstance(value, list):
        value = [
            StyleClassification(style=s["style"], confidence=float(s["confidence"]))
            for s in value
            if isinstance(s, dict) and "style" in s and "confidence" in s
        ]
    return ObservationItem(
        value=value,
        confidence=float(raw.get("confidence", 0.0)),
        not_observed=raw.get("not_observed"),
        flag=raw.get("flag"),
    )


def _opt_item(data: dict[str, Any], key: str) -> ObservationItem | None:
    raw = data.get(key)
    return _to_item(raw) if isinstance(raw, dict) else None


class ClaudeVisionAnalyzer:
    def __init__(
        self,
        analysis_model: str | None = None,
        triage_model: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = analysis_model or os.environ.get("HOUSEFLAVOR_VISION_MODEL", DEFAULT_ANALYSIS_MODEL)
        self.triage_model = triage_model or os.environ.get("HOUSEFLAVOR_TRIAGE_MODEL", DEFAULT_TRIAGE_MODEL)
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            from anthropic import Anthropic

            self._client = Anthropic()
        return self._client

    def _select_photos(self, photo_urls: list[str]) -> list[str]:
        # Cap count. The cheap triage-model pass that drops near-duplicate rooms
        # (contract section 8) plugs in here.
        return photo_urls[:MAX_PHOTOS]

    def analyze(self, facts: ListingFacts) -> ListingObservations:
        photos = self._select_photos(facts.photo_urls)
        if not photos:
            return ListingObservations(
                photos=[], flags=["no_photos"], model=self.model, schema_version=SCHEMA_VERSION
            )
        content: list[dict[str, Any]] = [
            {"type": "image", "source": {"type": "url", "url": url}} for url in photos
        ]
        content.append({"type": "text", "text": build_user_prompt(len(photos))})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )
        return self._parse(response, len(photos))

    def _parse(self, response: Any, photo_count: int) -> ListingObservations:
        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        data = json.loads(_extract_json(text))
        photos = [
            PhotoObservations(
                room_type=p.get("room_type", "other"),
                observations={k: _to_item(v) for k, v in p.get("observations", {}).items() if isinstance(v, dict)},
            )
            for p in data.get("photos", [])
            if isinstance(p, dict)
        ]
        return ListingObservations(
            photos=photos,
            overall_tone_warmth=_opt_item(data, "overall_tone_warmth"),
            overall_style=_opt_item(data, "overall_style"),
            condition_summary=_opt_item(data, "condition_summary"),
            flags=[f for f in data.get("flags", []) if isinstance(f, str)],
            model=getattr(response, "model", self.model),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )

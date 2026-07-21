# Scoring Contract

_Version 1.0. The authoritative specification for how HouseFlavor turns a listing plus a personal rubric into a score._

This document is the single source of truth for three things:
the preference-neutral vision prompt and the observation schema it returns (section 5),
the match and weight mapping that converts observations plus a rubric into a score (section 6),
and the vocabulary of architectural and interior styles the system reasons about (section 4).

It supersedes the provisional tables currently in `services/scoring/app/scoring/scoring_config.json`.
Section 10 reconciles this contract with what the code implements today.

## 1. Hard invariants

These are not negotiable, because the product's credibility depends on them.

The vision layer is preference-agnostic.
It reports what is present, never whether it is desirable, and it returns the same observations for every user looking at the same photo.
It emits observations and ratings, never scores.

All personalization enters through exactly one door: the rubric.
No taste is ever hardcoded into a prompt, a match function, or a default.
If you can point to a specific buyer's preference baked into the vision prompt or a match table, that is a bug.

The vision layer returns JSON only, conforming to the schema in section 5.
Every finding carries a confidence in the range 0 to 1.
Unseen features are reported as `not_observed` with a flag, never guessed.

## 2. The two layers

A listing is judged on two independent layers.

The objective layer is the set of stated hard facts: budget, bed and bath counts, garage, home type, location, and similar.
These are knowledge the buyer states directly, so the system asks for them and never infers them.
They act as gates: a listing that fails any active gate is disqualified before any style scoring runs.

The subjective layer is taste: the style a buyer is drawn to, inferred from image-only forced choices in the quiz.
Taste never disqualifies a listing.
It only moves the score up or down through match times weight math.

The rubric is the artifact that carries both layers.
Its `gates` field holds the objective layer.
Its `category_weights`, `item_weights`, `directions`, `archetype`, and `confidence` fields hold the subjective layer.

## 3. Objective layer: gates and fact-derived factors

### 3.1 Hard gates

A hard gate disqualifies a listing when it fails.
Gates are only enforced when the buyer has set them; an unset gate never disqualifies.

| Gate | Rule | Source | Implemented |
|---|---|---|---|
| `budget_max` | list price must be at most budget | facts.price | yes |
| `min_beds` | bedrooms at least the minimum | facts.beds | yes |
| `min_baths` | bathrooms at least the minimum | facts.baths | yes |
| `min_garage` | garage spaces at least the minimum | facts.garage | yes |
| `home_types` | home type is in the allowed set | facts.home_type | yes |
| `districts` | listing is in an allowed district | facts.address or coords | planned |
| `exclude_main_road` | not on a main road when set | facts.road_class flag | planned |
| `min_sqft` | living area at least the minimum | facts.sqft | planned |
| `min_lot_sqft` | lot area at least the minimum | facts.lot_sqft | planned |

District and road-class checks depend on geospatial data that the MVP does not yet ingest, so they are stated and enforced only when the fact is present.
Until then a listing whose district cannot be determined passes the district gate and the uncertainty is recorded as a due-diligence item.

### 3.2 Fact-derived scored factors

Some facts are not pass or fail; they feed scored categories.

The `value` category is computed from facts only in the MVP.
It reads budget headroom (`list_price / budget_max`) in bands, price versus comparable sales when comps are parseable, and a tax-assessment sanity flag.
The reno estimator will later supply an all-in cost that replaces the headroom stub; the seam is reserved.

The `age` category is a facts-based model over `year_built`: the home's age against a configurable reference year maps through configurable bands to a fraction, so a newer home scores higher on age (a maintenance-risk proxy, not a taste signal), and a future `year_built` is treated as new construction.
It is excluded from the total when `year_built` is unknown, rather than scored as zero, so it never silently caps a score.
A home past the configured age threshold gets a due-diligence prompt to verify roof, HVAC, electrical, and plumbing.
Disclosed system ages are not yet parsed from listings, so folding them into the model (and any disclosed or visible system concerns) remains reserved.

Location, the single largest driver of real value, enters as gates (districts) plus due-diligence prompts, not as a taste score, because desirability of a location is buyer-stated, not inferred from photos.

## 4. Subjective layer: the style model

### 4.1 Taste axes

Taste is modeled as a small set of bipolar axes.
Each axis has two neutral poles and neither pole is framed as better.
A buyer's position on an axis is inferred from quiz consistency; an axis the buyer was indifferent on is left unset and imposes nothing.

Each axis runs from -1 at its negative pole to +1 at its positive pole.

| Axis | Negative pole (-1) | Positive pole (+1) | What it reads |
|---|---|---|---|
| `warmth` | cool | warm | color temperature, material warmth, light quality |
| `modernity` | traditional | modern | line, era of forms |
| `minimalism` | ornate | minimal | visual density, trim, decoration |
| `lightness` | dark | light | wall and finish value, airiness |
| `naturalness` | engineered | natural | wood, stone, fiber versus glass, metal, lacquer |

The style coordinate tables below use these same axes, so a positive `minimalism` value means a cleaner, less ornamented style.

The rubric carries a buyer's position as `directions`, and each direction field maps to one axis:
`tone` to `warmth` (warm is +1, cool is -1),
`era` to `modernity` (modern is +1, traditional is -1),
`walls` to `lightness` (white_preferred is +1, color_preferred is -1),
`ornament` to `minimalism` (minimal is +1, ornate is -1),
`naturalness` to `naturalness` (natural is +1, engineered is -1).
The MVP rubric implements `tone`, `era`, and `walls`; `ornament` and `naturalness` are defined for the quiz and scorer to grow into, and section 10 tracks the delta.

### 4.2 Architectural styles (exterior)

Each style is defined by concrete, photo-observable cues, and placed as a fixed point in the axis space of section 4.1.
The vision layer classifies; the style point plus the buyer's axis position determine match (section 6.3).
Coordinates are in the range -1 to 1 and live in config, so they are tunable without code change.

| Style | Key visible cues | warmth | modernity | minimalism | lightness | naturalness |
|---|---|---|---|---|---|---|
| `modern_farmhouse` | board-and-batten or shiplap siding, white or greige body, black window frames, gable roof, covered porch, metal roof accents | +0.6 | +0.2 | +0.2 | +0.7 | +0.6 |
| `craftsman` | low-pitched gable, deep eaves, exposed rafter tails, tapered porch columns, natural wood and stone, earthy tones | +0.8 | -0.6 | -0.3 | -0.2 | +0.9 |
| `colonial` | symmetrical facade, centered door flanked by equal windows, two stories, shutters, brick or clapboard | +0.2 | -0.8 | -0.2 | +0.2 | +0.3 |
| `ranch` | single story, long low profile, low-pitched roof, attached garage, picture windows or sliders | +0.3 | -0.1 | +0.2 | +0.1 | +0.2 |
| `tudor` | steep multi-gable roof, half-timbering, brick or stucco, tall narrow leaded windows, prominent chimney | +0.4 | -0.9 | -0.6 | -0.4 | +0.4 |
| `victorian` | asymmetrical, gingerbread trim, turrets, steep roofs, bold multi-color paint, wraparound porch | +0.3 | -1.0 | -1.0 | -0.2 | +0.2 |
| `midcentury_modern` | flat or low-slope roof, floor-to-ceiling glass, post-and-beam, clean geometry, indoor-outdoor flow | +0.4 | +0.7 | +0.4 | +0.3 | +0.5 |
| `contemporary` | asymmetric massing, mixed materials, large glazing, flat roofs, minimal ornament | 0.0 | +0.9 | +0.5 | +0.2 | 0.0 |
| `modern` | rectilinear volumes, expansive glass, monochrome, no applied ornament | -0.2 | +1.0 | +0.8 | +0.1 | -0.3 |
| `mediterranean` | stucco walls, red clay tile roof, arches, wrought iron, warm earth tones | +0.7 | -0.5 | -0.3 | +0.1 | +0.4 |
| `cape_cod` | one to one and a half stories, steep gable, central chimney, dormers, symmetrical, shingle or clapboard | +0.4 | -0.5 | +0.1 | +0.5 | +0.4 |
| `prairie` | strong horizontal lines, low hipped roof, wide eaves, bands of windows, earth tones | +0.4 | +0.2 | +0.1 | -0.1 | +0.7 |

### 4.3 Interior styles

Placed in the same axis space, classified from the same neutral cues.

| Style | Key visible cues | warmth | modernity | minimalism | lightness | naturalness |
|---|---|---|---|---|---|---|
| `modern` | clean lines, neutral palette, smooth surfaces, low furniture, minimal decor | -0.1 | +0.9 | +0.7 | +0.2 | -0.2 |
| `contemporary` | current forms, mix of curves and clean lines, neutral base with bold accents | 0.0 | +0.8 | +0.5 | +0.2 | 0.0 |
| `minimalist` | monochrome or neutral, decluttered, hidden storage, few objects | -0.2 | +0.8 | +1.0 | +0.4 | -0.1 |
| `traditional` | symmetry, rich dark woods, crown molding, classic patterns, warm palette | +0.5 | -0.8 | -0.6 | -0.1 | +0.4 |
| `transitional` | traditional forms softened toward modern, neutral, mixed textures | +0.2 | +0.1 | +0.2 | +0.2 | +0.2 |
| `farmhouse` | shiplap, reclaimed wood, apron sink, warm neutrals, vintage accents | +0.7 | -0.2 | -0.1 | +0.5 | +0.8 |
| `industrial` | exposed brick, concrete, ductwork, blackened metal, raw finishes | -0.3 | +0.4 | +0.1 | -0.7 | +0.3 |
| `scandinavian` | light wood, white walls, cozy textiles, bright and functional | +0.3 | +0.6 | +0.7 | +0.8 | +0.6 |
| `midcentury_modern` | teak or walnut, organic curves, tapered legs, retro accent colors, geometric | +0.5 | +0.6 | +0.3 | +0.2 | +0.6 |
| `coastal` | soft blues and whites, abundant light, rattan and linen, airy | +0.2 | +0.2 | +0.2 | +0.8 | +0.6 |
| `bohemian` | layered textiles, plants, eclectic global patterns, warm saturated color | +0.7 | -0.2 | -1.0 | -0.1 | +0.6 |
| `rustic` | rough timber, stone, wrought iron, heavy natural texture, dark warm tones | +0.8 | -0.5 | -0.4 | -0.3 | +0.9 |

### 4.4 Taste archetypes

The quiz snaps a buyer to a display archetype: a flattering identity plus a blend over the style vocabulary.
Each archetype sits at a region of the axis space; the blend names the two or three styles nearest that region.
Every archetype must read as desirable, per the neutrality words requirement.

| Archetype | Axis lean | Blend |
|---|---|---|
| The Hearthkeeper | warm, traditional, natural | farmhouse, craftsman |
| The Classicist | traditional, formal, detailed | colonial, traditional |
| The Warm Modernist | modern, warm, natural | midcentury_modern, contemporary |
| The Minimalist | cool, modern, minimal | modern, scandinavian |
| The Naturalist | warm, light, natural | scandinavian, coastal |
| The Curator | balanced across axes | transitional, midcentury_modern, farmhouse |

The archetype set is a fixed display set the rubric snaps to, not an emergent cluster, so copy and imagery can be curated per archetype.

## 5. Observation schema (vision output)

The vision layer returns one JSON object per listing.
It contains a `photos` array of per-photo observations plus listing-level rollups, a `flags` array, and provenance.
Every leaf observation is an object `{ value, confidence, not_observed?, flag? }`.

```jsonc
{
  "schema_version": "1.0",
  "model": "claude-...",           // which model produced this
  "photos": [
    {
      "room_type": "kitchen",       // living | kitchen | dining | bedroom | bathroom
                                    // | exterior_front | exterior_rear | yard | other
      "observations": {
        // Style classification: top styles with confidence, never a single guess.
        "interior_style": { "value": [ {"style": "farmhouse", "confidence": 0.7},
                                        {"style": "transitional", "confidence": 0.3} ],
                            "confidence": 0.7 },

        // Preference-neutral scalar readings, 0 to 10 unless noted.
        "tone_warmth": { "value": 8, "confidence": 0.9 },      // 0 cool ... 10 warm
        "natural_light": { "value": 7, "confidence": 0.9 },
        "ornamentation": { "value": 3, "confidence": 0.7 },    // 0 minimal ... 10 ornate
        "wall_lightness": { "value": 8, "confidence": 0.9 },   // 0 dark ... 10 light
        "ceiling_height": { "value": 9, "confidence": 0.5, "flag": "estimated_from_photo" },
        "condition": { "value": 8, "confidence": 0.8 },

        // Categorical materials and features (room-appropriate).
        "flooring": { "value": "hardwood", "confidence": 0.8 },
        "counters": { "value": "quartz", "confidence": 0.8 },   // kitchen / bath
        "cabinets": { "value": "painted_white", "confidence": 0.8 },
        "appliances": { "value": "stainless", "confidence": 0.9 },
        "fireplace": { "value": "unverified_wood", "confidence": 0.4, "flag": "wood_vs_gas_unverified" }
      }
    },
    {
      "room_type": "exterior_front",
      "observations": {
        "exterior_style": { "value": [ {"style": "modern_farmhouse", "confidence": 0.8} ],
                            "confidence": 0.8 },  // architectural style; the scored item key
        "curb_appeal": { "value": 8, "confidence": 0.8 },
        "roof_type": { "value": "gable", "confidence": 0.7 },
        "siding_material": { "value": "board_and_batten", "confidence": 0.8 },
        "symmetry": { "value": 6, "confidence": 0.6 },
        "lot_character": { "value": "landscaped", "confidence": 0.7 },
        "deck_patio": { "value": "patio_stone", "confidence": 0.6 },
        "garage_type": { "value": "attached", "confidence": 0.9 }
      }
    }
  ],
  // Listing-level rollups the scorer may prefer over per-photo values.
  "overall_tone_warmth": { "value": 7, "confidence": 0.8 },
  "overall_style": { "value": [ {"style": "farmhouse", "confidence": 0.6},
                                 {"style": "transitional", "confidence": 0.4} ], "confidence": 0.6 },
  "condition_summary": { "value": 8, "confidence": 0.8 },
  "flags": ["fireplace_wood_vs_gas_unverified", "district_not_determined"]
}
```

### 5.1 Enumerations

`flooring`: hardwood, engineered_wood, tile, stone, laminate, vinyl, carpet, concrete.
`counters`: quartz, granite, marble, butcher_block, tile, laminate, concrete, stainless.
`cabinets`: painted_white, painted_color, wood_stained, wood_natural, dated, flat_slab, shaker.
`appliances`: stainless, white, black, panel_integrated, mixed, dated.
`fireplace`: wood, gas, electric, none, unverified_wood.
`roof_type`: gable, hip, flat, low_slope, gambrel, mansard, complex.
`siding_material`: board_and_batten, shiplap, clapboard, brick, stone, stucco, vinyl, shingle, fiber_cement, mixed.
`lot_character`: wooded, landscaped, open, minimal, waterfront.
`deck_patio`: deck_wood, deck_composite, patio_stone, patio_concrete, none.
`garage_type`: attached, detached, carport, none.
`interior_style` and `exterior_style` values (exterior style is the architectural style) are drawn from the vocabularies in sections 4.2 and 4.3, and `exterior_style` is the key the engine scores.

### 5.2 Confidence and flag rules

Every finding carries a confidence in the range 0 to 1.
A feature that cannot be seen is `not_observed: true` with a flag, never guessed.
An ambiguous wood-versus-gas fireplace is reported as `unverified_wood` with low confidence and a flag, never resolved by assumption.
Any reading inferred rather than measured (for example ceiling height from perspective) is flagged as estimated.

## 6. Match and weight mapping

Scoring is deterministic.
The vision layer classifies and rates; this section turns those neutral outputs plus the rubric into a number.

### 6.1 Continuous axis match

A scalar observation becomes a match in 0 to 1, driven only by the rubric direction.
Let `s` be the reading scaled to 0 to 1 over its range.

For a bipolar axis item (for example `tone_warmth` on the `warmth` axis):
direction positive pole gives match `s`, direction negative pole gives match `1 - s`, no direction gives `0.5` (no preference).

For a quality item where higher is objectively better regardless of taste (for example `natural_light`, `condition`, `curb_appeal`): match is `s`.

### 6.2 Categorical material match

Material and feature categoricals use lookup tables in config, keyed by the governing direction where one applies (for example `cabinets` keyed by the `lightness` or `walls` direction), otherwise by a default quality ordering.
An unknown observed value returns a neutral 0.5.
These tables live in `scoring_config.json` so tuning never requires a redeploy.

### 6.3 Style-affinity match

Style is scored through the axis space, not a per-style preference list, so it stays preference-neutral and scales as the vocabulary grows.

Build the buyer's taste point `u` from `rubric.directions`, one coordinate per axis in section 4.1, using only axes the buyer has a stated direction on.
For a detected style with fixed point `p` (sections 4.2 and 4.3), the per-axis agreement is `1 - |u_i - p_i| / 2`, averaged over the buyer's stated axes, giving a style match in 0 to 1.
The vision layer returns a confidence-weighted list of styles, so the item match is the confidence-weighted average of the per-style matches.

This is preference-neutral machinery: style points are fixed, and only `u` is personal.

### 6.4 Aggregation, gates, verdict

Check gates first.
Any failed active gate disqualifies the listing with a recorded reason and no style scoring.

Otherwise, for each scored item, match times item weight accumulates into the item's category.
A category fraction is the item-weight-weighted average of its item matches.
The total is `100 times the sum over assessed categories of (category_fraction times category_weight), divided by the sum of those category weights`, so two rubrics with different directions or category weights produce different totals for the same observations.
Verdict tiers: 80 to 100 pursue, 65 to 79 showing, 50 to 64 conditional, under 50 weak.

### 6.5 Confidence handling and due diligence

Confidence uses a single threshold of 0.5.
A finding below the threshold is scored at its observed value and added to the due-diligence checklist as a verify item, with no silent value adjustment.
Findings that are `not_observed`, flagged, or classify a style at low confidence also become verify items.
Fact-side gaps (undetermined district, stale tax assessment, disclosed system age) join the same checklist.

## 7. The vision prompt

The prompt is preference-neutral and returns JSON only.
It is versioned with this document.

System prompt:

```
You are a real estate photo analyst. You report only what is visible in the
photographs, as neutral observations and ratings. You never judge whether a
feature is desirable, attractive, or valuable, because different buyers want
different things. You return a single JSON object conforming to the schema you
are given, and nothing else. Every finding includes a confidence from 0 to 1.
If a feature is not visible, mark it not_observed with a flag rather than
guessing. If a fireplace cannot be confirmed as wood-burning, report
unverified_wood with low confidence and a flag. Any value inferred from
perspective rather than measured is flagged as estimated.
```

User prompt (per listing):

```
Analyze these {n} photographs of one listing. For each photo, identify the
room_type and report the observations defined in the schema that apply to that
room. Classify architectural style on exterior photos and interior style on
interior photos, returning the top one to three styles with confidence rather
than a single label. Use only the enumerations provided. Then provide the
listing-level rollups. Return only the JSON object.

Schema: {schema}
Style vocabularies: {architectural_styles}, {interior_styles}
```

The schema and vocabularies are injected from this contract so prompt and scorer never drift.

## 8. Model strategy, caching, photo selection

Analysis is two-tier.
A cheaper model runs a triage pass to classify room types and drop near-duplicate photos.
A stronger model runs the full observation pass on the deduplicated set.

Photos are resized to a long edge near 1300 pixels and capped near 12 to 15, preferring one strong photo per room type over many of the same room.

Analysis is cached by a hash of the photo set, so re-scoring the same listing for the same or a different rubric costs nothing new.
The scorer is deterministic, so only the vision pass is ever billed.

## 9. Versioning and change control

This contract is versioned, and each stored analysis records the `schema_version` and `model` that produced it.
A change to the observation schema, the style vocabulary, or the axis definitions is a schema-version bump.
A change to a match table or a style coordinate is a config change, not a schema change, and does not invalidate stored observations.
Scores record the rubric version that produced them, so tuning never rewrites history.

## 10. Reconciliation with the current code

What matches this contract today:
the gate checks, the continuous and categorical match machinery, the category normalization, the verdict tiers, the frozen 0.5 confidence rule, and the photoset-hash cache seam;
the style-affinity match of section 6.3 with the style coordinate tables of sections 4.2 and 4.3 in `scoring_config.json`, applied to the `exterior_style` and `interior_style` items;
the `ornament` and `naturalness` direction fields in the rubric (`RubricDirections`) and the observation schema of section 5 in `packages/contracts` and the Pydantic models, including `StyleClassification` values, `interior_style`, `ornamentation`, and `wall_lightness`;
the quiz-side inference of all five taste axes, including `ornament` and `naturalness` (`apps/web/src/quiz/`), so a completed quiz emits every direction the scorer reads;
the Claude vision analyzer (`app/photos/vision.py`), which calls Claude with this section 7 prompt and parses the response into the section 5 schema, gated on `ANTHROPIC_API_KEY` with a stub fallback.

What this contract still adds, to be built:
the cheap triage-model dedup pass and image resizing of section 8 (the analyzer currently caps photo count and passes images by URL), plus an async analyzer call;
the district and road-class gates once geospatial data is ingested.

The engine reads style items via `style_items` in config, so a style observation whose value is a `StyleClassification` list is matched through the axis space rather than a fixed table.

## 11. Sources

Architectural style taxonomy and cues:
[Renoworks guide to 17 architectural styles](https://www.renoworks.com/design-inspiration/defining-types-of-houses-a-guide-to-17-architectural-styles/),
[Homes and Gardens: 20 iconic American house styles](https://www.homesandgardens.com/spaces/house-styles-architectural-eras-224060),
[Homes.com most popular house styles](https://www.homes.com/learn/most-popular-house-styles/).

Interior design style taxonomy and cues:
[Decorilla interior design styles 101](https://www.decorilla.com/online-decorating/interior-design-styles-101),
[Bobby Berk interior design styles guide](https://bobbyberk.com/whats-your-interior-design-style-a-breakdown-of-all-the-styles/).

Home value and resale factors:
[Redfin home resale value factors](https://www.redfin.com/blog/home-resale-value-factors/),
[Opendoor what determines property value](https://www.opendoor.com/articles/factors-that-influence-home-value).

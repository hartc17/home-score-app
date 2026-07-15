# Phase C - Scoring Service

Turn the three stubbed endpoints into a working chain: parse a pasted listing, analyze its photos with preference-neutral vision, and score it against a rubric.
This phase is the product's core, since the same listing must score differently for different rubrics.

## Goal

Implement `/listings/parse`, `/photos/analyze`, and `/score` so a pasted public listing URL returns a full score with an observation trace.
Keep the vision layer preference-agnostic and keep all personalization flowing through exactly one door, the rubric.

## Definition of done

A pasted URL returns a full score with an observation trace legible end to end (for example "Kitchen 2/7 - laminate counters, dated cabinets, white appliances").
Two different rubrics produce meaningfully different totals for the same listing.
Photo analysis is preference-neutral and JSON-only, with a `confidence` on every finding and flags for unseen or ambiguous features.
The value category is computed from facts only via the documented MVP stub, with a clean seam for the reno estimator later.
Any gate failure short-circuits to `DISQUALIFIED` with a recorded reason and no scoring.

## Dependencies and prerequisites

The pure scoring engine already exists at `services/scoring/app/scoring/engine.py` and already implements match-times-weight, gate checks, verdict tiers, and a trace.
The Pydantic schemas exist at `services/scoring/app/schemas.py` and mirror `packages/contracts`.
An Anthropic API key and model access are required for real vision, so the analyze endpoint must degrade to a deterministic fixture path in tests.

The companion `scoring-contract.md` is now written at `docs/scoring-contract.md` (vision prompt, observation schema, style vocabulary, and match mapping).
Reconcile the current `observation.ts` and Pydantic schemas with its section 5 schema when building the analyzer, since the current schema is an approximation.

## Known gaps in the current engine to fix in this phase

The engine hardcodes `CATEGORY_BUDGETS` in code and ignores the rubric's personalized `category_weights`.
The spec requires category weights to be personalized and to come from the rubric, so the engine must normalize using `rubric.category_weights` rather than a fixed budget table.
The `CATEGORICAL_MATCH` tables live in code, but the spec requires the categorical match tables in config so tuning does not require a redeploy.
Move them to a config file (for example JSON or TOML under the service) loaded at startup.
The value category is not yet computed and `dd_items` is always empty, both of which this phase must implement.
Sub-0.5 confidence findings are currently down-weighted by multiplying contribution by confidence, but the frozen rule is a single 0.5 threshold: score at observed value and add a verify item to the due-diligence checklist, with no silent value adjustment.
Reconcile the engine to that frozen rule.

## Scope

### In scope

The three endpoints, wired to the pure engine.
Server-side fetch and fact extraction for manually pasted public listing URLs only.
Claude vision analysis, preference-neutral and JSON-only, two-tier with caching by photoset hash.
Personalized normalization using `rubric.category_weights`.
Categorical match tables moved to config.
The value category MVP stub from facts.
Due-diligence checklist generation, including verify items for low-confidence findings.

### Out of scope this phase

The reno cost estimator, which stays tabled behind a clean seam.
Any scraping or MLS and IDX feeds, since only manually pasted public URLs are ingested.
Persisting scores and analyses, which is Phase D (this phase can cache analyses in-process or by hash without the full schema).
Geospatial gate automation.

## Data contracts touched

Consumes `Rubric`, `ListingFacts`, and `ListingObservations`; produces `ScoreResult`, all from `packages/contracts` and mirrored in `services/scoring/app/schemas.py`.
Reconcile `observation.ts` and the Pydantic `PhotoObservations` with the authoritative `docs/scoring-contract.md` section 5 schema.
`ScoreResult.observation_trace` must carry enough per-item detail for the UI to render the legibility example above.

## Task breakdown

### Task C1: Listing parse

Implement `/listings/parse` in `services/scoring/app/api/routes/listings.py`.
Fetch the public page server-side with `httpx` and extract structured facts (price, beds, baths, sqft, year built, garage, lot, taxes, address or coords if present) plus photo URLs.
Only manually pasted public URLs are accepted, and there is no crawling beyond the single pasted page.
Return `ListingFacts`.
Validate the URL at the boundary and raise `HTTPException` for unfetchable or unparseable pages.

### Task C2: Photo analysis, preference-neutral

Implement `/photos/analyze` in `services/scoring/app/api/routes/photos.py`.
Resize photos to a long edge around 1300px and cap the count around 12 to 15.
Send them to Claude vision with the `docs/scoring-contract.md` section 7 prompt, returning JSON only, observations and ratings and never scores.
Every finding carries `confidence` 0 to 1; unseen features become `not_observed` with a flag; an ambiguous wood-versus-gas fireplace becomes `unverified_wood` with low confidence and a flag.
Use two tiers: a cheaper model for a triage pass and a stronger model for full analysis.
Cache analysis by photoset hash so re-scoring is free.
In tests, do not call the network: mock the Anthropic client and assert on the request shape and the parsing of a fixture response.

### Task C3: Personalized normalization in the engine

Change the engine to normalize category scores using `rubric.category_weights` rather than the hardcoded `CATEGORY_BUDGETS`.
Each category's item contributions sum and are scaled so the category cannot exceed its personalized weight, and the total normalizes to 100 using the category weights.
This is what makes two rubrics produce meaningfully different totals for the same observations, so add a test that asserts exactly that.

### Task C4: Match tables to config

Move `CATEGORICAL_MATCH` out of `engine.py` into a config file loaded at startup.
Keep the continuous match function parameterized by direction as it is, since it is already preference-neutral machinery driven only by the rubric direction.
Tuning a table must not require a code change.

### Task C5: Value category MVP stub

Compute the value category from facts only: a `list_price / budget_max` headroom band, price-versus-comps if comps are parseable else omitted and renormalized, and a taxes flag if the assessment looks stale.
Document the stub clearly and leave a seam where the reno estimator will later supply an all-in cost.

### Task C6: Due-diligence checklist and confidence rule

Generate `dd_items` from the observations and the frozen confidence rule.
Any finding below the single 0.5 threshold is scored at its observed value and also added to the checklist as a verify item, with no silent value adjustment.
Add checklist items for `not_observed` and flagged findings as well.

### Task C7: Verdict, gate, and trace end to end

Confirm the gate short-circuit records a reason and skips scoring.
Confirm the verdict tiers (80 to 100 pursue, 65 to 79 showing, 50 to 64 conditional, under 50 weak).
Ensure the trace is rich enough for the UI legibility example, and that `/score` returns `{ gate, category_scores, total, verdict, flags, dd_items, observation_trace }`.

## Testing strategy

Keep the pure engine tests as the core, extending them for personalized normalization, the config-driven tables, the value stub, and the confidence-to-checklist rule.
Test parse against saved HTML fixtures in `tests/fixtures/`, never a live fetch.
Test analyze with a mocked Anthropic client and a fixture response, asserting JSON-only parsing, confidence presence, and flag behavior for unseen and ambiguous features.
Add the two-rubrics-differ test as an explicit acceptance test.
Add a neutrality test that the same photo observations yield identical observations regardless of rubric (see `preference-neutrality.md`).

## Risks and open decisions

The authoritative observation schema and vision prompt live in `docs/scoring-contract.md`; the remaining analyze work is implementing the two-tier analyzer against it.
Photo-selection logic for analysis is an open decision (all photos versus room-type-deduplicated, and the count cap).
The two-tier model split (which model triages, which scores) needs concrete model ids and a cost and latency check.
Comps parseability varies by source, so the value stub must renormalize cleanly when comps are absent.
Live listing pages change markup often, so parse should be resilient and fail loudly rather than silently returning empty facts.

## Acceptance checklist

- [x] `scoring-contract.md` authored, and its section 5 observation schema plus the style-affinity model committed to `packages/contracts`, the Pydantic models, and the engine (`scoring_config.json` style coordinates). Live vision is the remaining piece.
- [x] Parse returns real facts and photo URLs from a pasted public page.
- [~] Analyze is preference-neutral and cached by photoset hash. Cache and pluggable analyzer seam done; live two-tier Claude vision to be built against `docs/scoring-contract.md` (stub flags `vision_unconfigured`).
- [x] Engine normalizes using `rubric.category_weights`, not hardcoded budgets.
- [x] Categorical match tables live in config, not code (`scoring_config.json`).
- [x] Value category computed from facts via the documented stub with a reno seam.
- [x] Confidence follows the frozen 0.5 threshold rule, feeding the due-diligence checklist with no silent value adjustment.
- [x] A pasted URL returns a full score with a legible trace (deterministic chain proven in `test_scoring_pipeline.py`; live vision stubbed).
- [x] Two different rubrics produce meaningfully different totals for the same listing.

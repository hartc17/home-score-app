# Phase D - Persistence and Comparison

Persist scored listings and give a user a comparison view to rank the houses they have scored.

## Goal

Save listings, photo analyses, and scores so a user can revisit and compare them.
Provide a comparison table across a user's scored listings so they can rank and choose.

## Definition of done

A user can score several listings and rank them in a comparison view.
Scores are persisted with the rubric version that produced them, so tuning weights later never silently rewrites a past score.

## Dependencies and prerequisites

Phase C produces `ScoreResult` for a listing, which is the thing being persisted.
Phase B established `users` and `rubrics` persistence and the auth approach, which this phase builds on.
The remaining tables from the spec data model land here: `listings`, `photo_analyses`, `scores`, and `dd_items`.

## Scope

### In scope

The `listings`, `photo_analyses`, `scores`, and `dd_items` tables and migrations.
Persisting a score run: the listing facts, the photo analysis, the score, and its due-diligence items.
Recording which rubric version produced each score.
Endpoints to list a user's scored listings and to fetch a comparison.
A comparison table in the web app.

### Out of scope this phase

Aggregate-data products and any cross-user analytics, which the spec reserves.
The reno estimator and geospatial automation, still tabled.
Native mobile, since the MVP is responsive web.

## Data contracts touched

Persists `ListingFacts`, `ListingObservations`, and `ScoreResult` from `packages/contracts`.
The persisted `scores` row records `rubric_id`, `rubric_version`, the category scores, the total, and the verdict, per the spec data model.
The `photo_analyses` row records `model`, `schema_version`, the observations JSON, and the `photoset_hash` so cached analyses from Phase C can be reused.

## Task breakdown

### Task D1: Remaining schema and migrations

Add `listings`, `photo_analyses`, `scores`, and `dd_items` tables via migrations under `infra`.
Match the spec data model columns, including nullable and JSON columns.
Keep persistence models out of the pure scoring engine so `app/scoring/engine.py` stays I/O-free.

### Task D2: Persist a score run

When `/score` runs for a signed-in user, persist the listing, the analysis (reusing the photoset-hash cache from Phase C), the score with its `rubric_version`, and the due-diligence items.
Anonymous scoring may run without persistence, consistent with the funnel.

### Task D3: Listing and comparison endpoints

Add a router for a user's scored listings with declared Pydantic response models.
Provide a list endpoint and a comparison endpoint that returns the totals, category scores, verdicts, and key facts across several listings for one user.

### Task D4: Comparison view

Build a comparison table in `apps/web` that ranks a user's scored listings by total, shows the verdict tier, and exposes the category breakdown and due-diligence items.
Apply the pixel-perfection standard from the project conventions.

## Testing strategy

Test persistence with a mocked or in-memory database, never a real one.
Test that a persisted score records the exact rubric version, and that re-tuning the rubric and re-scoring creates a new score rather than mutating the old one.
Test the comparison endpoint returns correctly ranked results for a user with several scored listings.

## Risks and open decisions

Reusing the Phase C photoset-hash cache across the persisted `photo_analyses` table needs a single source of truth for the hash, so define it once and share it.
Ranking ties (equal totals) need a deterministic tiebreak so the comparison order is stable.
Historical integrity depends on never mutating a past score, so persistence must always insert a new score row rather than update in place.

## Acceptance checklist

- [x] `listings`, `photo_analyses`, `scores`, and `dd_items` tables created (via the shared `Base.metadata`, consistent with the `users`/`rubrics` approach from Phase B; the project has no separate migration framework).
- [x] A score run persists listing, analysis, score, and due-diligence items for a user, keyed by `anon_id`.
- [x] Each score records the rubric version that produced it.
- [x] Re-scoring after tuning creates a new score, leaving the old one intact.
- [x] Comparison endpoint and view rank a user's scored listings by total.
- [x] Persistence models stay out of the pure scoring engine (`app/scores/store.py` does the I/O; `app/scoring/engine.py` stays pure).

# Architecture

This document tracks the data flow, layers, and modules as they are actually built.
It is updated whenever the data flow, layers, modules, or schema change.

## One paragraph

A user answers image-only forced-choice questions in the web app.
The quiz infers a personal taste rubric (directional preferences plus category and item weights) entirely on the client.
They optionally complete a gates step (budget, district, beds and baths) that adds hard constraints to the rubric.
They paste listing URLs.
The scoring service fetches the page, extracts facts and photo URLs, analyzes the photos into preference-neutral observations, and applies the rubric via deterministic match times weight math to produce a 0 to 100 score, a verdict, and a due-diligence checklist.
The same listing scores differently for different users, which is the product.

## Layers

### Web (`apps/web`)

React plus TypeScript plus Vite plus Tailwind.
The quiz module (`src/quiz/`) is the current surface.
`questions.ts` is the data-driven question bank.
`inference.ts` is a pure function from picks to a `Rubric`.
`storage.ts` persists the anonymous rubric in the browser.
`Quiz.tsx` and `Reveal.tsx` render the forced-choice flow and the dual reveal.

### Contracts (`packages/contracts`)

The single source of truth for the shapes exchanged across the system.
`Rubric` is produced by the quiz and consumed by the scorer.
`ListingFacts`, `ListingObservations`, and `ScoreResult` are the scoring-service boundary types.
The Python service mirrors these as Pydantic models in `services/scoring/app/schemas.py`.

### Scoring service (`services/scoring`)

Python plus FastAPI.
The API layer is split into routers under `app/api/routes/` (listings, photos, score).
The pure scoring engine lives in `app/scoring/engine.py` and performs no I/O.
Tunable match tables and thresholds live in `app/scoring/scoring_config.json`, loaded by `app/scoring/config.py`, so tuning does not require a code change.

## Scoring data flow

`POST /listings/parse` takes a pasted public URL.
`app/api/routes/listings.py` fetches the page through an injectable `fetch_html`, then `app/listings/parser.py` extracts facts and photo URLs.
Extraction prefers schema.org JSON-LD, then Open Graph and meta tags, then a regex pass over visible text.

`POST /photos/analyze` takes the parsed facts.
`app/photos/analyzer.py` returns preference-neutral observations and caches them by a photoset hash so re-scoring is free.
The real Claude vision analyzer is a pluggable seam.
It is currently a stub that flags `vision_unconfigured`, pending the authoritative vision prompt and observation schema (`scoring-contract.md`).

`POST /score` takes the rubric, the observations, and the facts.
`app/scoring/engine.py` checks gates, computes a per-item match parameterized only by the rubric direction, aggregates each category as a weighted-average match, and normalizes across the assessed categories to a 0 to 100 total.
Confidence follows a single 0.5 threshold: a low-confidence finding is scored at its observed value and added to the due-diligence checklist, with no silent value adjustment.
The value category is an MVP stub computed from budget headroom, with a seam for the reno estimator.
The age category is deferred and excluded from the total rather than counted as zero.

## Scoring math

For each scored item, match is a 0 to 1 measure of how ideal the observation is for this user, driven only by the rubric direction.
A category fraction is the item-weight-weighted average of its item matches.
The total is `100 times the sum of (category_fraction times category_weight) over assessed categories, divided by the sum of those category weights`.
Two rubrics with different directions or different category weights therefore produce different totals for the same observations.

## Persistence

Rubrics persist server-side with no login friction (anonymous-first).
The quiz generates an anonymous id in the browser, and the web app posts the rubric to `POST /rubrics` keyed by that id.
The scoring service stores it in Postgres (SQLite in tests) as a `users` row and a versioned `rubrics` row.
Each save writes a new version, so tuning weights never rewrites a past rubric (`GET /rubrics/{anon_id}` returns the latest, `GET /rubrics/{anon_id}/versions` lists all).

The SQLAlchemy models live in `app/db/models.py`, the engine and session in `app/db/base.py`, and the store functions in `app/rubrics/store.py`.
Persistence is kept out of the pure scoring engine, which still performs no I/O.
Server-side merge logic mirrors the web client in `app/rubrics/merge.py` (compose, do not clobber) for the future account-claim flow.

Real login is deferred by design.
An optional magic-link claim will later set `email` on the same `users` row, so an anonymous rubric is claimed without any migration.
The `users.email` column is already nullable and unique for that path.
Listings, photo analyses, scores, and due-diligence items land in Postgres in Phase D.
The `infra/docker-compose.yml` provisions Postgres, and the service auto-creates tables on startup for MVP (a migration tool replaces this when the schema stabilizes).

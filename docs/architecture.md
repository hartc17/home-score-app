# Architecture

This document tracks the data flow, layers, and modules as they are actually built.
It is updated whenever the data flow, layers, modules, or schema change.
Diagrams are written in Mermaid and render on GitHub.

## One paragraph

A user answers image-only forced-choice questions in the web app.
The quiz infers a personal taste rubric (directional preferences plus category and item weights) entirely on the client.
They optionally complete a gates step (budget, district, beds and baths) that adds hard constraints to the rubric.
They paste listing URLs.
The scoring service fetches the page, extracts facts and photo URLs, analyzes the photos into preference-neutral observations, and applies the rubric via deterministic match times weight math to produce a 0 to 100 score, a verdict, and a due-diligence checklist.
The same listing scores differently for different users, which is the product.

## System context

```mermaid
flowchart LR
  user([User / browser])
  listingsite(["Public listing page"])
  anthropic(["Anthropic vision API"])
  db[("Postgres")]
  contracts["packages/contracts (shared types)"]

  subgraph web["apps/web (React + Vite)"]
    ui["Quiz / Gates / Reveal"]
    ls["localStorage"]
  end
  subgraph svc["services/scoring (FastAPI)"]
    routes["Routers"]
    engine["Pure scoring engine"]
    parser["Listing parser"]
    analyzer["Photo analyzer (seam)"]
    store["Rubric store"]
  end

  user --> ui
  ui --> ls
  ui -->|"REST / JSON"| routes
  ui -.->|"imports"| contracts
  routes -.->|"mirrors"| contracts
  routes --> engine
  routes --> parser
  routes --> analyzer
  routes --> store
  parser -->|"fetch"| listingsite
  analyzer -.->|"planned"| anthropic
  store --> db
```

Dashed edges are planned, not yet built.

## The neutrality invariant

Personalization enters through exactly one door: the rubric.
The vision layer is preference-agnostic and produces the same observations for everyone.

```mermaid
flowchart LR
  photos(["Listing photos"]) --> vision["Vision layer (preference-agnostic)"]
  vision --> obs["Neutral observations (same for everyone)"]
  quiz(["Quiz picks"]) --> inf["Inference"]
  inf --> rubric["Rubric directions (personal)"]
  obs --> match["Match = M(observation, direction)"]
  rubric --> match
  match --> score(["Personalized score"])
```

## Layers

### Web (`apps/web`)

React plus TypeScript plus Vite plus Tailwind.
The quiz module (`src/quiz/`) is the current surface.
`questions.ts` is the data-driven question bank.
`inference.ts` is a pure function from picks to a `Rubric`.
`storage.ts` persists the anonymous rubric in the browser.
`Quiz.tsx` and `Reveal.tsx` render the forced-choice flow and the dual reveal.
`gates/` holds the gates form and its pure parse and validation.
`rubric/merge.ts` composes the quiz rubric with gates without clobbering either side.
`api/client.ts` posts the rubric to the scoring service, best effort.

### Contracts (`packages/contracts`)

The single source of truth for the shapes exchanged across the system.
`Rubric` is produced by the quiz and consumed by the scorer.
`ListingFacts`, `ListingObservations`, and `ScoreResult` are the scoring-service boundary types.
The Python service mirrors these as Pydantic models in `services/scoring/app/schemas.py`.

### Scoring service (`services/scoring`)

Python plus FastAPI.
The API layer is split into routers under `app/api/routes/` (listings, photos, score, rubrics).
The pure scoring engine lives in `app/scoring/engine.py` and performs no I/O.
Tunable match tables and thresholds live in `app/scoring/scoring_config.json`, loaded by `app/scoring/config.py`, so tuning does not require a code change.
Persistence lives in `app/db/` (models, engine, session) and `app/rubrics/` (store and the server-side merge mirror), kept out of the pure engine.

## Quiz and persistence flow

```mermaid
sequenceDiagram
  actor U as User
  participant Q as Quiz UI
  participant I as inference.ts
  participant S as localStorage
  participant API as POST /rubrics
  participant ST as Rubric store
  participant DB as Postgres

  U->>Q: answer forced choices
  Q->>I: picks
  I-->>Q: Rubric (directions, weights, archetype)
  Q->>S: save rubric + anon_id
  Q->>API: {anon_id, rubric}
  API->>ST: save_rubric
  ST->>DB: insert versioned rubric row
  DB-->>ST: version
  ST-->>API: stored rubric
  API-->>Q: {version, rubric}
  Note over Q,S: Best effort. If the API fails, localStorage still holds it.
```

## Scoring data flow

`POST /listings/parse` takes a pasted public URL.
`app/api/routes/listings.py` fetches the page through an injectable `fetch_html`, then `app/listings/parser.py` extracts facts and photo URLs.
Extraction prefers schema.org JSON-LD, then Open Graph and meta tags, then a regex pass over visible text.

`POST /photos/analyze` takes the parsed facts.
`app/photos/analyzer.py` returns preference-neutral observations and caches them by a photoset hash so re-scoring is free.
The real Claude vision analyzer is a pluggable seam.
It is currently a stub that flags `vision_unconfigured`; the real analyzer will be built against the vision prompt and observation schema in [scoring-contract.md](scoring-contract.md).

`POST /score` takes the rubric, the observations, and the facts.
`app/scoring/engine.py` checks gates, computes a per-item match parameterized only by the rubric direction, aggregates each category as a weighted-average match, and normalizes across the assessed categories to a 0 to 100 total.

```mermaid
sequenceDiagram
  actor U as User
  participant W as Web
  participant P as POST /listings/parse
  participant A as POST /photos/analyze
  participant SC as POST /score
  participant E as Scoring engine
  participant V as Vision (seam)

  U->>W: paste listing URL
  W->>P: {url}
  P-->>W: ListingFacts (facts + photo_urls)
  W->>A: {listing}
  A->>V: analyze photos (cached by photoset hash)
  V-->>A: ListingObservations (neutral)
  A-->>W: observations
  W->>SC: {rubric, observations, facts}
  SC->>E: score()
  E-->>SC: ScoreResult (total, verdict, dd_items, trace)
  SC-->>W: score
```

## Scoring engine

```mermaid
flowchart TD
  start(["facts + observations + rubric"]) --> gate{"Any active gate fails?"}
  gate -->|yes| dq["DISQUALIFIED, record reason"]
  gate -->|no| items["For each item: match = M(obs, direction)"]
  items --> conf{"confidence < 0.5?"}
  conf -->|yes| dd["Add verify item to DD checklist"]
  conf -->|no| cat["Accumulate match x weight into category"]
  dd --> cat
  cat --> frac["category fraction = weighted avg of item matches"]
  frac --> norm["total = 100 x sum(frac x weight) / sum(weight) over assessed categories"]
  norm --> verdict["Verdict tier: pursue / showing / conditional / weak"]
  verdict --> out(["ScoreResult + trace + DD checklist"])
  dq --> out
```

For each scored item, match is a 0 to 1 measure of how ideal the observation is for this user, driven only by the rubric direction.
A category fraction is the item-weight-weighted average of its item matches.
Two rubrics with different directions or different category weights therefore produce different totals for the same observations.
Confidence follows a single 0.5 threshold: a low-confidence finding is scored at its observed value and added to the due-diligence checklist, with no silent value adjustment.
The value category is an MVP stub computed from budget headroom, with a seam for the reno estimator.
The age category is deferred and excluded from the total rather than counted as zero.
Architectural and interior style are scored by style affinity: each style is a fixed point in a five-axis taste space, the buyer is a point derived from their rubric directions, and the match is their axis agreement (see [scoring-contract.md](scoring-contract.md) sections 4 and 6.3).
Style coordinates live in `scoring_config.json`, so the vocabulary grows without code change.

## Persistence

Rubrics persist server-side with no login friction (anonymous-first).
The quiz generates an anonymous id in the browser, and the web app posts the rubric to `POST /rubrics` keyed by that id.
The scoring service stores it in Postgres (SQLite in tests) as a `users` row and a versioned `rubrics` row.
Each save writes a new version, so tuning weights never rewrites a past rubric (`GET /rubrics/{anon_id}` returns the latest, `GET /rubrics/{anon_id}/versions` lists all).

The SQLAlchemy models live in `app/db/models.py`, the engine and session in `app/db/base.py`, and the store functions in `app/rubrics/store.py`.
Persistence is kept out of the pure scoring engine, which still performs no I/O.
Server-side merge logic mirrors the web client in `app/rubrics/merge.py` (compose, do not clobber) for the future account-claim flow.

### Data model

Solid entities are built today.
Dashed entities (listings, photo analyses, scores, due-diligence items) are the Phase D schema, shown here as the target.

```mermaid
erDiagram
  USERS ||--o{ RUBRICS : owns
  RUBRICS ||--o{ SCORES : produced
  LISTINGS ||--o{ PHOTO_ANALYSES : has
  LISTINGS ||--o{ SCORES : scored
  SCORES ||--o{ DD_ITEMS : contains

  USERS {
    int id PK
    string anon_id UK
    string email "nullable, set on magic-link claim"
    datetime created_at
  }
  RUBRICS {
    int id PK
    int user_id FK
    int version
    json gates
    json category_weights
    json item_weights
    json directions
    json archetype
    json confidence
    datetime created_at
  }
  LISTINGS {
    int id PK
    string url
    json facts
    datetime created_at
  }
  PHOTO_ANALYSES {
    int id PK
    int listing_id FK
    string model
    string schema_version
    string photoset_hash
    json observations
  }
  SCORES {
    int id PK
    int listing_id FK
    int rubric_id FK
    int rubric_version
    int total
    string verdict
    json category_scores
  }
  DD_ITEMS {
    int id PK
    int score_id FK
    string text
    bool checked
  }
```

### Rubric lifecycle

```mermaid
stateDiagram-v2
  [*] --> Anonymous: complete quiz
  Anonymous --> AnonymousGated: add gates (merge, no clobber)
  Anonymous --> Persisted: POST /rubrics (v1)
  AnonymousGated --> Persisted: POST /rubrics (v2)
  Persisted --> Persisted: retune, new version
  Persisted --> Claimed: magic-link claim (planned)
  Claimed --> Claimed: compose_forward on re-quiz
  Claimed --> [*]
```

Real login is deferred by design.
An optional magic-link claim will later set `email` on the same `users` row, so an anonymous rubric is claimed without any migration.
The `users.email` column is already nullable and unique for that path.
The `infra/docker-compose.yml` provisions Postgres, and the service auto-creates tables on startup for MVP (a migration tool replaces this when the schema stabilizes).

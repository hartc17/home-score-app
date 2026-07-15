# HouseFlavor

A home-listing scoring app that personalizes scores based on your taste profile.

## What it does

A user answers image-only forced-choice questions; the app infers a personal taste rubric (directional preferences + category weights).
They optionally complete a gates step (budget, district, beds/baths) that adds hard constraints to the rubric.
They paste listing URLs; the scoring service fetches the page, extracts photos, sends them to Claude vision (preference-neutral JSON observations), then applies the rubric via deterministic match x weight math to produce a 0-100 score, verdict, and due-diligence checklist.
The same listing scores differently for different users - that is the product.

## Documentation

Full documentation lives in [docs/](docs/README.md): [architecture](docs/architecture.md) (with diagrams), the [scoring contract](docs/scoring-contract.md), the [roadmap](docs/roadmap.md), the [decision log](docs/decisions.md), and the [phase plans](docs/plans/README.md).

## Monorepo layout

```
apps/web                  React + TypeScript + Vite + Tailwind frontend
packages/contracts        Shared TypeScript type definitions
services/scoring          Python FastAPI scoring service
infra/                    Infrastructure (docker-compose for Postgres)
```

## Prerequisites

- Node 20+
- Python 3.12
- Docker + Docker Compose

## Setup

### Frontend

```bash
npm install
npm run dev --workspace=apps/web
```

The web app opens on the forced-choice quiz.
Answering it infers a taste rubric (`packages/contracts` `Rubric`), persists it anonymously in the browser, and shows the archetype reveal.
The quiz module lives in `apps/web/src/quiz/`: `questions.ts` (data-driven bank), `inference.ts` (pure picks-to-rubric), `storage.ts` (anonymous persistence), and the `Quiz`/`Reveal` components.

### Scoring service

```bash
cd services/scoring
python3.12 -m venv ../../.venv
source ../../.venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The service reads `DATABASE_URL` (defaults to the Postgres from `infra/docker-compose.yml`).
It auto-creates tables on startup.
The web dev server proxies `/rubrics`, `/listings`, `/photos`, and `/score` to `http://localhost:8000`, so run both together during development.

### Database

```bash
cd infra
docker compose up -d
```

## Running tests

```bash
# Python tests
source .venv/bin/activate
pytest services/scoring

# Web tests
npm test --workspace=apps/web
```

## Phase status

Detailed, actionable plans for each phase live in [docs/plans/](docs/plans/README.md).

| Phase | Status | Description | Plan |
|---|---|---|---|
| A | 🔨 | Quiz -> Rubric (client-side inference, anonymous persistence). Core built with SVG stand-in plates; curated photo bank still pending. | [phase-a](docs/plans/phase-a-quiz-rubric.md) |
| B | 🔨 | Gates + anonymous persistence + merge. Gates form, rubric merge (compose, don't clobber), and versioned server-side persistence keyed by an anonymous id are done. Optional magic-link account claim is deferred by design. | [phase-b](docs/plans/phase-b-gates-accounts.md) |
| C | 🔨 | Scoring service. Deterministic core done (config-driven engine, personalized weights, style-affinity, parse); [scoring contract](docs/scoring-contract.md) written; Claude vision analyzer built (gated on `ANTHROPIC_API_KEY`), with triage/resize hardening left. | [phase-c](docs/plans/phase-c-scoring-service.md) |
| D | ⏳ | Persistence + comparison view | [phase-d](docs/plans/phase-d-persistence-comparison.md) |

Preference neutrality is a cross-cutting hard requirement spanning phases A and C: see [docs/plans/preference-neutrality.md](docs/plans/preference-neutrality.md).

## Scoring service endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/listings/parse` | Fetch a pasted public listing URL and extract facts + photo URLs (JSON-LD, then meta tags, then text) |
| POST | `/photos/analyze` | Analyze listing photos into preference-neutral observations, cached by photoset hash. Uses Claude vision when `ANTHROPIC_API_KEY` is set, else a stub; see [scoring-contract.md](docs/scoring-contract.md) |
| POST | `/score` | Apply a rubric to observations -> 0-100 score, verdict, due-diligence checklist, and trace |
| POST | `/rubrics` | Persist a rubric for an anonymous id (versioned); returns the stored version |
| GET | `/rubrics/{anon_id}` | Latest stored rubric for an anonymous id |
| GET | `/rubrics/{anon_id}/versions` | Version history for an anonymous id |

Tunable scoring tables and thresholds live in `services/scoring/app/scoring/scoring_config.json`, so tuning does not require a code change.
See [docs/architecture.md](docs/architecture.md) for the full data flow and scoring math.

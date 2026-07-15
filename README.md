# HouseFlavor

A home-listing scoring app that personalizes scores based on your taste profile.

## What it does

A user answers image-only forced-choice questions; the app infers a personal taste rubric (directional preferences + category weights).
They optionally complete a gates step (budget, district, beds/baths) that adds hard constraints to the rubric.
They paste listing URLs; the scoring service fetches the page, extracts photos, sends them to Claude vision (preference-neutral JSON observations), then applies the rubric via deterministic match x weight math to produce a 0-100 score, verdict, and due-diligence checklist.
The same listing scores differently for different users - that is the product.

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

### Scoring service

```bash
cd services/scoring
python3.12 -m venv ../../.venv
source ../../.venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

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
| A | ⏳ | Quiz -> Rubric (client-side inference, anonymous persistence) | [phase-a](docs/plans/phase-a-quiz-rubric.md) |
| B | ⏳ | Gates + accounts + anonymous->account rubric merge | [phase-b](docs/plans/phase-b-gates-accounts.md) |
| C | ⏳ | Scoring service (parse, analyze, score endpoints) | [phase-c](docs/plans/phase-c-scoring-service.md) |
| D | ⏳ | Persistence + comparison view | [phase-d](docs/plans/phase-d-persistence-comparison.md) |

Preference neutrality is a cross-cutting hard requirement spanning phases A and C: see [docs/plans/preference-neutrality.md](docs/plans/preference-neutrality.md).

## Scoring service endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/listings/parse` | Parse listing URL into structured facts |
| POST | `/photos/analyze` | Analyze listing photos into observations |
| POST | `/score` | Apply rubric to observations -> score |

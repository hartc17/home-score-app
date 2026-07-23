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
The quiz module lives in `apps/web/src/quiz/`: `questions.ts` (data-driven bank), `inference.ts` (pure picks-to-rubric), `storage.ts` (anonymous persistence), `scene/` (the token-driven parametric illustration engine: `tokens.ts` palettes, `spec.ts` scene ids, `Scene.tsx` renderer), `OptionImage.tsx` (the scene-to-curated-photo swap seam), `shareCard.ts` (the reveal's shareable image export), and the `Quiz`/`Reveal` components.
An account bar (`apps/web/src/account/`) lets a buyer save their profile: "Save your profile" emails a magic link, and landing on that link signs them in so their rubric follows them across devices.
From the reveal, "Share my flavor" exports an image card of the archetype, and "Score listings" opens the comparison view (`apps/web/src/compare/`), where pasting a listing URL scores it against the rubric and ranks it against previously scored listings.

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
The web dev server proxies `/rubrics`, `/listings`, `/photos`, `/score`, `/scores`, and `/auth` to `http://localhost:8000`, so run both together during development.

Production configuration (`HOUSEFLAVOR_ENV=production`) fails closed on unsafe auth defaults: the service refuses to sign a session unless `HOUSEFLAVOR_SESSION_SECRET` is set to a non-default value, and `/auth/request` errors rather than returning a link unless a real mail provider (`RESEND_API_KEY`) is configured. In development both fall back to safe local defaults (a console sender that returns the link as `dev_link`).

Server-side fetches refuse URLs that resolve to non-public addresses (SSRF guard), which also blocks a listing served from localhost. To score a local test listing during development set `HOUSEFLAVOR_ALLOW_PRIVATE_FETCH=1`; the flag is ignored in production.

### Database

```bash
cd infra
docker compose up -d
```

## Run with Docker (full stack)

The whole app (Postgres, the FastAPI scoring service, and the web app served by nginx) runs from the root compose file:

```bash
docker compose up --build
# then open http://localhost:8080
```

nginx serves the built web bundle and reverse-proxies the API paths (`/rubrics`, `/listings`, `/photos`, `/score`, `/scores`, `/auth`) to the scoring service, so there is one origin and no CORS.
This runs in development mode: the console email sender returns the magic link as `dev_link`, and the default session secret is used.
For a production-like run set `HOUSEFLAVOR_ENV=production` on the `scoring` service and provide `HOUSEFLAVOR_SESSION_SECRET` and `RESEND_API_KEY` (the service otherwise fails closed, as above).

## Running tests

```bash
# Python tests
source .venv/bin/activate
pytest services/scoring

# Web tests
npm test --workspace=apps/web
```

Both stacks are linted: Python with Ruff (`ruff check`, configured in `services/scoring/pyproject.toml`) and the web app with ESLint (`npm run lint --workspace=apps/web`, flat config with typescript-eslint type-checked rules plus react-hooks and jsx-a11y).
CI (`.github/workflows/ci.yml`) runs both lints, the Python and web tests, the web typecheck and build, and builds both Docker images on every push and pull request.

## Phase status

Detailed, actionable plans for each phase live in [docs/plans/](docs/plans/README.md).

| Phase | Status | Description | Plan |
|---|---|---|---|
| A | 🔨 | Quiz -> Rubric (client-side inference, anonymous persistence). Core built; the reveal exports a shareable image card. The image bank is a token-driven parametric SVG illustration system where warm/cool is a palette swap and traditional/modern is a motif swap over one fixed geometry, so within any pair neither pole can be better-lit or more lovingly rendered: neutrality is structural. Each option can still be overridden with a curated photo via one field. | [phase-a](docs/plans/phase-a-quiz-rubric.md), [illustration-bank](docs/plans/illustration-bank.md) |
| B | 🔨 | Gates + anonymous persistence + merge. Gates form, rubric merge (compose, don't clobber), and versioned server-side persistence keyed by an anonymous id are done. Optional magic-link account claim is deferred by design. | [phase-b](docs/plans/phase-b-gates-accounts.md) |
| C | 🔨 | Scoring service. Deterministic core done (config-driven engine, personalized weights, style-affinity, parse); [scoring contract](docs/scoring-contract.md) written; Claude vision analyzer built (gated on `ANTHROPIC_API_KEY`) with the two-tier pass wired: photos are resized to a ~1300px long edge and a cheap triage model dedups near-duplicate rooms before the strong analysis pass. A live cost/latency check still needs a real key. | [phase-c](docs/plans/phase-c-scoring-service.md) |
| D | 🔨 | Persistence + comparison view. Listing, photo-analysis, score, and due-diligence tables; a score-run endpoint that gets-or-creates a listing, reuses the cached photo analysis, and records a per-rubric score with its rubric version; and a comparison view that ranks a user's scored listings. Keyed by the anonymous id. | [phase-d](docs/plans/phase-d-persistence-comparison.md) |
| E | 🔨 | Accounts + magic-link claim. Passwordless sign-in emails a one-time link (real provider gated on `RESEND_API_KEY`, console sender otherwise); verifying it claims the anonymous rubric onto the account, composing forward when the email already has one, and issues a signed session. A live email send still needs a provider key. | [phase-e](docs/plans/phase-e-accounts.md) |

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
| POST | `/scores/run` | Score a pasted listing URL against the caller's latest rubric and persist the run (get-or-create listing, reuse cached photo analysis, record a per-rubric score with its rubric version) |
| GET | `/scores/{anon_id}` | The caller's scored listings, ranked by total (newest score per listing) |
| POST | `/auth/request` | Email a one-time magic-link sign-in for an email + anon id. Uses a real provider when `RESEND_API_KEY` is set, else a console sender that returns the link as `dev_link` for local use |
| POST | `/auth/verify` | Verify a magic-link token: claim the anonymous rubric onto the account (compose-forward when the email already has one) and return a signed session |
| GET | `/auth/me` | The signed-in user and their latest rubric, from a `Bearer` session token |
| POST | `/auth/signout` | Revoke every outstanding session for the signed-in user (bumps the user's session epoch) |

Tunable scoring tables and thresholds live in `services/scoring/app/scoring/scoring_config.json`, so tuning does not require a code change.
See [docs/architecture.md](docs/architecture.md) for the full data flow and scoring math.

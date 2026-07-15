# Decision log

A running record of the significant technical decisions on HouseFlavor, why they were made, and their consequences.
Newest decisions are appended at the bottom.
Each entry is short by design; the detail lives in the linked docs and code.

## ADR-001: Work directly off `main`

Status: accepted.

Context: a solo build in the early phase, where feature-branch-plus-PR ceremony adds friction without review benefit.
Decision: commit and push directly to `main`; keep the `--no-verify` and force-push guards.
Consequences: faster iteration; the convention is recorded in `CLAUDE.md` so it is deliberate, not accidental.
Revisit when more than one person contributes.

## ADR-002: Anonymous-first persistence, magic-link account claim deferred

Status: accepted.

Context: the funnel converts an anonymous quiz taker into a buyer, and the priority is the most seamless experience that still persists a rubric.
Decision: persist rubrics server-side keyed by the anonymous id the quiz already generates, with zero login friction; defer real login to an optional magic-link claim that sets `email` on the same `users` row.
Consequences: persistence works the instant a quiz completes; cross-device accounts wait for Phase E; no migration is needed to claim an anonymous rubric because the schema already carries a nullable `email`.
See [architecture.md](architecture.md) and [roadmap.md](roadmap.md).

## ADR-003: Config-driven scoring engine

Status: accepted.

Context: the spec requires that tuning match tables and thresholds not require a redeploy.
Decision: keep match tables, category and item vocabularies, thresholds, and (soon) style coordinates in `services/scoring/app/scoring/scoring_config.json`, loaded by `config.py`; the engine reads config and stays pure.
Consequences: tuning is a config edit, not a code change; the engine remains I/O-free and unit-testable.

## ADR-004: Personalized normalization over assessed categories

Status: accepted.

Context: the original engine hardcoded category budgets and ignored the rubric's personalized `category_weights`, which broke the premise that the same house scores differently for different people.
Decision: score each category as the item-weight-weighted average of its item matches, then normalize the total across only the categories that had data, using the rubric's personalized category weights.
Consequences: two rubrics produce meaningfully different totals for the same listing; missing photo categories do not silently cap the score; category scores are legible as points out of their weight.
See [architecture.md](architecture.md) scoring engine section.

## ADR-005: Frozen single 0.5 confidence threshold

Status: accepted.

Context: an earlier version multiplied each contribution by its confidence, which silently down-weighted uncertain but real observations.
Decision: use a single 0.5 threshold; a finding below it is scored at its observed value and added to the due-diligence checklist as a verify item, with no silent value adjustment.
Consequences: the score reflects what was observed; uncertainty surfaces as an explicit checklist item rather than a hidden discount.

## ADR-006: Style scoring via fixed axis coordinates, not per-style preference rows

Status: accepted.

Context: the system reasons about many architectural and interior styles, and personalization must never leak into the neutral layer.
Decision: place each style at a fixed point in the taste-axis space, and derive the buyer's point from their rubric directions; match is the axis-agreement between the two.
Consequences: adding a style is a config edit, not new match logic; neutrality holds because style points are fixed and only the buyer's point is personal.
See [scoring-contract.md](scoring-contract.md) sections 4 and 6.3.

## ADR-007: Synchronous SQLAlchemy with SQLite in tests

Status: accepted.

Context: the persistence layer needs to be robust and testable without a real database.
Decision: use synchronous SQLAlchemy 2.0 with Postgres in production and SQLite in tests; database endpoints are synchronous and run in FastAPI's threadpool, avoiding async-driver complexity.
Consequences: tests run against an in-memory SQLite engine via dependency override and never touch a real database; the pure scoring engine stays free of any database dependency.

## ADR-008: Auto-create tables on startup for the MVP

Status: accepted, with a planned successor.

Context: the schema is still moving, and a migration tool adds ceremony that is not yet worth it.
Decision: the service calls `create_all` on startup to provision tables.
Consequences: dev and MVP deploys just work; this is explicitly temporary and will be replaced by a migration tool (for example Alembic) once the schema stabilizes.
Tracked in [roadmap.md](roadmap.md) under the engineering backlog.

## ADR-009: `packages/contracts` is the source of truth; Python mirrors by hand

Status: accepted, with a known risk.

Context: both the web app and the Python service need the same shapes.
Decision: define the shapes once as TypeScript in `packages/contracts`, and mirror them as Pydantic models in the scoring service.
Consequences: one authoritative definition; the hand mirroring can drift.
The mitigation, generating JSON Schema from the contracts and testing the Pydantic models against it, is on the engineering backlog.

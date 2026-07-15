# Phase B - Gates, Accounts, and Merge

Add the hard-constraints gates step, account creation, and the anonymous to account rubric merge.
This is where the funnel converts an anonymous quiz taker into an account holder without it feeling like a toll.

## Goal

Capture the user's stated hard constraints (budget, districts, beds, baths, garage, home types, main-road exclusion, timeline) into `rubric.gates`.
Introduce accounts so a rubric can belong to a user and be persisted and versioned server-side.
Merge the anonymous quiz rubric forward into the new account rubric by composing, never clobbering the quiz-derived parts.

## Definition of done

Completing the gates step yields a full rubric that has both the gates and the quiz-derived parts intact.
The rubric is versioned, and a later weight change creates a new version rather than silently rewriting history.
Signup is framed as the first gate question, so it reads as progress, not a paywall.
On account creation, the anonymous quiz rubric merges into the account rubric with quiz weights and directions preserved.

## Dependencies and prerequisites

Phase A must emit a schema-valid anonymous rubric and persist it client-side, since Phase B merges that object.
A minimal backend that can own users and rubrics must exist.
The build spec's data model puts `users` and `rubrics` in Postgres and the scoring service is FastAPI, so the natural home for accounts and rubric persistence is the FastAPI service plus its Postgres database.
Standing up that persistence layer overlaps with Phase D, so decide early whether the `users` and `rubrics` tables land here in Phase B and the rest of the schema lands in Phase D, or whether all tables land in Phase D.
Recommended: create `users` and `rubrics` in Phase B (accounts cannot exist without them) and defer `listings`, `photo_analyses`, `scores`, and `dd_items` to Phase D.

## Scope

### In scope

The gates form and its write into `rubric.gates`.
Account creation and authentication, at the minimum needed to own a rubric.
The `users` and `rubrics` tables and their migrations.
Rubric versioning.
The anonymous to account merge-forward.

### Out of scope this phase

Any listing parsing, photo analysis, or scoring (Phase C).
Comparison views and the remaining tables (Phase D).
Geospatial automation of gates (district polygons, road-class), which the spec defers.
Password reset flows, social login, and other account polish beyond what is needed to own a rubric.

## Data contracts touched

Writes `RubricGates` from `packages/contracts/src/rubric.ts`: `budget_max`, `districts`, `min_beds`, `min_baths`, `min_garage`, `exclude_main_road`, `home_types`, and optional `timeline`.
The full `Rubric` gains its `gates` field here.
Persisted rubric rows should mirror the spec data model: `id`, `user_id` (nullable for anonymous), `version`, and the JSON columns for gates, category weights, item weights, directions, archetype, and confidence.

## Task breakdown

### Task B1: Decide and document the auth approach

The build spec names no auth technology, so this is a decision to surface before building (see open decisions).
Pick the simplest approach that lets a rubric belong to a user and keeps the anonymous data asset unencumbered with clear consent.
Document the choice in `docs/architecture.md` and the README before writing endpoints.

### Task B2: Users and rubrics persistence

Add the `users` and `rubrics` tables via a migration under `infra` (the compose file already provisions Postgres).
Add SQLAlchemy models or the chosen persistence layer to the scoring service, kept out of the pure scoring engine so `app/scoring/engine.py` stays free of I/O.
Persist rubrics versioned: a new logical change writes a new row with an incremented `version`, and the old version remains readable.

### Task B3: Rubric API endpoints

Add a rubrics router under `services/scoring/app/api/routes/` following the routers-not-monolith rule.
Provide create, read, and list-versions for a user's rubric, each with a declared Pydantic response model.
Return `HTTPException` for client errors and let unexpected errors surface as 500s.

### Task B4: Gates form on the web

Build the gates form in `apps/web` capturing the stated constraints directly, since these are stated knowledge and must not be inferred.
Validate at the boundary (budget positive, min beds and baths non-negative, at least one district or an explicit any).
Write the collected values into the rubric's `gates` and submit to the rubrics endpoint.

### Task B5: Signup as the first gate question

Frame account creation as the first step of the gates flow so it reads as progress.
Before signup, the quiz and its anonymous rubric already work, so signup unlocks utility rather than gating the quiz.

### Task B6: Anonymous to account merge

Implement the merge-forward: on account creation, take the anonymous rubric from client storage and compose it into the new account rubric.
Quiz-derived `category_weights`, `item_weights`, `directions`, `archetype`, and `confidence` must not be overwritten by the gates step.
Gates are added on top.
If the user somehow completed gates before an anonymous quiz existed, the account rubric has gates and empty or default quiz parts, and a later quiz completion composes in without clobbering gates.
Write a single merge function with explicit precedence rules and test it directly.

## Testing strategy

Unit test the merge function: quiz parts survive, gates are added, neither side clobbers the other, and versioning increments correctly.
Test the rubrics endpoints with a mocked or in-memory database, never a real one, per the repo testing rules.
Test gates form validation at the boundary.
Test that reading an old rubric version returns the pre-change weights, proving versioning does not rewrite history.

## Risks and open decisions

Auth technology is unspecified in the spec and must be chosen and documented (Task B1).
The split of table ownership between Phase B and Phase D must be settled (see prerequisites).
Consent and data-asset cleanliness are called out in the business context, so capture the anonymous profile with clear consent from day one.
The merge precedence rules are the highest-risk logic in this phase, so they get direct unit tests rather than being covered only through the UI.

## Acceptance checklist

- [ ] Auth approach chosen and documented in architecture and README. Open decision, not yet made.
- [ ] `users` and `rubrics` tables migrated, models kept out of the pure engine. Blocked on the auth decision.
- [ ] Rubrics endpoints exist with declared response models. Blocked on the auth decision.
- [x] Gates form captures stated constraints and validates at the boundary (`apps/web/src/gates/`).
- [ ] Signup is framed as the first gate question. Blocked on accounts.
- [x] Merge composes quiz and gates without clobbering either side (`apps/web/src/rubric/merge.ts`).
- [ ] Rubrics are versioned and old versions remain readable. Server-side, blocked on persistence.
- [x] Merge and gates parsing have direct unit tests (`merge.test.ts`, `schema.test.ts`).

# Phase A - Quiz to Rubric

Client-only phase.
Productionize the forced-choice quiz prototype so a session produces a schema-valid `Rubric` and a shareable archetype reveal, persisted anonymously in the browser.

## Goal

Turn the image-only forced-choice quiz into a data-driven module that infers a personal taste rubric entirely on the client.
No backend, no account, no network call is required to complete the quiz and see a result.
The rubric object it emits is the single contract consumed by every later phase, so getting its shape and inference right is the whole point of this phase.

## Definition of done

A completed quiz session produces a `Rubric` object that validates against `packages/contracts` (matching `Rubric` in `rubric.ts`).
The reveal shows both a shareable archetype and a taste-profile rubric preview.
The anonymous rubric persists across page reloads with no account.
Answering consistently to one pole yields that pole's archetype with a `strong` direction.
Mixed or indifferent answers yield the balanced archetype with `slight` or low-confidence directions.
The bias smoke test passes (see `preference-neutrality.md`).

## Dependencies and prerequisites

The React and Vite and Tailwind skeleton already exists at `apps/web`.
The `packages/contracts` `Rubric` type already exists and is the target shape.

Blocking prerequisite: the companion prototype `house-flavor-quiz.jsx` referenced in the build spec is not in the repo.
The very first task is to obtain that file and commit it, or to reconstruct the prototype from its described behavior if it cannot be recovered.
Do not start productionizing before the prototype (or an agreed replacement) is in the tree, since it defines the question flow, the inference tally, and the reveal.

Non-blocking prerequisite: the production photo bank does not exist yet.
Phase A ships with SVG stand-ins and a one-field swap seam so photos can replace them later (see `preference-neutrality.md` for the image curation test).

## Scope

### In scope

Data-driven question bank with neutral framing and no option captions.
Client-side inference from picks to directions, category weights, item weights, archetype, and confidence.
Anonymous persistence of the rubric in the browser.
Dual reveal (archetype plus rubric preview).
The bias smoke test wired into CI.

### Out of scope this phase

Gates, accounts, and any server persistence (Phase B).
Any scoring of real listings (Phase C).
The curated production photo bank and the share-card image export (later passes).
Reading or writing the rubric to Postgres.

## Data contracts touched

Produces `Rubric` from `packages/contracts/src/rubric.ts`.
The emitted object must set `version`, `category_weights`, `item_weights`, `directions`, `archetype`, and `confidence`.
The `gates` field is left undefined by the quiz and is filled only in Phase B.
`category_weights` keys are fixed by the `CategoryWeights` interface: `bones`, `warmth`, `finish`, `outdoor`, `value`, `age`.
`item_weights` keys must match the item keys the scoring engine reads, so align them with `services/scoring/app/scoring/engine.py` `ITEM_CATEGORY` (for example `tone_warmth`, `fireplace`, `flooring`, `counters`, `cabinets`, `appliances`, `curb_appeal`, `lot_character`, `deck_patio`, `garage_type`, `exterior_style`, `ceiling_height`, `natural_light`, `condition`).
Keeping these key sets in sync is a hard cross-phase constraint, so treat any mismatch as a bug in `packages/contracts`, not something to paper over per side.

## Task breakdown

### Task A1: Bring in the prototype

Obtain `house-flavor-quiz.jsx` and commit it under `apps/web/src/quiz/prototype/` as a reference, or reconstruct it.
Get it rendering inside the existing Vite app at a `/quiz` route so its current behavior is visible end to end before any refactor.

### Task A2: Extract the question bank into typed data

Create `apps/web/src/quiz/questions.ts`.
Each question is a plain object with a neutral `prompt`, an `id`, and exactly two `options`.
Each option carries `image` (SVG stand-in URL or inline id for now), axis deltas `d` (a partial map of axis to signed magnitude), and `tags` (string array).
Model the axes explicitly as a typed union, at minimum `tone` (cool to warm) and `era` (traditional to modern), plus any tag-only axes the prototype uses.
Structure the option so swapping an SVG for a photo URL is a single field change, per the spec.
No option may carry a caption, and center or axis labels must not name one pole (use `Tone`, not `Warmth`).

### Task A3: Build the typed inference unit

Create `apps/web/src/quiz/inference.ts` as a pure function from an ordered list of picks to a `Rubric`.
Per axis, tally the signed deltas, average them, and map the average to a direction plus a strength band (`strong`, `slight`, or none).
Compute per-axis confidence from consistency of picks on that axis, not from raw count.
Indifference or mixed picks must down-weight the axis toward zero rather than average to a misleading middle, so an indifferent axis contributes near-zero weight and no asserted direction.
Map axis strengths and tag frequencies to `category_weights` (normalized to sum to 100) and to `item_weights` (each category's items sum to its category budget).
Snap the axis and tag blend to one of a fixed display archetype set and emit `archetype.name` plus `archetype.blend`.
Emit `confidence` per category from the axis consistencies that feed it.
Keep this function free of React and free of side effects so it is unit-testable in isolation.

### Task A4: Wire the quiz UI to the inference

Replace the prototype's inline inference with the extracted unit.
Keep keyboard support (left and right pick) and image-only plates from the prototype.
On completion, call `inference.ts` and store the resulting rubric.

### Task A5: Anonymous persistence

Create `apps/web/src/quiz/storage.ts` that serializes the rubric to `localStorage` under a versioned key.
Reload restores the last completed rubric and skips straight to the reveal unless the user restarts.
Record enough to support the Phase B merge later (the full rubric, its `version`, and a client-generated anonymous id), but do not build the merge here.

### Task A6: Dual reveal

Build the reveal view with two outputs.
The shareable archetype card (marketing surface) shows `archetype.name` and a flattering identity description.
The rubric preview (proof surface) shows the inferred directions, category weights, and confidences in a legible form.
Audit every archetype's reveal copy so each reads as desirable, per the neutrality words requirement.

### Task A7: Bias smoke test in CI

Implement the synthetic random-choice session runner described in `preference-neutrality.md`.
Add it to the web test suite so `npm test` from `apps/web` runs it, and wire that into CI.

## Testing strategy

Unit test `inference.ts` with `test_<thing>_<condition>_<expected>` style names adapted to the web runner.
Cover: consistent one-pole picks yield that pole with `strong`; alternating picks yield near-zero axis weight and no asserted direction; the emitted object validates against the `Rubric` JSON Schema from `packages/contracts`.
Add a schema-validation test that fails loudly if `item_weights` keys drift from the scoring engine's known item keys.
The bias smoke test asserts that aggregate archetypes over many random sessions are roughly uniform across the taste space.
Tests must not hit the network, consistent with the repo testing rules.

## Risks and open decisions

The prototype file is missing, which blocks the phase until recovered or reconstructed (see prerequisites).
Question-bank size for a stable rubric is an open decision, target roughly 8 to 12 picks.
Category-weight floors and ceilings are an open decision, so one category cannot swamp the score.
Archetype set is an open decision, recommended as a fixed display set the rubric snaps to rather than emergent clusters.
The `item_weights` key vocabulary must be agreed jointly with Phase C, since both sides must reference the same item keys.

## Acceptance checklist

- [ ] Prototype committed and rendering at `/quiz` before refactor.
- [ ] Question bank is typed data with neutral prompts and no captions.
- [ ] Inference is a pure, tested, React-free unit.
- [ ] Indifferent axes down-weight rather than average to the middle.
- [ ] Emitted rubric validates against `packages/contracts`.
- [ ] `item_weights` keys match the scoring engine's item keys.
- [ ] Anonymous rubric persists across reload.
- [ ] Reveal shows both archetype and rubric preview, with audited flattering copy.
- [ ] Bias smoke test passes in CI.

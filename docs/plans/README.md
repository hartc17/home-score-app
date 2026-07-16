# HouseFlavor - Phase Plans

Detailed, actionable plans for the four build phases plus the cross-cutting neutrality requirement.
These plans are derived from the build spec and grounded in the current scaffold (the `packages/contracts` types, the stubbed FastAPI endpoints, and the pure scoring engine already in the tree).

## The chain in one line

Quiz infers a rubric (A), gates and accounts complete and persist it (B), the scoring service applies it to real listings (C), and persistence plus comparison lets a user rank houses (D).

## Phase index

| Phase | Plan | Outcome |
|---|---|---|
| A | [phase-a-quiz-rubric.md](phase-a-quiz-rubric.md) | A quiz session emits a schema-valid rubric and a shareable reveal, persisted anonymously. |
| B | [phase-b-gates-accounts.md](phase-b-gates-accounts.md) | Gates plus accounts plus anonymous to account merge, with versioned rubrics. |
| C | [phase-c-scoring-service.md](phase-c-scoring-service.md) | Parse, analyze, and score a pasted listing; two rubrics differ on the same house. |
| D | [phase-d-persistence-comparison.md](phase-d-persistence-comparison.md) | Persist scores and rank listings in a comparison view. |
| Cross | [preference-neutrality.md](preference-neutrality.md) | The three-places neutrality hard requirement, spanning A and C. |
| A image bank | [illustration-bank.md](illustration-bank.md) | The token-driven parametric illustration system for the quiz images, where neutrality is structural. |

## Dependency order

Phase A is independent and client-only, so it can start immediately once the quiz prototype is in the tree.
Phase B depends on A's anonymous rubric and stands up `users` and `rubrics` persistence.
Phase C depends on the rubric shape being stable and extends the existing pure engine; its parse step is independent of A and B.
Phase D depends on C's `ScoreResult` and on B's persistence and auth.
Preference neutrality is not sequential; it constrains A and C throughout and gates the quiz via the bias smoke test.

## Cross-phase constraints to hold

The rubric object is the single contract between the quiz and the scorer, so its shape in `packages/contracts` is the source of truth for both web and Python.
The `item_weights` key vocabulary must be agreed jointly by Phase A and Phase C, since both reference the same item keys.
Rubric versioning is not optional polish: every score records the rubric version that produced it, so tuning never rewrites history.
The vision layer is preference-agnostic; personalization enters only through the rubric.

## Missing companion files (surfaced, not blocking the plans)

The build spec references companion files that are not in the repo and are prerequisites for specific phases.
`house-flavor-quiz.jsx` is the quiz prototype and blocks the start of Phase A until obtained or reconstructed.
`scoring-contract.md` (the authoritative vision prompt, observation schema, style vocabulary, and match mapping) is now written at [docs/scoring-contract.md](../scoring-contract.md); Phase C's remaining work is building the vision integration against it, not obtaining it.
`quiz-to-scores-pipeline.md` and `listing-scorer-app-plan.md` are design references that inform A through D.
`reno-estimator.md` is out of scope and stays tabled behind a clean seam in Phase C's value category.

## Open decisions carried across phases

Question-bank size for a stable rubric, target roughly 8 to 12 picks (Phase A).
Category-weight floors and ceilings so one category cannot swamp the score (Phase A).
Archetype set as a fixed display set the rubric snaps to, recommended over emergent clusters (Phase A).
Auth technology, unspecified by the spec and chosen in Phase B.
The split of table ownership between Phase B and Phase D (Phase B owns `users` and `rubrics`, Phase D owns the rest).
Photo-selection logic for analysis and the two-tier model split (Phase C).

## Engine gaps Phase C has closed

The engine now normalizes using the rubric's personalized `category_weights` instead of a hardcoded budget table.
The categorical match tables and thresholds live in `services/scoring/app/scoring/scoring_config.json`, so tuning does not require a code change.
The value category (budget-headroom stub) and the due-diligence checklist are implemented.
Confidence follows the frozen single 0.5 threshold: a low-confidence finding is scored at its observed value and added to the checklist as a verify item, with no silent value adjustment.

What remains open in Phase C is building the live two-tier Claude vision analyzer against the now-written [scoring contract](../scoring-contract.md), and expanding the observation schema and style vocabulary to match it.
The analyze endpoint has the photoset-hash cache and a pluggable analyzer seam ready for it.

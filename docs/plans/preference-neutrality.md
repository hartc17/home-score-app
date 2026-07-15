# Preference Neutrality - Cross-cutting Hard Requirement

Neutrality is not polish, it is what makes the rubric trustworthy and the product defensible.
The instrument must be neutral in three places, and a bias in any one corrupts the result.
This document is referenced by Phase A (the quiz) and Phase C (the vision and match layers), and both phases must satisfy it.

## The architectural invariant

The vision layer is preference-agnostic and produces identical observations for every user.
All personalization enters through exactly one door: the rubric.
Never hardcode any taste (no example buyer's preferences) into prompts, match functions, or defaults.
A useful phrasing to test against: if you can point to a taste baked into the vision prompt, a match function, or a default weight, that is a bug.

## The three places

### 1. Words

No leading option captions in the quiz.
Use neutral axis labels: `Cool` to `Warm`, never `sterile` or `clinical`.
Center or axis labels must not name one pole, so use `Tone`, not `Warmth`.
Every archetype's reveal copy must read as a flattering identity.
Audit names like `The Purist` and `The Classicist` so they feel as desirable as `The Hearthkeeper`.

### 2. Images

Every pair needs a warm option that a warm-lover picks and a cool option that a minimalist picks, each shot at its most flattering.
Curation test: show the two photos to a stranger with no words, and check that the intended contrast is obvious and that neither photo is the prettier one.
If a photo wins only because it is better shot, replace it.
Because Phase A ships with SVG stand-ins, structure the question bank so swapping an SVG for a photo URL is a single field change, then apply this curation test when the real photo bank lands.

### 3. Math

Indifference must zero out an axis by down-weighting it, never average to a misleading middle.
Directions are inferred from consistency of picks, never defaulted.
On the scoring side, the match function `M` is preference-neutral machinery parameterized by the user's direction, so the same observation yields opposite matches for opposite directions and nothing else.

## The bias smoke test

Add a synthetic random-choice session runner to CI.
Run many sessions that pick randomly, then aggregate the resulting archetypes.
The aggregate should be roughly uniform across the taste space.
A skew (for example toward warm) means bias is still hiding in words, images, or math, so hunt it down before shipping.
This test lives in the web suite for Phase A and gates the quiz.

## Neutrality checks per phase

Phase A: neutral prompts and labels, no captions, flattering archetype copy, indifference down-weights, directions inferred from consistency, bias smoke test in CI.
Phase C: vision prompt returns observations and ratings and never scores, the same photo yields the same observations regardless of rubric, and match functions carry no baked-in taste.
Add a Phase C test that identical observations run through two opposite-direction rubrics produce mirror-image matches, proving personalization lives only in the rubric.

## Acceptance checklist

- [ ] Quiz has no option captions and no pole-naming center labels.
- [ ] Every archetype reveal reads as flattering, audited explicitly.
- [ ] Question bank supports a one-field SVG to photo swap, and the curation test is documented for the photo bank.
- [ ] Indifferent axes down-weight; directions come from consistency, never defaults.
- [ ] Bias smoke test runs in CI and aggregate archetypes are roughly uniform.
- [ ] Vision observations are identical across users for the same photos.
- [ ] No taste is hardcoded in any prompt, match function, or default.

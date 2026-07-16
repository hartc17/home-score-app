# Illustration Bank - Phase A image system

The quiz image bank is a deliberate, consistent illustration style rather than photography.
This route was chosen over a licensed photo bank because it gives an ownable visual signature, no uncanny-realism QA, no licensing, and, the decisive reason, it makes neutrality structural.

## Why illustration makes neutrality structural

Each room is a parametric drawing themed by tokens.
The warm and cool variants are the same geometry with a palette swap, so neither can be better lit, better composed, or more lovingly rendered than the other.
The bias you would have to police in photos (see [preference-neutrality.md](preference-neutrality.md)) is designed out.

Tone lives in the palette tokens, era lives in the motif tokens, and the warm and cool palettes are matched in lightness and contrast, not raw saturation.
Forcing equal saturation would blue-tint the cool palette and make it read clinical, which biases against cool.
Instead cool is tuned as an elegant warm-leaning neutral and warm as a muted sophistication, with equal accent count and only the accent pop saturation-matched.

## The two axes and the pair rule

Tone is a palette token swap (warm woods, brick, textiles versus cool greys, stone, off-white), matched in richness.
Era is a motif token swap (traditional forms like raised-panel, molding, gable, and ornament versus modern forms like flat fronts, clean lines, and minimal detail), applied to the same base geometry.

Each pair holds one axis fixed so a pick is cleanly attributable: a tone pair is same-era, an era pair is same-tone.
The palette and naturalness axes ride on two matched controls (`wall`: light versus color, and `material`: natural versus engineered) that vary nothing else in the pair.

## Base rooms

Six base rooms, each drawn once and themed across the warm/cool by traditional/modern matrix: living, kitchen, bedroom, facade, backyard, and walls/focal detail.

## Implementation

The engine lives in `apps/web/src/quiz/scene/`.

- `tokens.ts` holds the neutral tokens (shared by both poles so greenery and glazing never become a warmth cue), the warm and cool palettes matched in lightness, and the saturation-matched accent pair.
- `spec.ts` defines the `SceneSpec` (base, tone, era, and the matched `wall`/`material` controls) and `sceneId`, the `B{n}-{tone}-{era}` provenance id tagged onto every rendered scene for the vision QA pre-screen.
- `Scene.tsx` composes each base once from flat-illustration primitives and themes it by the tokens, with a fixed perspective, line weight, and single soft-shadow style across the whole set.

`questions.ts` references a scene per option, and each pair isolates one axis.
`OptionImage.tsx` is the swap seam: it renders the scene, or a curated photo if an option ever sets one.

## QA gates

- Style consistency: every scene obeys the fixed perspective, line, and shadow style. With token-driven SVG this is automatic.
- Neutrality within a pair: same geometry, palettes matched in lightness and contrast, equal staging and accent count, no pole prettier or more dominant. Enforced in part by `tokens.test.ts`.
- Axis isolation within a pair: differs only on the intended axis. Enforced by the pair construction in `questions.ts`.
- Automated pre-screen: run each scene through the vision model to confirm each pair isolates its axis and neither pole reads as more dominant. The scoring model QA's its own future inputs. This runs on real users as the bias smoke test.

## Provenance

Self-authored SVG sidesteps licensing entirely, so the bank is a clean, owned data asset rather than a generated or stock path.

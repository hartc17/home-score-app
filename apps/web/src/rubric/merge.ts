import type { Rubric, RubricGates } from "@houseflavor/contracts";

// Stated gates must never overwrite the quiz-derived parts of a rubric.
// See docs/plans/phase-b-gates-accounts.md.
export function mergeGates(rubric: Rubric, gates: RubricGates): Rubric {
  return { ...rubric, gates };
}

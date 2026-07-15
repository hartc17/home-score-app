import type { Rubric, RubricGates } from "@houseflavor/contracts";

// The quiz-derived parts of a rubric. Gates are stated separately and must never
// overwrite these. See docs/plans/phase-b-gates-accounts.md.
const QUIZ_KEYS = ["category_weights", "item_weights", "directions", "archetype", "confidence"] as const;

function hasQuizSignal(rubric: Rubric): boolean {
  return Object.keys(rubric.item_weights).length > 0;
}

export function mergeGates(rubric: Rubric, gates: RubricGates): Rubric {
  return { ...rubric, gates };
}

// Compose an anonymous quiz rubric forward into an existing account rubric on signup.
// Quiz-derived weights and directions come from whichever side actually took the quiz,
// preferring the just-completed anonymous rubric. Stated gates are preserved, preferring
// the account's own gates. Neither side clobbers the other.
export function composeForward(anonymous: Rubric, account: Rubric): Rubric {
  const quizSource = hasQuizSignal(anonymous) ? anonymous : account;
  const merged: Rubric = {
    version: quizSource.version,
    gates: account.gates ?? anonymous.gates,
    category_weights: quizSource.category_weights,
    item_weights: quizSource.item_weights,
    directions: quizSource.directions,
    archetype: quizSource.archetype,
    confidence: quizSource.confidence,
  };
  return merged;
}

export { QUIZ_KEYS };

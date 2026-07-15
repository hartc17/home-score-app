import { describe, expect, it } from "vitest";
import type { Rubric, RubricGates } from "@houseflavor/contracts";
import { composeForward, mergeGates } from "./merge.ts";
import { inferRubric } from "../quiz/inference.ts";
import { QUESTIONS } from "../quiz/questions.ts";

const quizRubric = inferRubric(QUESTIONS.map((q) => q.options[0]));

const gates: RubricGates = {
  budget_max: 600000,
  districts: ["Saratoga Springs"],
  min_beds: 3,
  min_baths: 2,
  min_garage: 2,
  exclude_main_road: true,
  home_types: ["single_family"],
};

function emptyRubric(): Rubric {
  return {
    version: "1.0",
    category_weights: { bones: 17, warmth: 17, finish: 16, outdoor: 17, value: 17, age: 16 },
    item_weights: {},
    directions: {},
    archetype: { name: "none", blend: {} },
    confidence: {},
  };
}

describe("mergeGates", () => {
  it("test_merge_gates_adds_gates_and_keeps_quiz_parts", () => {
    const merged = mergeGates(quizRubric, gates);
    expect(merged.gates).toEqual(gates);
    expect(merged.item_weights).toEqual(quizRubric.item_weights);
    expect(merged.directions).toEqual(quizRubric.directions);
    expect(merged.archetype).toEqual(quizRubric.archetype);
  });
});

describe("composeForward", () => {
  it("test_compose_keeps_quiz_parts_and_account_gates", () => {
    const account = mergeGates(emptyRubric(), gates);
    const merged = composeForward(quizRubric, account);
    expect(merged.item_weights).toEqual(quizRubric.item_weights);
    expect(merged.directions).toEqual(quizRubric.directions);
    expect(merged.gates).toEqual(gates);
  });

  it("test_compose_does_not_overwrite_quiz_with_empty_account", () => {
    const merged = composeForward(quizRubric, emptyRubric());
    expect(merged.item_weights).toEqual(quizRubric.item_weights);
    expect(merged.archetype.name).toBe(quizRubric.archetype.name);
  });

  it("test_compose_preserves_account_quiz_when_anonymous_has_none", () => {
    const account = mergeGates(quizRubric, gates);
    const anonEmpty = emptyRubric();
    const merged = composeForward(anonEmpty, account);
    expect(merged.item_weights).toEqual(quizRubric.item_weights);
    expect(merged.gates).toEqual(gates);
  });

  it("test_compose_prefers_anonymous_gates_when_account_has_none", () => {
    const anonWithGates = mergeGates(quizRubric, gates);
    const merged = composeForward(anonWithGates, emptyRubric());
    expect(merged.gates).toEqual(gates);
  });
});

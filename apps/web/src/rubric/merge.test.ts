import { describe, expect, it } from "vitest";
import type { RubricGates } from "@houseflavor/contracts";
import { mergeGates } from "./merge.ts";
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

describe("mergeGates", () => {
  it("test_merge_gates_adds_gates_and_keeps_quiz_parts", () => {
    const merged = mergeGates(quizRubric, gates);
    expect(merged.gates).toEqual(gates);
    expect(merged.item_weights).toEqual(quizRubric.item_weights);
    expect(merged.directions).toEqual(quizRubric.directions);
    expect(merged.archetype).toEqual(quizRubric.archetype);
  });
});

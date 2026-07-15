import { describe, expect, it } from "vitest";
import { inferProfile, inferRubric, archetypeCopy } from "./inference.ts";
import { CATEGORY_ITEMS, SIGNAL_CATEGORIES, type Category } from "./categories.ts";
import { QUESTIONS, type QuizOption } from "./questions.ts";
import { AXIS_IDS, type AxisId } from "./axes.ts";

function primaryAxis(qIndex: number): AxisId {
  const opt = QUESTIONS[qIndex].options[0];
  for (const axis of AXIS_IDS) {
    if (typeof opt.d[axis] === "number") return axis;
  }
  throw new Error(`question ${qIndex} has no primary axis`);
}

function chooseBySign(qIndex: number, sign: number): QuizOption {
  const axis = primaryAxis(qIndex);
  const [a, b] = QUESTIONS[qIndex].options;
  return (a.d[axis] as number) * sign > 0 ? a : b;
}

function session(strategy: (qIndex: number) => 0 | 1): QuizOption[] {
  return QUESTIONS.map((q, i) => q.options[strategy(i)]);
}

function allSign(sign: number): QuizOption[] {
  return QUESTIONS.map((_, i) => chooseBySign(i, sign));
}

function lcg(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 2 ** 32;
  };
}

describe("inferProfile directions", () => {
  it("test_infer_all_positive_condition_warm_traditional_strong", () => {
    const { rubric, axes } = inferProfile(allSign(1));
    expect(rubric.directions.tone).toBe("warm");
    expect(rubric.directions.era).toBe("traditional");
    expect(rubric.directions.walls).toBe("white_preferred");
    expect(rubric.directions.ornament).toBe("minimal");
    expect(rubric.directions.naturalness).toBe("natural");
    expect(axes.tone.band).toBe("strong");
    expect(axes.era.band).toBe("strong");
    expect(rubric.archetype.name).toBe("The Hearthkeeper");
  });

  it("test_infer_all_negative_condition_cool_modern_strong", () => {
    const { rubric, axes } = inferProfile(allSign(-1));
    expect(rubric.directions.tone).toBe("cool");
    expect(rubric.directions.era).toBe("modern");
    expect(rubric.directions.walls).toBe("color_preferred");
    expect(rubric.directions.ornament).toBe("ornate");
    expect(rubric.directions.naturalness).toBe("engineered");
    expect(axes.tone.band).toBe("strong");
    expect(rubric.archetype.name).toBe("The Minimalist");
  });

  it("test_infer_alternating_tone_downweights_tone_axis", () => {
    // Alternate on tone questions, stay consistent elsewhere.
    const picks = session((i) => (primaryAxis(i) === "tone" ? ((i % 2) as 0 | 1) : 0));
    const { rubric, axes } = inferProfile(picks);
    expect(axes.tone.band).toBe("none");
    expect(rubric.directions.tone).toBeUndefined();
  });

  it("test_infer_alternating_all_condition_curator_no_directions", () => {
    // Alternate the sign per axis so every axis nets to zero.
    const toggle: Record<AxisId, number> = { tone: 1, era: 1, palette: 1, ornament: 1, naturalness: 1 };
    const picks = QUESTIONS.map((_, i) => {
      const axis = primaryAxis(i);
      const sign = toggle[axis];
      toggle[axis] *= -1;
      return chooseBySign(i, sign);
    });
    const { rubric } = inferProfile(picks);
    expect(rubric.archetype.name).toBe("The Curator");
    expect(rubric.directions.tone).toBeUndefined();
    expect(rubric.directions.era).toBeUndefined();
    expect(rubric.directions.walls).toBeUndefined();
    expect(rubric.directions.ornament).toBeUndefined();
    expect(rubric.directions.naturalness).toBeUndefined();
  });

  it("test_infer_all_positive_sets_new_axes_strong", () => {
    const { axes } = inferProfile(allSign(1));
    expect(axes.ornament.band).toBe("strong");
    expect(axes.naturalness.band).toBe("strong");
  });

  it("test_infer_alternating_ornament_downweights_ornament_axis", () => {
    const picks = session((i) => (primaryAxis(i) === "ornament" ? ((i % 2) as 0 | 1) : 0));
    const { rubric, axes } = inferProfile(picks);
    expect(axes.ornament.band).toBe("none");
    expect(rubric.directions.ornament).toBeUndefined();
  });
});

describe("inferProfile rubric shape", () => {
  it("test_category_weights_sum_to_100", () => {
    const rubric = inferRubric(allSign(1));
    const total = Object.values(rubric.category_weights).reduce((a, b) => a + b, 0);
    expect(total).toBe(100);
  });

  it("test_item_weights_sum_to_their_category_weight", () => {
    const rubric = inferRubric(allSign(1));
    for (const cat of SIGNAL_CATEGORIES) {
      const budget = (rubric.category_weights as unknown as Record<Category, number>)[cat];
      const sum = CATEGORY_ITEMS[cat].reduce((a, t) => a + (rubric.item_weights[t] ?? 0), 0);
      expect(sum).toBeCloseTo(budget, 6);
    }
  });

  it("test_item_weights_keys_match_engine_vocabulary", () => {
    const rubric = inferRubric(allSign(1));
    const known = new Set(SIGNAL_CATEGORIES.flatMap((c) => CATEGORY_ITEMS[c]));
    for (const key of Object.keys(rubric.item_weights)) {
      expect(known.has(key as never)).toBe(true);
    }
  });

  it("test_infer_rubric_equals_profile_rubric", () => {
    const picks = allSign(1);
    expect(inferRubric(picks)).toEqual(inferProfile(picks).rubric);
  });

  it("test_archetype_copy_present_for_known_name", () => {
    expect(archetypeCopy("The Hearthkeeper").length).toBeGreaterThan(0);
  });
});

describe("bias smoke test", () => {
  it("test_random_sessions_have_no_directional_skew", () => {
    const rnd = lcg(12345);
    const N = 500;
    const sums: Record<AxisId, number> = { tone: 0, era: 0, palette: 0, ornament: 0, naturalness: 0 };
    let warm = 0;
    let cool = 0;
    let traditional = 0;
    let modern = 0;

    for (let n = 0; n < N; n++) {
      const { axes } = inferProfile(session(() => (rnd() < 0.5 ? 0 : 1)));
      for (const axis of AXIS_IDS) sums[axis] += axes[axis].signedStrength;
      if (axes.tone.signedStrength > 0.34) warm++;
      else if (axes.tone.signedStrength < -0.34) cool++;
      if (axes.era.signedStrength > 0.34) traditional++;
      else if (axes.era.signedStrength < -0.34) modern++;
    }

    // No pole on any axis should be systematically favored: every mean sits near zero.
    for (const axis of AXIS_IDS) {
      expect(Math.abs(sums[axis] / N)).toBeLessThan(0.1);
    }

    // Decisive sessions should split evenly between opposing poles.
    expect(Math.abs(warm - cool) / N).toBeLessThan(0.12);
    expect(Math.abs(traditional - modern) / N).toBeLessThan(0.12);
  });
});

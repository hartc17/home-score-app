import type { Rubric, RubricDirections, CategoryWeights } from "@houseflavor/contracts";
import { AXES, AXIS_IDS, AXIS_TO_DIRECTION, type AxisId } from "./axes.ts";
import { CATEGORIES, CATEGORY_ITEMS, SIGNAL_CATEGORIES, type Category, type Tag } from "./categories.ts";
import { QUESTIONS, type QuizOption } from "./questions.ts";

// How often each item is offered by the fixed instrument. Used to turn a raw pick
// count into an affinity in [0, 1] that is neutral under random answering (~0.5).
const OPPORTUNITY: Partial<Record<Tag, number>> = (() => {
  const counts: Partial<Record<Tag, number>> = {};
  for (const q of QUESTIONS) {
    const seen = new Set<Tag>();
    for (const opt of q.options) for (const t of opt.tags) seen.add(t);
    for (const t of seen) counts[t] = (counts[t] ?? 0) + 1;
  }
  return counts;
})();

export type StrengthBand = "strong" | "slight" | "none";

export interface AxisStat {
  axis: AxisId;
  netSum: number;
  count: number;
  signedStrength: number; // net / total signal, in [-1, 1]
  strength: number; // |signedStrength|, in [0, 1]
  coverage: number; // how much data fed this axis, in [0, 1]
  confidence: number;
  band: StrengthBand;
  direction: string | null; // resolved pole label, or null when indifferent
}

export interface TasteProfile {
  rubric: Rubric;
  axes: Record<AxisId, AxisStat>;
}

interface Archetype {
  name: string;
  tone: number;
  era: number;
  blend: Record<string, number>;
  copy: string;
}

const ARCHETYPES: Archetype[] = [
  {
    name: "The Hearthkeeper",
    tone: 1,
    era: 1,
    blend: { farmhouse: 0.6, craftsman: 0.4 },
    copy: "You are drawn to rooms that hold warmth: natural materials, a hearth, and light that softens as the day ends.",
  },
  {
    name: "The Classicist",
    tone: -1,
    era: 1,
    blend: { colonial: 0.6, tudor: 0.4 },
    copy: "You gravitate to composure and proportion: rooms with a considered, timeless order that never chases a trend.",
  },
  {
    name: "The Warm Modernist",
    tone: 1,
    era: -1,
    blend: { modern: 0.6, craftsman: 0.4 },
    copy: "You like clean lines that still feel lived in: open, current spaces softened with wood and warmth.",
  },
  {
    name: "The Minimalist",
    tone: -1,
    era: -1,
    blend: { modern: 0.7, ranch: 0.3 },
    copy: "You value clarity and calm: uncluttered rooms, cool light, and finishes that let the space breathe.",
  },
  {
    name: "The Curator",
    tone: 0,
    era: 0,
    blend: { craftsman: 0.4, modern: 0.3, farmhouse: 0.3 },
    copy: "You read each room on its own terms, blending warmth and restraint rather than committing to a single look.",
  },
];

const BASE_WEIGHT = 100 / 6;
const WEIGHT_SPREAD = 24;
const WEIGHT_FLOOR = 4;
const INDIFFERENT_CORE = 0.34;

function apportion(total: number, weights: number[], decimals = 0): number[] {
  const factor = 10 ** decimals;
  const clamped = weights.map((w) => Math.max(0, w));
  const sum = clamped.reduce((a, b) => a + b, 0) || 1;
  const ideal = clamped.map((w) => (w / sum) * total * factor);
  const floors = ideal.map((v) => Math.floor(v));
  const target = Math.round(total * factor);
  let remainder = target - floors.reduce((a, b) => a + b, 0);
  const order = ideal
    .map((v, i) => ({ i, frac: v - Math.floor(v) }))
    .sort((a, b) => b.frac - a.frac);
  for (let k = 0; k < order.length && remainder > 0; k++, remainder--) {
    floors[order[k].i] += 1;
  }
  return floors.map((f) => f / factor);
}

function axisStat(axis: AxisId, picks: QuizOption[]): AxisStat {
  const deltas = picks.map((p) => p.d[axis]).filter((d): d is number => typeof d === "number" && d !== 0);
  const netSum = deltas.reduce((a, b) => a + b, 0);
  const absSum = deltas.reduce((a, b) => a + Math.abs(b), 0);
  const count = deltas.length;
  const signedStrength = absSum === 0 ? 0 : netSum / absSum;
  const strength = Math.abs(signedStrength);
  const coverage = Math.min(1, count / 3);
  const confidence = Number((strength * coverage).toFixed(2));
  const band: StrengthBand = strength >= 0.66 && count >= 2 ? "strong" : strength >= 0.25 ? "slight" : "none";
  const poles = AXES[axis];
  const direction = band === "none" ? null : signedStrength > 0 ? poles.pos : poles.neg;
  return { axis, netSum, count, signedStrength, strength, coverage, confidence, band, direction };
}

function affinity(tag: Tag, picks: QuizOption[]): number {
  const opportunity = OPPORTUNITY[tag] ?? 0;
  if (opportunity === 0) return 0.5;
  const chosen = picks.filter((p) => p.tags.includes(tag)).length;
  return chosen / opportunity;
}

function categoryEmphasis(cat: Category, picks: QuizOption[]): number {
  const items = CATEGORY_ITEMS[cat];
  if (items.length === 0) return 0.5;
  const mean = items.reduce((a, t) => a + affinity(t, picks), 0) / items.length;
  return mean;
}

function buildDirections(axes: Record<AxisId, AxisStat>): RubricDirections {
  const directions: RubricDirections = {};
  for (const axis of AXIS_IDS) {
    const dir = axes[axis].direction;
    if (dir === null) continue;
    switch (AXIS_TO_DIRECTION[axis]) {
      case "tone":
        directions.tone = dir as "warm" | "cool";
        break;
      case "era":
        directions.era = dir as "traditional" | "modern";
        break;
      case "walls":
        directions.walls = dir as "white_preferred" | "color_preferred";
        break;
      case "ornament":
        directions.ornament = dir as "minimal" | "ornate";
        break;
      case "naturalness":
        directions.naturalness = dir as "natural" | "engineered";
        break;
    }
  }
  return directions;
}

function pickArchetype(tone: number, era: number): Archetype {
  if (Math.abs(tone) < INDIFFERENT_CORE && Math.abs(era) < INDIFFERENT_CORE) {
    return ARCHETYPES[ARCHETYPES.length - 1];
  }
  const corners = ARCHETYPES.filter((a) => a.tone !== 0 || a.era !== 0);
  let best = corners[0];
  let bestDist = Infinity;
  for (const a of corners) {
    const dist = (a.tone - tone) ** 2 + (a.era - era) ** 2;
    if (dist < bestDist) {
      bestDist = dist;
      best = a;
    }
  }
  return best;
}

export function inferProfile(picks: QuizOption[]): TasteProfile {
  const axes = Object.fromEntries(AXIS_IDS.map((axis) => [axis, axisStat(axis, picks)])) as Record<
    AxisId,
    AxisStat
  >;

  const rawCategory = CATEGORIES.map((cat) => {
    const emphasis = categoryEmphasis(cat, picks);
    return Math.max(WEIGHT_FLOOR, BASE_WEIGHT + WEIGHT_SPREAD * (emphasis - 0.5));
  });
  const categoryInts = apportion(100, rawCategory, 0);
  const weightOf = (cat: Category): number => categoryInts[CATEGORIES.indexOf(cat)];
  const categoryWeights: CategoryWeights = {
    bones: weightOf("bones"),
    warmth: weightOf("warmth"),
    finish: weightOf("finish"),
    outdoor: weightOf("outdoor"),
    value: weightOf("value"),
    age: weightOf("age"),
  };

  const itemWeights: Record<string, number> = {};
  for (const cat of SIGNAL_CATEGORIES) {
    const items = CATEGORY_ITEMS[cat];
    const budget = categoryWeights[cat];
    const raw = items.map((t) => 0.5 + affinity(t, picks));
    const parts = apportion(budget, raw, 2);
    items.forEach((t, i) => {
      itemWeights[t] = parts[i];
    });
  }

  const confidence: Record<string, number> = {};
  for (const cat of SIGNAL_CATEGORIES) {
    const items = CATEGORY_ITEMS[cat];
    const decisiveness = items.reduce((a, t) => a + Math.abs(affinity(t, picks) - 0.5) * 2, 0) / items.length;
    const coverage = items.reduce((a, t) => a + Math.min(1, (OPPORTUNITY[t] ?? 0) / 2), 0) / items.length;
    confidence[cat] = Number((decisiveness * coverage).toFixed(2));
  }

  const archetype = pickArchetype(axes.tone.signedStrength, axes.era.signedStrength);

  const rubric: Rubric = {
    version: "1.0",
    category_weights: categoryWeights,
    item_weights: itemWeights,
    directions: buildDirections(axes),
    archetype: { name: archetype.name, blend: archetype.blend },
    confidence,
  };

  return { rubric, axes };
}

export function inferRubric(picks: QuizOption[]): Rubric {
  return inferProfile(picks).rubric;
}

export function archetypeCopy(name: string): string {
  return ARCHETYPES.find((a) => a.name === name)?.copy ?? "";
}

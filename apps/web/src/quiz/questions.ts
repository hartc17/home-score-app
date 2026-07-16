import type { AxisId } from "./axes.ts";
import type { Tag } from "./categories.ts";
import type { SceneSpec } from "./scene/spec.ts";

export interface QuizOption {
  id: string;
  // The parametric scene to draw. A curated photo can override it later by
  // setting `photo`; swapping one field per option is the whole change.
  scene: SceneSpec;
  photo?: string;
  d: Partial<Record<AxisId, number>>;
  tags: Tag[];
}

export interface Question {
  id: string;
  // Neutral framing only. Never names a pole and never captions the options.
  prompt: string;
  options: [QuizOption, QuizOption];
}

export function optionsByIds(ids: string[]): QuizOption[] {
  const lookup = new Map(QUESTIONS.flatMap((q) => q.options.map((o) => [o.id, o] as const)));
  return ids.map((id) => lookup.get(id)).filter((o): o is QuizOption => o !== undefined);
}

// Each pair holds every axis fixed but the one it tests, so a pick is cleanly
// attributable (illustration-kit v2, section 1). Tone pairs share an era; era
// and ornament pairs share a tone; palette pairs vary only the wall treatment;
// naturalness pairs vary only the material.
export const QUESTIONS: Question[] = [
  {
    id: "q1",
    prompt: "Which room would you rather come home to?",
    options: [
      { id: "q1a", scene: { base: "living", tone: "warm", era: "modern" }, d: { tone: 2 }, tags: ["tone_warmth"] },
      { id: "q1b", scene: { base: "living", tone: "cool", era: "modern" }, d: { tone: -2 }, tags: ["natural_light"] },
    ],
  },
  {
    id: "q2",
    prompt: "Pick the space you'd want to sit in on a winter evening.",
    options: [
      { id: "q2a", scene: { base: "living", tone: "warm", era: "traditional" }, d: { tone: 2 }, tags: ["fireplace"] },
      { id: "q2b", scene: { base: "living", tone: "cool", era: "traditional" }, d: { tone: -2 }, tags: ["ceiling_height"] },
    ],
  },
  {
    id: "q3",
    prompt: "Choose the kitchen you'd cook in most nights.",
    options: [
      { id: "q3a", scene: { base: "kitchen", tone: "warm", era: "traditional" }, d: { era: 2 }, tags: ["cabinets"] },
      { id: "q3b", scene: { base: "kitchen", tone: "warm", era: "modern" }, d: { era: -2 }, tags: ["counters"] },
    ],
  },
  {
    id: "q4",
    prompt: "Which kitchen would you keep as-is?",
    options: [
      { id: "q4a", scene: { base: "kitchen", tone: "cool", era: "traditional" }, d: { era: 2 }, tags: ["flooring"] },
      { id: "q4b", scene: { base: "kitchen", tone: "cool", era: "modern" }, d: { era: -2 }, tags: ["appliances"] },
    ],
  },
  {
    id: "q5",
    prompt: "Pick a wall.",
    options: [
      { id: "q5a", scene: { base: "walls", tone: "warm", era: "traditional", wall: "light" }, d: { palette: 2 }, tags: ["condition"] },
      { id: "q5b", scene: { base: "walls", tone: "warm", era: "traditional", wall: "color" }, d: { palette: -2 }, tags: ["natural_light"] },
    ],
  },
  {
    id: "q6",
    prompt: "Which exterior feels like home?",
    options: [
      { id: "q6a", scene: { base: "facade", tone: "cool", era: "traditional" }, d: { era: 2 }, tags: ["exterior_style"] },
      { id: "q6b", scene: { base: "facade", tone: "cool", era: "modern" }, d: { era: -2 }, tags: ["curb_appeal"] },
    ],
  },
  {
    id: "q7",
    prompt: "Choose a backyard.",
    options: [
      { id: "q7a", scene: { base: "backyard", tone: "warm", era: "modern" }, d: { tone: 1 }, tags: ["lot_character"] },
      { id: "q7b", scene: { base: "backyard", tone: "cool", era: "modern" }, d: { tone: -1 }, tags: ["garage_type"] },
    ],
  },
  {
    id: "q8",
    prompt: "Where would you rather spend a Saturday?",
    options: [
      { id: "q8a", scene: { base: "backyard", tone: "warm", era: "traditional" }, d: { tone: 1 }, tags: ["deck_patio"] },
      { id: "q8b", scene: { base: "backyard", tone: "cool", era: "traditional" }, d: { tone: -1 }, tags: ["curb_appeal"] },
    ],
  },
  {
    id: "q9",
    prompt: "Pick a bedroom.",
    options: [
      { id: "q9a", scene: { base: "bedroom", tone: "warm", era: "modern", wall: "light" }, d: { palette: 2 }, tags: ["condition"] },
      { id: "q9b", scene: { base: "bedroom", tone: "warm", era: "modern", wall: "color" }, d: { palette: -2 }, tags: ["cabinets"] },
    ],
  },
  {
    id: "q10",
    prompt: "Which one would you tour first?",
    options: [
      { id: "q10a", scene: { base: "living", tone: "warm", era: "traditional" }, d: { era: 2 }, tags: ["ceiling_height"] },
      { id: "q10b", scene: { base: "living", tone: "warm", era: "modern" }, d: { era: -2 }, tags: ["flooring"] },
    ],
  },
  {
    id: "q11",
    prompt: "Which detailing feels right?",
    options: [
      { id: "q11a", scene: { base: "kitchen", tone: "warm", era: "traditional" }, d: { ornament: -2 }, tags: ["cabinets"] },
      { id: "q11b", scene: { base: "kitchen", tone: "warm", era: "modern" }, d: { ornament: 2 }, tags: ["counters"] },
    ],
  },
  {
    id: "q12",
    prompt: "Pick the room that feels most like you.",
    options: [
      { id: "q12a", scene: { base: "living", tone: "cool", era: "traditional" }, d: { ornament: -2 }, tags: ["ceiling_height"] },
      { id: "q12b", scene: { base: "living", tone: "cool", era: "modern" }, d: { ornament: 2 }, tags: ["natural_light"] },
    ],
  },
  {
    id: "q13",
    prompt: "Which surfaces would you rather live with?",
    options: [
      { id: "q13a", scene: { base: "living", tone: "warm", era: "modern", material: "natural" }, d: { naturalness: 2 }, tags: ["flooring"] },
      { id: "q13b", scene: { base: "living", tone: "warm", era: "modern", material: "engineered" }, d: { naturalness: -2 }, tags: ["appliances"] },
    ],
  },
  {
    id: "q14",
    prompt: "Choose the setting you would relax in.",
    options: [
      { id: "q14a", scene: { base: "backyard", tone: "warm", era: "modern", material: "natural" }, d: { naturalness: 2 }, tags: ["lot_character"] },
      { id: "q14b", scene: { base: "backyard", tone: "warm", era: "modern", material: "engineered" }, d: { naturalness: -2 }, tags: ["deck_patio"] },
    ],
  },
];

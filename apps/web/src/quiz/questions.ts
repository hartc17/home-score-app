import type { AxisId } from "./axes.ts";
import type { Tag } from "./categories.ts";

// Visual spec for an SVG stand-in plate. To move to a curated photo bank later,
// replace this field with a photo URL and swap the renderer: a one-field change.
export interface PlateSpec {
  motif: "living" | "kitchen" | "exterior" | "yard" | "wall" | "bedroom";
  warm: boolean;
  ornate: boolean;
  lightWalls: boolean;
}

export interface QuizOption {
  id: string;
  plate: PlateSpec;
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

const base: Omit<PlateSpec, "motif"> = { warm: false, ornate: false, lightWalls: true };

export const QUESTIONS: Question[] = [
  {
    id: "q1",
    prompt: "Which room would you rather come home to?",
    options: [
      { id: "q1a", plate: { ...base, motif: "living", warm: true }, d: { tone: 2 }, tags: ["tone_warmth"] },
      { id: "q1b", plate: { ...base, motif: "living", warm: false }, d: { tone: -2 }, tags: ["natural_light"] },
    ],
  },
  {
    id: "q2",
    prompt: "Pick the space you'd want to sit in on a winter evening.",
    options: [
      { id: "q2a", plate: { ...base, motif: "living", warm: true }, d: { tone: 2 }, tags: ["fireplace"] },
      { id: "q2b", plate: { ...base, motif: "living", warm: false }, d: { tone: -2 }, tags: ["ceiling_height"] },
    ],
  },
  {
    id: "q3",
    prompt: "Choose the kitchen you'd cook in most nights.",
    options: [
      { id: "q3a", plate: { ...base, motif: "kitchen", warm: true, ornate: true }, d: { era: 2 }, tags: ["cabinets"] },
      { id: "q3b", plate: { ...base, motif: "kitchen", ornate: false }, d: { era: -2 }, tags: ["counters"] },
    ],
  },
  {
    id: "q4",
    prompt: "Which kitchen would you keep as-is?",
    options: [
      { id: "q4a", plate: { ...base, motif: "kitchen", warm: true, ornate: true }, d: { era: 2 }, tags: ["flooring"] },
      { id: "q4b", plate: { ...base, motif: "kitchen", ornate: false }, d: { era: -2 }, tags: ["appliances"] },
    ],
  },
  {
    id: "q5",
    prompt: "Pick a wall.",
    options: [
      { id: "q5a", plate: { ...base, motif: "wall", lightWalls: true }, d: { palette: 2 }, tags: ["condition"] },
      { id: "q5b", plate: { ...base, motif: "wall", warm: true, lightWalls: false }, d: { palette: -2 }, tags: ["natural_light"] },
    ],
  },
  {
    id: "q6",
    prompt: "Which exterior feels like home?",
    options: [
      { id: "q6a", plate: { ...base, motif: "exterior", warm: true, ornate: true }, d: { era: 2 }, tags: ["exterior_style"] },
      { id: "q6b", plate: { ...base, motif: "exterior", ornate: false }, d: { era: -2 }, tags: ["curb_appeal"] },
    ],
  },
  {
    id: "q7",
    prompt: "Choose a backyard.",
    options: [
      { id: "q7a", plate: { ...base, motif: "yard", warm: true }, d: { tone: 1 }, tags: ["lot_character"] },
      { id: "q7b", plate: { ...base, motif: "yard", warm: false }, d: { tone: -1 }, tags: ["garage_type"] },
    ],
  },
  {
    id: "q8",
    prompt: "Where would you rather spend a Saturday?",
    options: [
      { id: "q8a", plate: { ...base, motif: "yard", warm: true }, d: { tone: 1 }, tags: ["deck_patio"] },
      { id: "q8b", plate: { ...base, motif: "yard", warm: false }, d: { tone: -1 }, tags: ["curb_appeal"] },
    ],
  },
  {
    id: "q9",
    prompt: "Pick a bedroom.",
    options: [
      { id: "q9a", plate: { ...base, motif: "bedroom", lightWalls: true }, d: { palette: 2 }, tags: ["condition"] },
      { id: "q9b", plate: { ...base, motif: "bedroom", warm: true, lightWalls: false }, d: { palette: -2 }, tags: ["cabinets"] },
    ],
  },
  {
    id: "q10",
    prompt: "Which one would you tour first?",
    options: [
      { id: "q10a", plate: { ...base, motif: "living", warm: true, ornate: true }, d: { era: 2 }, tags: ["ceiling_height"] },
      { id: "q10b", plate: { ...base, motif: "living", ornate: false }, d: { era: -2 }, tags: ["flooring"] },
    ],
  },
  {
    id: "q11",
    prompt: "Which detailing feels right?",
    options: [
      { id: "q11a", plate: { ...base, motif: "kitchen", warm: true, ornate: true }, d: { ornament: -2 }, tags: ["cabinets"] },
      { id: "q11b", plate: { ...base, motif: "kitchen", ornate: false }, d: { ornament: 2 }, tags: ["counters"] },
    ],
  },
  {
    id: "q12",
    prompt: "Pick the room that feels most like you.",
    options: [
      { id: "q12a", plate: { ...base, motif: "living", ornate: true }, d: { ornament: -2 }, tags: ["ceiling_height"] },
      { id: "q12b", plate: { ...base, motif: "living", ornate: false }, d: { ornament: 2 }, tags: ["natural_light"] },
    ],
  },
  {
    id: "q13",
    prompt: "Which surfaces would you rather live with?",
    options: [
      { id: "q13a", plate: { ...base, motif: "living", warm: true }, d: { naturalness: 2 }, tags: ["flooring"] },
      { id: "q13b", plate: { ...base, motif: "living", lightWalls: true }, d: { naturalness: -2 }, tags: ["appliances"] },
    ],
  },
  {
    id: "q14",
    prompt: "Choose the setting you would relax in.",
    options: [
      { id: "q14a", plate: { ...base, motif: "yard", warm: true }, d: { naturalness: 2 }, tags: ["lot_character"] },
      { id: "q14b", plate: { ...base, motif: "yard" }, d: { naturalness: -2 }, tags: ["deck_patio"] },
    ],
  },
];

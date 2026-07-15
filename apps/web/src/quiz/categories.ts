export type Category = "bones" | "warmth" | "finish" | "outdoor" | "value" | "age";

// Item keys match the scoring engine's ITEM_CATEGORY vocabulary
// (services/scoring/app/scoring/engine.py). Keep these in sync across web and Python.
export type Tag =
  | "ceiling_height"
  | "natural_light"
  | "tone_warmth"
  | "fireplace"
  | "flooring"
  | "counters"
  | "cabinets"
  | "appliances"
  | "condition"
  | "curb_appeal"
  | "lot_character"
  | "deck_patio"
  | "garage_type"
  | "exterior_style";

export const CATEGORY_ITEMS: Record<Category, Tag[]> = {
  bones: ["ceiling_height", "natural_light"],
  warmth: ["tone_warmth", "fireplace"],
  finish: ["flooring", "counters", "cabinets", "appliances", "condition"],
  outdoor: ["curb_appeal", "lot_character", "deck_patio", "garage_type", "exterior_style"],
  value: [],
  age: [],
};

export const CATEGORIES: Category[] = ["bones", "warmth", "finish", "outdoor", "value", "age"];

// Categories the quiz produces a taste signal for. `value` and `age` are scored
// from facts later (Phase C), so the quiz asserts no per-item preference for them.
export const SIGNAL_CATEGORIES: Category[] = ["bones", "warmth", "finish", "outdoor"];

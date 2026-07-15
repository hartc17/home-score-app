export interface RubricGates {
  budget_max: number;
  districts: string[];
  min_beds: number;
  min_baths: number;
  min_garage: number;
  exclude_main_road: boolean;
  home_types: string[];
  timeline?: string;
}

export interface CategoryWeights {
  bones: number;
  warmth: number;
  finish: number;
  outdoor: number;
  value: number;
  age: number;
}

export type ItemWeights = Record<string, number>;

export interface RubricDirections {
  tone?: "warm" | "cool";
  era?: "traditional" | "modern";
  walls?: "white_preferred" | "color_preferred";
}

export interface RubricArchetype {
  name: string;
  blend: Record<string, number>;
}

export type RubricConfidence = Record<string, number>;

export interface Rubric {
  version: string;
  gates?: RubricGates;
  category_weights: CategoryWeights;
  item_weights: ItemWeights;
  directions: RubricDirections;
  archetype: RubricArchetype;
  confidence: RubricConfidence;
}

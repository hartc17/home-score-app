export interface StyleClassification {
  style: string;
  confidence: number;
}

export type ObservationValue = number | string | StyleClassification[] | null;

export interface ObservationItem {
  value: ObservationValue;
  confidence: number;
  not_observed?: boolean;
  flag?: string;
}

export interface RoomObservations {
  tone_warmth?: ObservationItem;       // 0-10 warm reading
  natural_light?: ObservationItem;     // 0-10
  ornamentation?: ObservationItem;     // 0 minimal ... 10 ornate
  wall_lightness?: ObservationItem;    // 0 dark ... 10 light
  ceiling_height?: ObservationItem;    // feet
  condition?: ObservationItem;         // 0-10
  interior_style?: ObservationItem;    // value: StyleClassification[]
  flooring?: ObservationItem;          // "hardwood" | "tile" | "carpet" | "laminate" | "vinyl" | ...
  counters?: ObservationItem;          // "granite" | "quartz" | "laminate" | "marble" | "tile" | ...
  cabinets?: ObservationItem;          // "wood_stained" | "painted_white" | "painted_color" | "dated" | ...
  appliances?: ObservationItem;        // "stainless" | "white" | "black" | "mixed" | ...
  fireplace?: ObservationItem;         // "wood" | "gas" | "electric" | "none" | "unverified_wood"
}

export interface ExteriorObservations {
  exterior_style?: ObservationItem;    // value: StyleClassification[]
  curb_appeal?: ObservationItem;       // 0-10
  roof_type?: ObservationItem;         // "gable" | "hip" | "flat" | "low_slope" | ...
  siding_material?: ObservationItem;   // "board_and_batten" | "shiplap" | "clapboard" | "brick" | ...
  symmetry?: ObservationItem;          // 0-10
  lot_character?: ObservationItem;     // "wooded" | "open" | "landscaped" | "minimal" | "waterfront"
  deck_patio?: ObservationItem;        // "deck_wood" | "deck_composite" | "patio_stone" | "patio_concrete" | "none"
  garage_type?: ObservationItem;       // "attached" | "detached" | "carport" | "none"
}

export interface PhotoObservations {
  room_type: string;
  observations: RoomObservations | ExteriorObservations;
}

export interface ListingObservations {
  photos: PhotoObservations[];
  overall_tone_warmth?: ObservationItem;
  overall_style?: ObservationItem;     // value: StyleClassification[]
  condition_summary?: ObservationItem;
  flags: string[];
  model: string;
  schema_version: string;
}

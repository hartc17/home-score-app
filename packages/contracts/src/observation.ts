export type ObservationValue = number | string | null;

export interface ObservationItem {
  value: ObservationValue;
  confidence: number;
  not_observed?: boolean;
  flag?: string;
}

export interface RoomObservations {
  tone_warmth?: ObservationItem;       // 0-10 warm reading
  flooring?: ObservationItem;          // "hardwood" | "tile" | "carpet" | "laminate" | "vinyl"
  ceiling_height?: ObservationItem;    // feet
  fireplace?: ObservationItem;         // "wood" | "gas" | "electric" | "none" | "unverified_wood"
  counters?: ObservationItem;          // "granite" | "quartz" | "laminate" | "marble" | "tile"
  cabinets?: ObservationItem;          // "wood_stained" | "painted_white" | "painted_color" | "dated"
  appliances?: ObservationItem;        // "stainless" | "white" | "black" | "mixed"
  natural_light?: ObservationItem;     // 0-10
  condition?: ObservationItem;         // 0-10
}

export interface ExteriorObservations {
  style?: ObservationItem;             // "farmhouse" | "craftsman" | "colonial" | "ranch" | "modern" | "tudor" | "cape_cod"
  curb_appeal?: ObservationItem;       // 0-10
  lot_character?: ObservationItem;     // "wooded" | "open" | "landscaped" | "minimal"
  deck_patio?: ObservationItem;        // "deck_wood" | "deck_composite" | "patio_stone" | "patio_concrete" | "none"
  garage_type?: ObservationItem;       // "attached" | "detached" | "none"
}

export interface PhotoObservations {
  room_type: string;
  observations: RoomObservations | ExteriorObservations;
}

export interface ListingObservations {
  photos: PhotoObservations[];
  overall_tone_warmth?: ObservationItem;
  condition_summary?: ObservationItem;
  flags: string[];
  model: string;
  schema_version: string;
}

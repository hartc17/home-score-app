import type { Tone } from "./spec.ts";

// Design tokens for the parametric scene bank (illustration-kit v2, section 10).
// Neutrality is structural: warm and cool are the same geometry with a palette
// swap, matched in lightness and contrast (never saturation), so neither pole
// can read as better lit or more lovingly rendered than the other.

export interface Neutral {
  ink: string;
  shadow: string;
  green1: string;
  green2: string;
  glass: string;
  sky: string;
}

// Shared by both poles so warmth never becomes a "life" cue: both rooms get
// plants, glazing, and sky from the same values.
export const NEUTRAL: Neutral = {
  ink: "#2B2F31",
  shadow: "rgba(0,0,0,0.10)",
  green1: "#6E8A5A",
  green2: "#4E6B45",
  glass: "#AEBEC0",
  sky: "#C4D0CE",
};

export interface Palette {
  floor: string;
  wall: string;
  primary: string;
  feature: string;
  metal: string;
  wood2: string;
  accent: string;
}

// Matched lightness across poles. Cool is an elegant warm-leaning neutral, not
// cold blue; warm is muted, not kitsch. Only `accent` is saturation-matched, so
// each pole gets exactly one equally-vivid pop.
const WARM: Palette = {
  floor: "#C6A576",
  wall: "#E7DECB",
  primary: "#C79A6E",
  feature: "#BA7F5E",
  metal: "#C8A96A",
  wood2: "#9A6E45",
  accent: "#B87A46",
};

const COOL: Palette = {
  floor: "#BCC0BE",
  wall: "#E6E9E8",
  primary: "#C4C8C7",
  feature: "#878D8D",
  metal: "#A9B1B2",
  wood2: "#C3C0B6",
  accent: "#4E90A4",
};

export function palette(tone: Tone): Palette {
  return tone === "warm" ? WARM : COOL;
}

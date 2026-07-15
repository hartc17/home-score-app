export type AxisId = "tone" | "era" | "palette" | "ornament" | "naturalness";

export type DirectionField = "tone" | "era" | "walls" | "ornament" | "naturalness";

export interface AxisPoles {
  neg: string;
  pos: string;
}

// Sign convention: a positive delta leans toward `pos`, negative toward `neg`.
// The pole labels are the rubric direction values, so they must match the
// `directions` unions in packages/contracts. Labels are neutral by design.
export const AXES: Record<AxisId, AxisPoles> = {
  tone: { neg: "cool", pos: "warm" },
  era: { neg: "modern", pos: "traditional" },
  palette: { neg: "color_preferred", pos: "white_preferred" },
  ornament: { neg: "ornate", pos: "minimal" },
  naturalness: { neg: "engineered", pos: "natural" },
};

export const AXIS_IDS: AxisId[] = ["tone", "era", "palette", "ornament", "naturalness"];

export const AXIS_TO_DIRECTION: Record<AxisId, DirectionField> = {
  tone: "tone",
  era: "era",
  palette: "walls",
  ornament: "ornament",
  naturalness: "naturalness",
};

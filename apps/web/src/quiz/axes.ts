export type AxisId = "tone" | "era" | "palette";

export interface AxisPoles {
  neg: string;
  pos: string;
}

// Sign convention: a positive delta leans toward `pos`, negative toward `neg`.
// Labels are neutral by design; neither pole is framed as better.
export const AXES: Record<AxisId, AxisPoles> = {
  tone: { neg: "cool", pos: "warm" },
  era: { neg: "modern", pos: "traditional" },
  palette: { neg: "color_preferred", pos: "white_preferred" },
};

export const AXIS_IDS: AxisId[] = ["tone", "era", "palette"];

export const AXIS_TO_DIRECTION: Record<AxisId, "tone" | "era" | "walls"> = {
  tone: "tone",
  era: "era",
  palette: "walls",
};

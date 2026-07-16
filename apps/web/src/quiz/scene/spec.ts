// A scene is a parametric room drawing. Tone swaps the palette, era swaps the
// motif set, and both apply to one fixed base geometry (illustration-kit v2).
// `wall` and `material` are the two matched controls that carry the palette and
// naturalness axes without disturbing the tone/era isolation of a pair.

export type SceneBase = "living" | "kitchen" | "bedroom" | "facade" | "backyard" | "walls";
export type Tone = "warm" | "cool";
export type Era = "traditional" | "modern";
export type WallTreatment = "light" | "color";
export type Material = "natural" | "engineered";

export interface SceneSpec {
  base: SceneBase;
  tone: Tone;
  era: Era;
  wall?: WallTreatment;
  material?: Material;
}

const BASE_NUMBER: Record<SceneBase, string> = {
  living: "B1",
  kitchen: "B2",
  bedroom: "B3",
  facade: "B4",
  backyard: "B5",
  walls: "B6",
};

// Stable identifier per the kit's `B{n}-{tone}-{era}` provenance scheme. Tagged
// onto every rendered scene so the vision QA pre-screen can name what it reads.
export function sceneId(spec: SceneSpec): string {
  const era = spec.era === "traditional" ? "trad" : "mod";
  return `${BASE_NUMBER[spec.base]}-${spec.tone}-${era}`;
}

import { describe, expect, it } from "vitest";
import { sceneId } from "./spec.ts";

describe("sceneId", () => {
  it("test_encodes_base_tone_and_era", () => {
    expect(sceneId({ base: "living", tone: "warm", era: "modern" })).toBe("B1-warm-mod");
    expect(sceneId({ base: "kitchen", tone: "cool", era: "traditional" })).toBe("B2-cool-trad");
    expect(sceneId({ base: "walls", tone: "warm", era: "traditional" })).toBe("B6-warm-trad");
  });

  it("test_ignores_wall_and_material_controls", () => {
    expect(sceneId({ base: "bedroom", tone: "cool", era: "modern", wall: "color", material: "engineered" })).toBe("B3-cool-mod");
  });
});

import { describe, expect, it } from "vitest";
import { palette, type Palette } from "./tokens.ts";

function channels(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function relativeLuminance(hex: string): number {
  const toLin = (c: number) => {
    const s = c / 255;
    return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  const [r, g, b] = channels(hex);
  return 0.2126 * toLin(r) + 0.7152 * toLin(g) + 0.0722 * toLin(b);
}

function saturationLightness(hex: string): { s: number; l: number } {
  const [r, g, b] = channels(hex).map((c) => c / 255);
  const mx = Math.max(r, g, b);
  const mn = Math.min(r, g, b);
  const l = (mx + mn) / 2;
  const s = mx === mn ? 0 : l > 0.5 ? (mx - mn) / (2 - mx - mn) : (mx - mn) / (mx + mn);
  return { s, l };
}

const SLOTS = ["floor", "wall", "primary", "feature", "metal", "wood2", "accent"] as const;

function meanLuminance(p: Palette): number {
  return SLOTS.reduce((a, s) => a + relativeLuminance(p[s]), 0) / SLOTS.length;
}

const warm = palette("warm");
const cool = palette("cool");

describe("palette neutrality", () => {
  // The kit's discipline: match scene-level lightness (not per-slot saturation),
  // so neither pole reads as darker or more dominant overall.
  it("test_overall_lightness_is_balanced_across_poles", () => {
    expect(Math.abs(meanLuminance(warm) - meanLuminance(cool))).toBeLessThan(0.12);
  });

  // Each pole gets exactly one equally-vivid pop: the accent is the one
  // saturation-matched pair (~S 40%, L 50%).
  it("test_accent_pops_match_in_saturation_and_lightness", () => {
    const w = saturationLightness(warm.accent);
    const c = saturationLightness(cool.accent);
    expect(Math.abs(w.s - c.s)).toBeLessThan(0.12);
    expect(Math.abs(w.l - c.l)).toBeLessThan(0.1);
  });

  it("test_poles_are_distinct_per_slot", () => {
    for (const slot of SLOTS) expect(warm[slot]).not.toBe(cool[slot]);
  });
});

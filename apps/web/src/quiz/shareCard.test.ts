import { describe, expect, it } from "vitest";
import { buildShareCardSvg } from "./shareCard.ts";

describe("buildShareCardSvg", () => {
  it("test_includes_archetype_name_and_blend_shares", () => {
    const svg = buildShareCardSvg("The Hearthkeeper", { farmhouse: 0.6, craftsman: 0.4 });
    expect(svg).toContain("The Hearthkeeper");
    expect(svg).toContain("farmhouse 60%");
    expect(svg).toContain("craftsman 40%");
  });

  it("test_orders_blend_by_share_descending", () => {
    const svg = buildShareCardSvg("The Modernist", { ranch: 0.3, modern: 0.7 });
    expect(svg.indexOf("modern 70%")).toBeLessThan(svg.indexOf("ranch 30%"));
  });

  it("test_declares_og_card_dimensions", () => {
    const svg = buildShareCardSvg("x", { modern: 1 });
    expect(svg).toContain('width="1200"');
    expect(svg).toContain('height="630"');
  });

  it("test_escapes_special_characters_in_name", () => {
    const svg = buildShareCardSvg("A & B <C>", { modern: 1 });
    expect(svg).toContain("A &amp; B &lt;C&gt;");
    expect(svg).not.toContain("<C>");
  });
});

import { afterEach, describe, expect, it, vi } from "vitest";
import type { Rubric } from "@houseflavor/contracts";
import { saveRubricToServer } from "./client.ts";

const rubric: Rubric = {
  version: "1.0",
  category_weights: { bones: 20, warmth: 20, finish: 20, outdoor: 20, value: 10, age: 10 },
  item_weights: { tone_warmth: 10 },
  directions: { tone: "warm" },
  archetype: { name: "x", blend: { x: 1 } },
  confidence: {},
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("saveRubricToServer", () => {
  it("test_posts_anon_id_and_rubric_and_returns_version", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ version: 3 }) });
    vi.stubGlobal("fetch", fetchMock);

    const version = await saveRubricToServer("anon-9", rubric);

    expect(version).toBe(3);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/rubrics");
    expect(JSON.parse(init.body)).toEqual({ anon_id: "anon-9", rubric });
  });

  it("test_returns_null_when_response_not_ok", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, json: async () => ({}) }));
    expect(await saveRubricToServer("anon-9", rubric)).toBeNull();
  });

  it("test_returns_null_when_fetch_throws", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    expect(await saveRubricToServer("anon-9", rubric)).toBeNull();
  });
});

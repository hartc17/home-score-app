import { afterEach, describe, expect, it, vi } from "vitest";
import type { Rubric } from "@houseflavor/contracts";
import { listScores, runScore, saveRubricToServer, ScoreError } from "./client.ts";

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

describe("runScore", () => {
  it("test_posts_url_and_returns_score_run", async () => {
    const body = { listing_id: 7, score: { total: 82 } };
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => body });
    vi.stubGlobal("fetch", fetchMock);

    const result = await runScore("anon-9", "https://example.com/a");

    expect(result).toEqual(body);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/scores/run");
    expect(JSON.parse(init.body)).toEqual({ anon_id: "anon-9", url: "https://example.com/a" });
  });

  it("test_throws_score_error_with_detail_on_failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({ detail: "no rubric" }) }));
    await expect(runScore("anon-9", "https://example.com/a")).rejects.toThrow(ScoreError);
    await expect(runScore("anon-9", "https://example.com/a")).rejects.toThrow("no rubric");
  });
});

describe("listScores", () => {
  it("test_returns_listings_on_ok", async () => {
    const listings = [{ listing_id: 1, url: "u", total: 80, verdict: "pursue" }];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => listings }));
    expect(await listScores("anon-9")).toEqual(listings);
  });

  it("test_returns_empty_on_error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, json: async () => ({}) }));
    expect(await listScores("anon-9")).toEqual([]);
  });
});

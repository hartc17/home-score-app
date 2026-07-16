import { afterEach, describe, expect, it, vi } from "vitest";
import type { Rubric } from "@houseflavor/contracts";
import {
  AuthError,
  fetchMe,
  listScores,
  requestMagicLink,
  runScore,
  saveRubricToServer,
  ScoreError,
  verifyMagicLink,
} from "./client.ts";

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

describe("requestMagicLink", () => {
  it("test_posts_email_and_anon_id", async () => {
    const body = { sent: true, dev_link: "http://x/?token=abc" };
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => body });
    vi.stubGlobal("fetch", fetchMock);

    const result = await requestMagicLink("a@b.com", "anon-9");

    expect(result).toEqual(body);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/auth/request");
    expect(JSON.parse(init.body)).toEqual({ email: "a@b.com", anon_id: "anon-9" });
  });

  it("test_throws_auth_error_on_invalid_email", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 422 }));
    await expect(requestMagicLink("bad", "anon-9")).rejects.toThrow(AuthError);
  });
});

describe("verifyMagicLink", () => {
  it("test_posts_token_and_returns_session", async () => {
    const body = { email: "a@b.com", anon_id: "anon-9", session: "s.tok", rubric: null, rubric_version: 1 };
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => body });
    vi.stubGlobal("fetch", fetchMock);

    const result = await verifyMagicLink("tok-123");

    expect(result).toEqual(body);
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ token: "tok-123" });
  });

  it("test_throws_auth_error_on_bad_token", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 400 }));
    await expect(verifyMagicLink("nope")).rejects.toThrow(AuthError);
  });
});

describe("fetchMe", () => {
  it("test_sends_bearer_and_returns_profile", async () => {
    const body = { email: "a@b.com", anon_id: "anon-9", rubric: null };
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => body });
    vi.stubGlobal("fetch", fetchMock);

    expect(await fetchMe("s.tok")).toEqual(body);
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer s.tok");
  });

  it("test_returns_null_when_unauthorized", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false }));
    expect(await fetchMe("s.tok")).toBeNull();
  });
});

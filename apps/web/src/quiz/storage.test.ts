import { describe, expect, it } from "vitest";
import { clearRubric, loadRubric, saveRubric, type KeyValueStore } from "./storage.ts";
import { inferRubric } from "./inference.ts";
import { QUESTIONS } from "./questions.ts";

function memoryStore(): KeyValueStore {
  const map = new Map<string, string>();
  return {
    getItem: (k) => map.get(k) ?? null,
    setItem: (k, v) => void map.set(k, v),
    removeItem: (k) => void map.delete(k),
  };
}

const sampleRubric = inferRubric(QUESTIONS.map((q) => q.options[0]));

describe("rubric storage", () => {
  it("test_save_then_load_roundtrips_rubric", () => {
    const store = memoryStore();
    saveRubric(sampleRubric, ["q1a", "q2a"], "2026-07-15T00:00:00Z", store);
    const loaded = loadRubric(store);
    expect(loaded?.rubric).toEqual(sampleRubric);
    expect(loaded?.optionIds).toEqual(["q1a", "q2a"]);
    expect(loaded?.savedAt).toBe("2026-07-15T00:00:00Z");
  });

  it("test_load_missing_returns_null", () => {
    expect(loadRubric(memoryStore())).toBeNull();
  });

  it("test_save_preserves_anon_id_across_updates", () => {
    const store = memoryStore();
    const first = saveRubric(sampleRubric, ["q1a"], "2026-07-15T00:00:00Z", store);
    const second = saveRubric(sampleRubric, ["q1b"], "2026-07-16T00:00:00Z", store);
    expect(second?.anonId).toBe(first?.anonId);
  });

  it("test_clear_removes_stored_rubric", () => {
    const store = memoryStore();
    saveRubric(sampleRubric, ["q1a"], "2026-07-15T00:00:00Z", store);
    clearRubric(store);
    expect(loadRubric(store)).toBeNull();
  });
});

import type { Rubric } from "@houseflavor/contracts";

const KEY = "houseflavor.rubric.v1";

export interface StoredRubric {
  anonId: string;
  rubric: Rubric;
  optionIds: string[];
  savedAt: string;
}

export interface KeyValueStore {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

function defaultStore(): KeyValueStore | null {
  return typeof localStorage !== "undefined" ? localStorage : null;
}

function newAnonId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return `anon-${Date.now()}`;
}

export function saveRubric(
  rubric: Rubric,
  optionIds: string[],
  savedAt: string,
  store: KeyValueStore | null = defaultStore(),
): StoredRubric | null {
  if (store === null) return null;
  const existing = loadRubric(store);
  const record: StoredRubric = {
    anonId: existing?.anonId ?? newAnonId(),
    rubric,
    optionIds,
    savedAt,
  };
  store.setItem(KEY, JSON.stringify(record));
  return record;
}

export function loadRubric(store: KeyValueStore | null = defaultStore()): StoredRubric | null {
  if (store === null) return null;
  const raw = store.getItem(KEY);
  if (raw === null) return null;
  try {
    return JSON.parse(raw) as StoredRubric;
  } catch {
    // A corrupted or legacy value must not crash the app on startup; drop it.
    store.removeItem(KEY);
    return null;
  }
}

export function clearRubric(store: KeyValueStore | null = defaultStore()): void {
  store?.removeItem(KEY);
}

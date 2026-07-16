import type { Rubric, ScoredListing, ScoreRunResponse } from "@houseflavor/contracts";

// Best-effort server persistence. A missing or failing backend must never block
// the quiz experience, so callers treat a null result as "kept locally only".
export async function saveRubricToServer(anonId: string, rubric: Rubric): Promise<number | null> {
  try {
    const response = await fetch("/rubrics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ anon_id: anonId, rubric }),
    });
    if (!response.ok) return null;
    const body = await response.json();
    return typeof body.version === "number" ? body.version : null;
  } catch {
    return null;
  }
}

export class ScoreError extends Error {}

export async function runScore(anonId: string, url: string): Promise<ScoreRunResponse> {
  const response = await fetch("/scores/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ anon_id: anonId, url }),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new ScoreError(detail?.detail ?? `Scoring failed (${response.status})`);
  }
  return response.json();
}

export async function listScores(anonId: string): Promise<ScoredListing[]> {
  const response = await fetch(`/scores/${encodeURIComponent(anonId)}`);
  if (!response.ok) return [];
  return response.json();
}

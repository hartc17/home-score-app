import type { Rubric } from "@houseflavor/contracts";

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

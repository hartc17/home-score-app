import type {
  MagicLinkResponse,
  MeResponse,
  Rubric,
  ScoredListing,
  ScoreRunResponse,
  SessionResponse,
} from "@houseflavor/contracts";

// `response.json()` is typed `any`; every call site knows the shape it expects,
// so read it through one narrow-cast helper rather than casting at each call.
async function readJson<T>(response: Response): Promise<T> {
  return (await response.json()) as T;
}

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
    const body = await readJson<{ version?: unknown }>(response);
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
    const detail = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new ScoreError(detail?.detail ?? `Scoring failed (${response.status})`);
  }
  return readJson<ScoreRunResponse>(response);
}

export async function listScores(anonId: string): Promise<ScoredListing[]> {
  const response = await fetch(`/scores/${encodeURIComponent(anonId)}`);
  if (!response.ok) return [];
  return readJson<ScoredListing[]>(response);
}

export class AuthError extends Error {}

export async function requestMagicLink(email: string, anonId: string | null): Promise<MagicLinkResponse> {
  const response = await fetch("/auth/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, anon_id: anonId }),
  });
  if (!response.ok) {
    throw new AuthError(response.status === 422 ? "Enter a valid email address" : "Could not send the link");
  }
  return readJson<MagicLinkResponse>(response);
}

export async function verifyMagicLink(token: string): Promise<SessionResponse> {
  const response = await fetch("/auth/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  if (!response.ok) throw new AuthError("This sign-in link is invalid or has expired");
  return readJson<SessionResponse>(response);
}

export async function fetchMe(session: string): Promise<MeResponse | null> {
  const response = await fetch("/auth/me", { headers: { Authorization: `Bearer ${session}` } });
  if (!response.ok) return null;
  return readJson<MeResponse>(response);
}

// Best effort: revokes every outstanding token server-side, but local sign-out
// proceeds even when the server is unreachable.
export async function signOutServer(session: string): Promise<void> {
  try {
    await fetch("/auth/signout", { method: "POST", headers: { Authorization: `Bearer ${session}` } });
  } catch {
    // Local sign-out is the source of truth for this client.
  }
}

import type { Rubric } from "./rubric.ts";

export interface MagicLinkResponse {
  sent: boolean;
  // Present only from the console (non-production) sender for local dev; never
  // populated when a real mail provider is configured.
  dev_link: string | null;
}

export interface SessionResponse {
  email: string;
  anon_id: string;
  session: string;
  rubric: Rubric | null;
  rubric_version: number | null;
}

export interface MeResponse {
  email: string;
  anon_id: string;
  rubric: Rubric | null;
}

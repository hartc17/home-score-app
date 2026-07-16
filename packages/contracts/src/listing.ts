export interface ListingFacts {
  url: string;
  price?: number;
  beds?: number;
  baths?: number;
  sqft?: number;
  year_built?: number;
  garage?: number;
  lot_sqft?: number;
  taxes_annual?: number;
  address?: string;
  home_type?: string;
  photo_urls: string[];
}

export interface ScoreResult {
  gate: "pass" | "disqualified";
  disqualified_reason?: string;
  category_scores: Record<string, number>;
  total: number;
  verdict: "pursue" | "showing" | "conditional" | "weak";
  flags: string[];
  dd_items: string[];
  observation_trace: Record<string, string>;
}

export interface ScoreRunResponse {
  listing_id: number;
  score: ScoreResult;
}

export interface ScoredListing {
  listing_id: number;
  url: string;
  address?: string;
  price?: number;
  total: number;
  verdict: "pursue" | "showing" | "conditional" | "weak";
  category_scores: Record<string, number>;
  rubric_version: number;
  created_at: string;
}

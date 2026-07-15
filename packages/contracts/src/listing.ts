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

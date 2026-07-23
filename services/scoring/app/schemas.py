from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator


class RubricGates(BaseModel):
    budget_max: float
    districts: list[str]
    min_beds: float
    min_baths: float
    min_garage: float
    exclude_main_road: bool
    home_types: list[str]
    timeline: str | None = None


class CategoryWeights(BaseModel):
    bones: float
    warmth: float
    finish: float
    outdoor: float
    value: float
    age: float


class RubricDirections(BaseModel):
    tone: str | None = None
    era: str | None = None
    walls: str | None = None
    ornament: str | None = None
    naturalness: str | None = None


class RubricArchetype(BaseModel):
    name: str
    blend: dict[str, float]


class Rubric(BaseModel):
    version: str
    gates: RubricGates | None = None
    category_weights: CategoryWeights
    item_weights: dict[str, float]
    directions: RubricDirections
    archetype: RubricArchetype
    confidence: dict[str, float]


class ListingFacts(BaseModel):
    url: str
    price: float | None = None
    beds: float | None = None
    baths: float | None = None
    sqft: float | None = None
    year_built: int | None = None
    garage: float | None = None
    lot_sqft: float | None = None
    taxes_annual: float | None = None
    address: str | None = None
    home_type: str | None = None
    photo_urls: list[str]


class StyleClassification(BaseModel):
    style: str
    confidence: float


class ObservationItem(BaseModel):
    value: float | str | list[StyleClassification] | None
    confidence: float
    not_observed: bool | None = None
    flag: str | None = None


class PhotoObservations(BaseModel):
    room_type: str
    observations: dict[str, ObservationItem]


class ListingObservations(BaseModel):
    photos: list[PhotoObservations]
    overall_tone_warmth: ObservationItem | None = None
    overall_style: ObservationItem | None = None
    condition_summary: ObservationItem | None = None
    flags: list[str]
    model: str
    schema_version: str


class ScoreResult(BaseModel):
    gate: str
    disqualified_reason: str | None = None
    category_scores: dict[str, float]
    total: float
    verdict: str
    flags: list[str]
    dd_items: list[str]
    observation_trace: dict[str, str]


class ParseRequest(BaseModel):
    url: str


class AnalyzeRequest(BaseModel):
    listing: ListingFacts


class ScoreRequest(BaseModel):
    rubric: Rubric
    observations: ListingObservations
    facts: ListingFacts


class SaveRubricRequest(BaseModel):
    anon_id: str
    rubric: Rubric


class StoredRubricResponse(BaseModel):
    version: int
    rubric: Rubric


class RubricVersionInfo(BaseModel):
    version: int
    created_at: datetime


class ScoreRunRequest(BaseModel):
    anon_id: str
    url: str


class ScoreRunResponse(BaseModel):
    listing_id: int
    score: ScoreResult


class MagicLinkRequest(BaseModel):
    email: str
    anon_id: str | None = None

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("invalid email")
        return email


class MagicLinkResponse(BaseModel):
    sent: bool
    # Populated only by the console (non-production) sender so local dev and the
    # E2E can complete the loop without a mail provider. Never set in production.
    dev_link: str | None = None


class VerifyRequest(BaseModel):
    token: str


class SessionResponse(BaseModel):
    email: str
    anon_id: str
    session: str
    rubric: Rubric | None = None
    rubric_version: int | None = None


class MeResponse(BaseModel):
    email: str
    anon_id: str
    rubric: Rubric | None = None


class SignOutResponse(BaseModel):
    signed_out: bool


class ScoredListing(BaseModel):
    listing_id: int
    url: str
    address: str | None = None
    price: float | None = None
    total: float
    verdict: str
    category_scores: dict[str, float]
    rubric_version: int
    created_at: datetime

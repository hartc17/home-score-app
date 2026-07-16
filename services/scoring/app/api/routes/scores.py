from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.listings.fetch import fetch_html_sync
from app.listings.parser import parse_listing_html
from app.photos.analyzer import analyze_photoset
from app.rubrics.store import get_latest_rubric_row, rubric_from_row
from app.schemas import (
    ListingFacts,
    ListingObservations,
    ScoredListing,
    ScoreRunRequest,
    ScoreRunResponse,
)
from app.scores.store import get_listing_by_url, record_score_run, scored_listings
from app.scoring.engine import score as score_rubric

router = APIRouter()


# Sync so FastAPI runs the blocking fetch, vision, and database calls in a threadpool.
@router.post("/run", response_model=ScoreRunResponse)
def run_score(request: ScoreRunRequest, db: Session = Depends(get_db)) -> ScoreRunResponse:
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=422, detail="url must be an http(s) listing URL")
    rubric_row = get_latest_rubric_row(db, request.anon_id)
    if rubric_row is None:
        raise HTTPException(status_code=404, detail="no rubric for this id; complete the quiz first")
    rubric = rubric_from_row(rubric_row)

    listing = get_listing_by_url(db, request.url)
    if listing is not None:
        facts = ListingFacts(**listing.facts_json)
        observations = (
            ListingObservations(**listing.analysis.observations_json)
            if listing.analysis is not None
            else analyze_photoset(facts)
        )
    else:
        try:
            html = fetch_html_sync(request.url)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"could not fetch listing: {exc}") from exc
        facts = parse_listing_html(request.url, html)
        observations = analyze_photoset(facts)

    result = score_rubric(rubric, observations, facts)
    score_row = record_score_run(db, facts, observations, result, rubric_row)
    return ScoreRunResponse(listing_id=score_row.listing_id, score=result)


@router.get("/{anon_id}", response_model=list[ScoredListing])
def list_scores(anon_id: str, db: Session = Depends(get_db)) -> list[ScoredListing]:
    return [
        ScoredListing(
            listing_id=s.listing_id,
            url=s.listing.url,
            address=s.listing.address,
            price=s.listing.price,
            total=s.total,
            verdict=s.verdict,
            category_scores=s.category_scores_json,
            rubric_version=s.rubric_version,
            created_at=s.created_at,
        )
        for s in scored_listings(db, anon_id)
    ]

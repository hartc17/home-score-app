from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DdItem, Listing, PhotoAnalysis, RubricRow, Score, User
from app.photos.analyzer import photoset_hash
from app.schemas import ListingFacts, ListingObservations, ScoreResult


def get_listing_by_url(db: Session, url: str) -> Listing | None:
    return db.scalar(select(Listing).where(Listing.url == url))


def record_score_run(
    db: Session,
    facts: ListingFacts,
    observations: ListingObservations,
    result: ScoreResult,
    rubric_row: RubricRow,
) -> Score:
    listing = get_listing_by_url(db, facts.url)
    if listing is None:
        listing = Listing(url=facts.url, address=facts.address, price=facts.price, facts_json=facts.model_dump())
        db.add(listing)
        db.flush()
    if listing.analysis is None:
        db.add(
            PhotoAnalysis(
                listing_id=listing.id,
                model=observations.model,
                schema_version=observations.schema_version,
                photoset_hash=photoset_hash(facts.photo_urls),
                observations_json=observations.model_dump(),
            )
        )
        db.flush()
    score = Score(
        listing_id=listing.id,
        rubric_id=rubric_row.id,
        rubric_version=rubric_row.version,
        total=result.total,
        verdict=result.verdict,
        category_scores_json=result.category_scores,
    )
    score.dd_items = [DdItem(text=text) for text in result.dd_items]
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def scored_listings(db: Session, anon_id: str) -> list[Score]:
    # Newest score per listing for the user, ranked best first.
    rows = db.scalars(
        select(Score)
        .join(RubricRow, Score.rubric_id == RubricRow.id)
        .join(User, RubricRow.user_id == User.id)
        .where(User.anon_id == anon_id)
        .order_by(Score.created_at.desc())
    ).all()
    latest: dict[int, Score] = {}
    for score in rows:
        latest.setdefault(score.listing_id, score)
    return sorted(latest.values(), key=lambda s: s.total, reverse=True)

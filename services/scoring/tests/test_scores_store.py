from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import PhotoAnalysis, Score
from app.rubrics.store import get_latest_rubric_row, save_rubric
from app.schemas import ListingFacts, ObservationItem, RubricDirections
from app.scores.store import record_score_run, scored_listings
from app.scoring.engine import score
from tests.builders import make_rubric, single_photo


def _rubric_row(db: Session, anon: str = "u1"):
    rubric = make_rubric(item_weights={"tone_warmth": 10.0}, directions=RubricDirections(tone="warm"))
    save_rubric(db, anon, rubric)
    return rubric, get_latest_rubric_row(db, anon)


def _facts(url: str) -> ListingFacts:
    return ListingFacts(url=url, photo_urls=["p.jpg"], address="1 Main St", price=400000)


def _tone_obs(value: float):
    return single_photo({"tone_warmth": ObservationItem(value=value, confidence=1.0)})


def test_record_score_run_persists_listing_analysis_and_score(db: Session):
    rubric, row = _rubric_row(db)
    facts = _facts("https://example.com/a")
    obs = _tone_obs(9.0)
    result = score(rubric, obs, facts)

    persisted = record_score_run(db, facts, obs, result, row)

    assert persisted.total == result.total
    assert persisted.verdict == result.verdict
    assert persisted.rubric_version == row.version
    assert db.scalar(select(func.count()).select_from(PhotoAnalysis)) == 1


def test_record_score_run_creates_dd_items(db: Session):
    rubric, row = _rubric_row(db)
    facts = _facts("https://example.com/a")
    # Low confidence forces a verify due-diligence item.
    obs = single_photo({"tone_warmth": ObservationItem(value=9.0, confidence=0.3)})
    result = score(rubric, obs, facts)

    persisted = record_score_run(db, facts, obs, result, row)
    assert len(persisted.dd_items) == len(result.dd_items)
    assert len(result.dd_items) > 0


def test_scored_listings_ranked_best_first(db: Session):
    rubric, row = _rubric_row(db)
    for url, value in [("https://example.com/low", 1.0), ("https://example.com/high", 9.0)]:
        facts = _facts(url)
        obs = _tone_obs(value)
        record_score_run(db, facts, obs, score(rubric, obs, facts), row)

    ranked = scored_listings(db, "u1")
    assert [s.listing.url for s in ranked] == ["https://example.com/high", "https://example.com/low"]


def test_rescoring_same_listing_reuses_analysis_and_returns_latest(db: Session):
    rubric, row = _rubric_row(db)
    facts = _facts("https://example.com/a")
    record_score_run(db, facts, _tone_obs(9.0), score(rubric, _tone_obs(9.0), facts), row)
    record_score_run(db, facts, _tone_obs(1.0), score(rubric, _tone_obs(1.0), facts), row)

    assert db.scalar(select(func.count()).select_from(PhotoAnalysis)) == 1
    assert db.scalar(select(func.count()).select_from(Score)) == 2
    assert len(scored_listings(db, "u1")) == 1


def test_scored_listings_empty_for_unknown_user(db: Session):
    assert scored_listings(db, "nobody") == []

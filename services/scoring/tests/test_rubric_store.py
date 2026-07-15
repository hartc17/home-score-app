import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.rubrics.store import (
    get_latest_rubric,
    get_rubric_by_version,
    get_rubric_versions,
    save_rubric,
)
from app.schemas import CategoryWeights, Rubric, RubricArchetype, RubricDirections


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session


def _rubric(warmth: int = 20) -> Rubric:
    return Rubric(
        version="1.0",
        category_weights=CategoryWeights(bones=20, warmth=warmth, finish=20, outdoor=20, value=10, age=10),
        item_weights={"tone_warmth": 10.0},
        directions=RubricDirections(tone="warm"),
        archetype=RubricArchetype(name="x", blend={"x": 1.0}),
        confidence={},
    )


def test_save_rubric_first_version_is_1(db: Session):
    version, _ = save_rubric(db, "anon-1", _rubric())
    assert version == 1


def test_save_rubric_increments_version(db: Session):
    save_rubric(db, "anon-1", _rubric())
    version, _ = save_rubric(db, "anon-1", _rubric())
    assert version == 2


def test_get_latest_returns_highest_version(db: Session):
    save_rubric(db, "anon-1", _rubric(warmth=20))
    save_rubric(db, "anon-1", _rubric(warmth=40))
    version, rubric = get_latest_rubric(db, "anon-1")
    assert version == 2
    assert rubric.category_weights.warmth == 40


def test_old_version_remains_readable_after_new_save(db: Session):
    save_rubric(db, "anon-1", _rubric(warmth=20))
    save_rubric(db, "anon-1", _rubric(warmth=40))
    v1 = get_rubric_by_version(db, "anon-1", 1)
    assert v1.category_weights.warmth == 20


def test_get_versions_lists_all_in_order(db: Session):
    save_rubric(db, "anon-1", _rubric())
    save_rubric(db, "anon-1", _rubric())
    versions = get_rubric_versions(db, "anon-1")
    assert [v for v, _ in versions] == [1, 2]


def test_separate_anon_ids_have_independent_versions(db: Session):
    save_rubric(db, "anon-1", _rubric())
    version, _ = save_rubric(db, "anon-2", _rubric())
    assert version == 1


def test_get_latest_missing_returns_none(db: Session):
    assert get_latest_rubric(db, "nobody") is None

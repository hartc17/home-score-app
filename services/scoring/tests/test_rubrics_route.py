import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import get_db
from app.db.models import Base
from app.main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def _rubric_payload(warmth: int = 20) -> dict:
    return {
        "version": "1.0",
        "category_weights": {"bones": 20, "warmth": warmth, "finish": 20, "outdoor": 20, "value": 10, "age": 10},
        "item_weights": {"tone_warmth": 10.0},
        "directions": {"tone": "warm"},
        "archetype": {"name": "x", "blend": {"x": 1.0}},
        "confidence": {},
    }


def test_post_rubric_returns_version_1_and_echoes_rubric(client: TestClient):
    response = client.post("/rubrics", json={"anon_id": "anon-1", "rubric": _rubric_payload()})
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 1
    assert body["rubric"]["directions"]["tone"] == "warm"


def test_get_latest_returns_most_recent_version(client: TestClient):
    client.post("/rubrics", json={"anon_id": "anon-1", "rubric": _rubric_payload(20)})
    client.post("/rubrics", json={"anon_id": "anon-1", "rubric": _rubric_payload(40)})
    response = client.get("/rubrics/anon-1")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 2
    assert body["rubric"]["category_weights"]["warmth"] == 40


def test_get_missing_rubric_returns_404(client: TestClient):
    assert client.get("/rubrics/nobody").status_code == 404


def test_versions_endpoint_lists_all(client: TestClient):
    client.post("/rubrics", json={"anon_id": "anon-1", "rubric": _rubric_payload()})
    client.post("/rubrics", json={"anon_id": "anon-1", "rubric": _rubric_payload()})
    response = client.get("/rubrics/anon-1/versions")
    assert response.status_code == 200
    assert [v["version"] for v in response.json()] == [1, 2]

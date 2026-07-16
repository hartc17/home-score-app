from fastapi.testclient import TestClient

from app.api.routes import scores
from app.schemas import ObservationItem
from tests.builders import single_photo


def _rubric_payload() -> dict:
    return {
        "version": "1.0",
        "category_weights": {"bones": 20, "warmth": 40, "finish": 20, "outdoor": 10, "value": 5, "age": 5},
        "item_weights": {"tone_warmth": 20.0},
        "directions": {"tone": "warm"},
        "archetype": {"name": "x", "blend": {"x": 1.0}},
        "confidence": {},
    }


def _mock_pipeline(monkeypatch, tone: float = 9.0):
    monkeypatch.setattr(scores, "fetch_html_sync", lambda url: "<html><body>3 beds 2 baths</body></html>")
    monkeypatch.setattr(
        scores,
        "analyze_photoset",
        lambda facts: single_photo({"tone_warmth": ObservationItem(value=tone, confidence=1.0)}),
    )


def test_run_score_persists_and_returns_result(client: TestClient, monkeypatch):
    client.post("/rubrics", json={"anon_id": "u1", "rubric": _rubric_payload()})
    _mock_pipeline(monkeypatch)

    response = client.post("/scores/run", json={"anon_id": "u1", "url": "https://example.com/a"})

    assert response.status_code == 200
    body = response.json()
    assert body["score"]["gate"] == "pass"
    assert body["score"]["total"] > 0


def test_run_score_without_rubric_returns_404(client: TestClient, monkeypatch):
    _mock_pipeline(monkeypatch)
    response = client.post("/scores/run", json={"anon_id": "ghost", "url": "https://example.com/a"})
    assert response.status_code == 404


def test_run_score_rejects_non_http_url(client: TestClient):
    response = client.post("/scores/run", json={"anon_id": "u1", "url": "ftp://example.com/a"})
    assert response.status_code == 422


def test_run_score_blocks_internal_address_ssrf(client: TestClient):
    # Real fetch path (not mocked): the guard must refuse a link-local address
    # like the cloud metadata endpoint before any connection is made.
    client.post("/rubrics", json={"anon_id": "u1", "rubric": _rubric_payload()})
    response = client.post("/scores/run", json={"anon_id": "u1", "url": "http://169.254.169.254/latest/meta-data/"})
    assert response.status_code == 422


def test_list_scores_returns_ranked_comparison(client: TestClient, monkeypatch):
    client.post("/rubrics", json={"anon_id": "u1", "rubric": _rubric_payload()})
    _mock_pipeline(monkeypatch, tone=9.0)
    client.post("/scores/run", json={"anon_id": "u1", "url": "https://example.com/high"})
    _mock_pipeline(monkeypatch, tone=1.0)
    client.post("/scores/run", json={"anon_id": "u1", "url": "https://example.com/low"})

    response = client.get("/scores/u1")
    assert response.status_code == 200
    listings = response.json()
    assert [x["url"] for x in listings] == ["https://example.com/high", "https://example.com/low"]
    assert listings[0]["total"] >= listings[1]["total"]

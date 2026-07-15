from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.routes import listings
from app.main import app

_FIXTURE = (Path(__file__).parent / "fixtures" / "sample_listing.html").read_text()

client = TestClient(app)


def test_parse_route_returns_facts_from_fetched_html(monkeypatch):
    async def fake_fetch(url: str) -> str:
        return _FIXTURE

    monkeypatch.setattr(listings, "fetch_html", fake_fetch)
    response = client.post("/listings/parse", json={"url": "https://listings.example.com/42-maple"})

    assert response.status_code == 200
    body = response.json()
    assert body["beds"] == 4
    assert body["price"] == 575000
    assert len(body["photo_urls"]) >= 3


def test_parse_route_rejects_non_http_url():
    response = client.post("/listings/parse", json={"url": "ftp://example.com/x"})
    assert response.status_code == 422


def test_parse_route_maps_fetch_failure_to_502(monkeypatch):
    async def failing_fetch(url: str) -> str:
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(listings, "fetch_html", failing_fetch)
    response = client.post("/listings/parse", json={"url": "https://listings.example.com/broken"})

    assert response.status_code == 502

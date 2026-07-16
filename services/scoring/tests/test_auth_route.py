from urllib.parse import parse_qs, urlparse

from tests.builders import make_rubric


def _save_rubric(client, anon_id):
    client.post("/rubrics", json={"anon_id": anon_id, "rubric": make_rubric().model_dump()})


def _token_from_dev_link(link: str) -> str:
    return parse_qs(urlparse(link).query)["token"][0]


def test_request_returns_dev_link_without_a_mail_provider(client):
    resp = client.post("/auth/request", json={"email": "Buyer@Example.com", "anon_id": "anon-1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["sent"] is True
    assert body["dev_link"] and "token=" in body["dev_link"]


def test_request_rejects_invalid_email(client):
    assert client.post("/auth/request", json={"email": "not-an-email"}).status_code == 422


def test_full_magic_link_flow_claims_and_signs_in(client):
    _save_rubric(client, "anon-1")
    link = client.post("/auth/request", json={"email": "buyer@example.com", "anon_id": "anon-1"}).json()["dev_link"]

    verify = client.post("/auth/verify", json={"token": _token_from_dev_link(link)})
    assert verify.status_code == 200
    session = verify.json()
    assert session["email"] == "buyer@example.com"
    assert session["anon_id"] == "anon-1"
    assert session["rubric"] is not None

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {session['session']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "buyer@example.com"


def test_request_is_rate_limited_per_email(client):
    for _ in range(5):
        assert client.post("/auth/request", json={"email": "buyer@example.com"}).status_code == 200
    assert client.post("/auth/request", json={"email": "buyer@example.com"}).status_code == 429


def test_verify_rejects_unknown_token(client):
    assert client.post("/auth/verify", json={"token": "nope"}).status_code == 400


def test_verify_is_single_use(client):
    link = client.post("/auth/request", json={"email": "buyer@example.com", "anon_id": "a"}).json()["dev_link"]
    token = _token_from_dev_link(link)
    assert client.post("/auth/verify", json={"token": token}).status_code == 200
    assert client.post("/auth/verify", json={"token": token}).status_code == 400


def test_me_requires_a_valid_session(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401

from app.auth.tokens import (
    SESSION_MAX_AGE_SECONDS,
    hash_login_token,
    issue_session,
    new_login_token,
    read_session,
)


def test_new_login_token_hash_matches_hash_function():
    raw, token_hash = new_login_token()
    assert hash_login_token(raw) == token_hash
    assert raw != token_hash


def test_session_round_trips_user_id():
    token = issue_session(42, issued_at=1000.0)
    assert read_session(token, now=1000.0) == (42, 0)


def test_session_round_trips_epoch():
    token = issue_session(42, issued_at=1000.0, epoch=3)
    assert read_session(token, now=1000.0) == (42, 3)


def test_session_rejects_tampered_payload():
    token = issue_session(42, issued_at=1000.0)
    payload, signature = token.split(".")
    forged = issue_session(999, issued_at=1000.0).split(".")[0]
    assert read_session(f"{forged}.{signature}", now=1000.0) is None


def test_session_expires_after_max_age():
    token = issue_session(7, issued_at=1000.0)
    assert read_session(token, now=1000.0 + SESSION_MAX_AGE_SECONDS + 1) is None


def test_session_rejects_malformed_token():
    assert read_session("garbage", now=1000.0) is None
    assert read_session("a.b.c", now=1000.0) is None

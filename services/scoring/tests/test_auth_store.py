from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.auth.store import claim_account, consume_login_token, create_login_token
from app.db.models import User
from app.rubrics.store import latest_rubric_for_user, save_rubric
from tests.builders import make_gates, make_rubric

NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)


def _consume(db, raw, now=NOW):
    return consume_login_token(db, raw, now)


def test_create_and_consume_token_round_trip(db):
    raw = create_login_token(db, "buyer@example.com", "anon-1", NOW)
    token = _consume(db, raw)
    assert token is not None
    assert token.email == "buyer@example.com"
    assert token.claim_anon_id == "anon-1"


def test_consumed_token_cannot_be_reused(db):
    raw = create_login_token(db, "buyer@example.com", "anon-1", NOW)
    assert _consume(db, raw) is not None
    assert _consume(db, raw) is None


def test_expired_token_is_rejected(db):
    raw = create_login_token(db, "buyer@example.com", None, NOW)
    assert consume_login_token(db, raw, NOW + timedelta(hours=1)) is None


def test_requesting_new_token_retires_prior_one(db):
    first = create_login_token(db, "buyer@example.com", "anon-1", NOW)
    create_login_token(db, "buyer@example.com", "anon-1", NOW)
    assert _consume(db, first) is None


def test_claim_in_place_sets_email_on_anonymous_row(db):
    save_rubric(db, "anon-1", make_rubric())
    user = claim_account(db, "buyer@example.com", "anon-1")
    assert user.email == "buyer@example.com"
    assert user.anon_id == "anon-1"
    # No second user row was created.
    assert len(db.scalars(select(User)).all()) == 1


def test_claim_without_prior_rubric_creates_account(db):
    user = claim_account(db, "buyer@example.com", "anon-new")
    assert user.email == "buyer@example.com"
    assert latest_rubric_for_user(db, user) is None


def test_second_device_composes_rubric_forward_onto_account(db):
    # Existing account with gates.
    save_rubric(db, "anon-account", make_rubric(gates=make_gates(budget_max=500_000)))
    claim_account(db, "buyer@example.com", "anon-account")
    # New device took the quiz (no gates) and signs in with the same email.
    save_rubric(db, "anon-device2", make_rubric(item_weights={"tone_warmth": 9.0}))
    account = claim_account(db, "buyer@example.com", "anon-device2")

    latest = latest_rubric_for_user(db, account)
    assert latest is not None
    # Fresh quiz taste is preserved and the account's gates carry forward.
    assert latest.item_weights == {"tone_warmth": 9.0}
    assert latest.gates is not None
    assert latest.gates.budget_max == 500_000
    assert account.anon_id == "anon-account"


def test_second_device_leaves_a_new_version_on_the_account(db):
    save_rubric(db, "anon-account", make_rubric())
    claim_account(db, "buyer@example.com", "anon-account")
    save_rubric(db, "anon-device2", make_rubric(item_weights={"fireplace": 5.0}))
    account = claim_account(db, "buyer@example.com", "anon-device2")
    versions = sorted(r.version for r in account.rubrics)
    assert versions == [1, 2]

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth.tokens import hash_login_token, new_login_token
from app.db.models import LoginToken, User
from app.rubrics.merge import compose_forward
from app.rubrics.store import latest_rubric_for_user, save_rubric_for_user

LOGIN_TTL_MINUTES = 15


def create_login_token(db: Session, email: str, anon_id: str | None, now: datetime) -> str:
    # One outstanding link per email: requesting a new one retires any prior
    # unconsumed tokens so an old link cannot be replayed.
    db.execute(
        update(LoginToken)
        .where(LoginToken.email == email, LoginToken.consumed_at.is_(None))
        .values(consumed_at=now)
    )
    raw, token_hash = new_login_token()
    db.add(
        LoginToken(
            token_hash=token_hash,
            email=email,
            claim_anon_id=anon_id,
            expires_at=now + timedelta(minutes=LOGIN_TTL_MINUTES),
        )
    )
    db.commit()
    return raw


def _as_utc(value: datetime) -> datetime:
    # SQLite returns naive datetimes; Postgres returns aware. Normalize so the
    # expiry comparison works on both backends.
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def consume_login_token(db: Session, raw: str, now: datetime) -> LoginToken | None:
    token = db.scalar(select(LoginToken).where(LoginToken.token_hash == hash_login_token(raw)))
    if token is None or token.consumed_at is not None or _as_utc(token.expires_at) < now:
        return None
    token.consumed_at = now
    db.flush()
    return token


def claim_account(db: Session, email: str, anon_id: str | None) -> User:
    account = db.scalar(select(User).where(User.email == email))
    anon_user = db.scalar(select(User).where(User.anon_id == anon_id)) if anon_id else None

    if account is None:
        # No prior account: claim in place by setting email on the anonymous row,
        # so the anonymous rubric is claimed with no migration.
        if anon_user is None:
            anon_user = User(anon_id=anon_id or email, email=email)
            db.add(anon_user)
        else:
            anon_user.email = email
        db.commit()
        return anon_user

    if anon_user is not None and anon_user.id != account.id:
        # Signing in on a device that already took the quiz: compose the device's
        # latest rubric forward onto the existing account as a new version.
        incoming = latest_rubric_for_user(db, anon_user)
        if incoming is not None:
            merged = compose_forward(latest_rubric_for_user(db, account), incoming)
            save_rubric_for_user(db, account, merged)
            db.expire(account, ["rubrics"])
    db.commit()
    return account

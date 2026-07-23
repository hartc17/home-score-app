from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.email import resolve_email_sender
from app.auth.ratelimit import SlidingWindowLimiter
from app.auth.store import RateLimitedError, claim_account, consume_login_token, create_login_token
from app.auth.tokens import issue_session, read_session
from app.db.base import get_db
from app.db.models import RubricRow, User
from app.rubrics.store import latest_rubric_for_user
from app.schemas import (
    MagicLinkRequest,
    MagicLinkResponse,
    MeResponse,
    SessionResponse,
    SignOutResponse,
    VerifyRequest,
)

router = APIRouter()

# Coarser than the per-email limit so a shared NAT is not locked out, but low
# enough to bound scripted link-spraying across many addresses from one host.
IP_LIMIT_MAX = 30
IP_LIMIT_WINDOW_SECONDS = 3600.0
ip_limiter = SlidingWindowLimiter(IP_LIMIT_MAX, IP_LIMIT_WINDOW_SECONDS)


def _app_url() -> str:
    return os.environ.get("HOUSEFLAVOR_APP_URL", "http://localhost:5173").rstrip("/")


def _client_ip(request: Request) -> str:
    # nginx appends the peer address to X-Forwarded-For, so the last entry is
    # what our own proxy observed and cannot be spoofed by the client. Without
    # the header (direct access, tests) fall back to the socket peer.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


@router.post("/request", response_model=MagicLinkResponse)
def request_link(
    request: MagicLinkRequest, http_request: Request, db: Session = Depends(get_db)
) -> MagicLinkResponse:
    now = datetime.now(timezone.utc)
    if not ip_limiter.allow(_client_ip(http_request), now.timestamp()):
        raise HTTPException(status_code=429, detail="too many sign-in requests; try again shortly")
    try:
        raw = create_login_token(db, request.email, request.anon_id, now)
    except RateLimitedError as exc:
        raise HTTPException(status_code=429, detail="too many sign-in requests; try again shortly") from exc
    link = f"{_app_url()}/?token={raw}"
    sender = resolve_email_sender()
    sender.send_magic_link(request.email, link)
    return MagicLinkResponse(sent=True, dev_link=None if sender.production else link)


@router.post("/verify", response_model=SessionResponse)
def verify(request: VerifyRequest, db: Session = Depends(get_db)) -> SessionResponse:
    now = datetime.now(timezone.utc)
    token = consume_login_token(db, request.token, now)
    if token is None:
        raise HTTPException(status_code=400, detail="invalid or expired link")
    user = claim_account(db, token.email, token.claim_anon_id)
    latest_version = db.scalar(select(func.max(RubricRow.version)).where(RubricRow.user_id == user.id))
    return SessionResponse(
        email=user.email,
        anon_id=user.anon_id,
        session=issue_session(user.id, now.timestamp(), user.session_epoch),
        rubric=latest_rubric_for_user(db, user),
        rubric_version=latest_version,
    )


def _session_user(authorization: str | None, db: Session) -> User:
    token = authorization[7:] if authorization and authorization.startswith("Bearer ") else None
    claim = read_session(token, datetime.now(timezone.utc).timestamp()) if token else None
    user = db.scalar(select(User).where(User.id == claim[0])) if claim is not None else None
    # A token issued under an older epoch was revoked by a sign-out.
    if user is None or user.email is None or claim[1] != user.session_epoch:
        raise HTTPException(status_code=401, detail="not signed in")
    return user


@router.get("/me", response_model=MeResponse)
def me(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> MeResponse:
    user = _session_user(authorization, db)
    return MeResponse(email=user.email, anon_id=user.anon_id, rubric=latest_rubric_for_user(db, user))


@router.post("/signout", response_model=SignOutResponse)
def signout(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> SignOutResponse:
    user = _session_user(authorization, db)
    user.session_epoch += 1
    db.commit()
    return SignOutResponse(signed_out=True)

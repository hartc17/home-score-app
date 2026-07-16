from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets

# Two kinds of token. A login token is a random one-time secret emailed as a
# magic link; only its hash is persisted. A session token is a stateless signed
# claim of a user id, verified by HMAC with a server secret.

SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30


def new_login_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hash_login_token(raw)


def hash_login_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _secret() -> bytes:
    return os.environ.get("HOUSEFLAVOR_SESSION_SECRET", "dev-insecure-session-secret").encode()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(payload: str) -> str:
    return _b64(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest())


def issue_session(user_id: int, issued_at: float) -> str:
    payload = _b64(json.dumps({"uid": user_id, "iat": int(issued_at)}).encode())
    return f"{payload}.{_sign(payload)}"


def read_session(token: str, now: float, max_age: int = SESSION_MAX_AGE_SECONDS) -> int | None:
    parts = token.split(".")
    if len(parts) != 2:
        return None
    payload, signature = parts
    if not hmac.compare_digest(signature, _sign(payload)):
        return None
    try:
        data = json.loads(_unb64(payload))
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(data.get("uid"), int) or not isinstance(data.get("iat"), int):
        return None
    if now - data["iat"] > max_age:
        return None
    return data["uid"]

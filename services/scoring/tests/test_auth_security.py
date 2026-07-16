import pytest

from app.api.routes import auth as auth_route
from app.auth.email import ConsoleEmailSender, ResendEmailSender, resolve_email_sender
from app.auth.tokens import issue_session, read_session


def test_session_secret_required_in_production(monkeypatch):
    monkeypatch.setenv("HOUSEFLAVOR_ENV", "production")
    monkeypatch.delenv("HOUSEFLAVOR_SESSION_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        issue_session(1, issued_at=1000.0)


def test_session_secret_rejects_shipped_default_in_production(monkeypatch):
    monkeypatch.setenv("HOUSEFLAVOR_ENV", "production")
    monkeypatch.setenv("HOUSEFLAVOR_SESSION_SECRET", "dev-insecure-session-secret")
    with pytest.raises(RuntimeError):
        issue_session(1, issued_at=1000.0)


def test_session_works_in_production_with_a_real_secret(monkeypatch):
    monkeypatch.setenv("HOUSEFLAVOR_ENV", "production")
    monkeypatch.setenv("HOUSEFLAVOR_SESSION_SECRET", "a-real-deployment-secret")
    token = issue_session(7, issued_at=1000.0)
    assert read_session(token, now=1000.0) == 7


def test_session_uses_default_secret_in_development(monkeypatch):
    monkeypatch.delenv("HOUSEFLAVOR_ENV", raising=False)
    monkeypatch.delenv("HOUSEFLAVOR_SESSION_SECRET", raising=False)
    token = issue_session(7, issued_at=1000.0)
    assert read_session(token, now=1000.0) == 7


def test_email_sender_raises_in_production_without_a_provider(monkeypatch):
    monkeypatch.setenv("HOUSEFLAVOR_ENV", "production")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        resolve_email_sender()


def test_email_sender_is_console_in_development(monkeypatch):
    monkeypatch.delenv("HOUSEFLAVOR_ENV", raising=False)
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    assert isinstance(resolve_email_sender(), ConsoleEmailSender)


def test_email_sender_uses_resend_with_a_key(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    sender = resolve_email_sender()
    assert isinstance(sender, ResendEmailSender)
    assert sender.production is True


class _FakeProductionSender:
    production = True

    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send_magic_link(self, email, link):
        self.sent.append((email, link))


def test_request_does_not_leak_dev_link_with_a_production_sender(client, monkeypatch):
    fake = _FakeProductionSender()
    monkeypatch.setattr(auth_route, "resolve_email_sender", lambda: fake)

    body = client.post("/auth/request", json={"email": "buyer@example.com", "anon_id": "a"}).json()

    assert body["sent"] is True
    assert body["dev_link"] is None
    # The link still went out through the provider, just not back to the caller.
    assert fake.sent and "token=" in fake.sent[0][1]

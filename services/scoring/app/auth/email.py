from __future__ import annotations

import os
from typing import Protocol

import httpx


# The email sender is a pluggable seam, mirroring the vision analyzer: a real
# provider is used when configured, otherwise a console sender that records the
# link so local dev and tests can complete the loop without sending mail.
class EmailSender(Protocol):
    production: bool

    def send_magic_link(self, email: str, link: str) -> None: ...


class ConsoleEmailSender:
    production = False

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send_magic_link(self, email: str, link: str) -> None:
        self.sent.append((email, link))
        print(f"[magic-link] {email} -> {link}")


class ResendEmailSender:
    production = True

    def __init__(self, api_key: str, sender: str) -> None:
        self._api_key = api_key
        self._sender = sender

    def send_magic_link(self, email: str, link: str) -> None:
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "from": self._sender,
                "to": [email],
                "subject": "Your HouseFlavor sign-in link",
                "text": f"Tap to sign in and save your taste profile:\n\n{link}\n\nThis link expires shortly.",
            },
            timeout=15.0,
        ).raise_for_status()


console_sender = ConsoleEmailSender()


def resolve_email_sender() -> EmailSender:
    api_key = os.environ.get("RESEND_API_KEY")
    if api_key:
        sender = os.environ.get("HOUSEFLAVOR_EMAIL_FROM", "HouseFlavor <login@houseflavor.app>")
        return ResendEmailSender(api_key, sender)
    return console_sender

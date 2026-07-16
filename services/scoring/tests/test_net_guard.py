import httpx
import pytest

from app.net import guard
from app.net.guard import UnsafeURLError, assert_public_url, safe_get


def test_assert_public_url_rejects_non_http_scheme():
    with pytest.raises(UnsafeURLError):
        assert_public_url("ftp://example.com/x")


def test_assert_public_url_rejects_loopback(monkeypatch):
    monkeypatch.setattr(guard.socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("127.0.0.1", 80))])
    with pytest.raises(UnsafeURLError):
        assert_public_url("http://localhost/")


def test_assert_public_url_rejects_cloud_metadata_ip(monkeypatch):
    monkeypatch.setattr(guard.socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("169.254.169.254", 80))])
    with pytest.raises(UnsafeURLError):
        assert_public_url("http://169.254.169.254/latest/meta-data/")


def test_assert_public_url_rejects_private_range(monkeypatch):
    monkeypatch.setattr(guard.socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("10.0.0.5", 80))])
    with pytest.raises(UnsafeURLError):
        assert_public_url("http://internal.svc/")


def test_assert_public_url_rejects_ipv4_mapped_ipv6(monkeypatch):
    monkeypatch.setattr(guard.socket, "getaddrinfo", lambda *a, **k: [(10, 1, 6, "", ("::ffff:127.0.0.1", 80, 0, 0))])
    with pytest.raises(UnsafeURLError):
        assert_public_url("http://sneaky/")


def test_assert_public_url_allows_public_ip(monkeypatch):
    monkeypatch.setattr(guard.socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 80))])
    assert_public_url("http://example.com/listing")


class _Transport(httpx.BaseTransport):
    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = responses
        self.requested: list[str] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requested.append(str(request.url))
        return self._responses.pop(0)


def test_safe_get_validates_each_redirect_hop(monkeypatch):
    # First host resolves public; the redirect target resolves to loopback and
    # must be blocked before the second request is issued.
    resolved = {"good.com": "93.184.216.34", "evil.com": "127.0.0.1"}
    monkeypatch.setattr(
        guard.socket,
        "getaddrinfo",
        lambda host, *a, **k: [(2, 1, 6, "", (resolved[host], 80))],
    )
    redirect = httpx.Response(302, headers={"location": "http://evil.com/"}, request=httpx.Request("GET", "http://good.com/"))
    transport = _Transport([redirect])
    real_client = httpx.Client
    monkeypatch.setattr(guard.httpx, "Client", lambda **kw: real_client(transport=transport))

    with pytest.raises(UnsafeURLError):
        safe_get("http://good.com/")
    # The blocked hop was never requested.
    assert transport.requested == ["http://good.com/"]

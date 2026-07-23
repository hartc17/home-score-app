import httpx
import pytest

from app.net import guard
from app.net.guard import UnsafeURLError, resolve_public_address, safe_get


def _resolver(mapping):
    return lambda host, *a, **k: [(2, 1, 6, "", (mapping[host], 80))]


def test_resolve_rejects_non_http_scheme():
    with pytest.raises(UnsafeURLError):
        resolve_public_address("ftp://example.com/x")


def test_resolve_rejects_loopback(monkeypatch):
    monkeypatch.setattr(guard.socket, "getaddrinfo", _resolver({"localhost": "127.0.0.1"}))
    with pytest.raises(UnsafeURLError):
        resolve_public_address("http://localhost/")


def test_resolve_rejects_cloud_metadata_ip(monkeypatch):
    monkeypatch.setattr(guard.socket, "getaddrinfo", _resolver({"169.254.169.254": "169.254.169.254"}))
    with pytest.raises(UnsafeURLError):
        resolve_public_address("http://169.254.169.254/latest/meta-data/")


def test_resolve_rejects_private_range(monkeypatch):
    monkeypatch.setattr(guard.socket, "getaddrinfo", _resolver({"internal.svc": "10.0.0.5"}))
    with pytest.raises(UnsafeURLError):
        resolve_public_address("http://internal.svc/")


def test_resolve_rejects_ipv4_mapped_ipv6(monkeypatch):
    monkeypatch.setattr(
        guard.socket, "getaddrinfo", lambda *a, **k: [(10, 1, 6, "", ("::ffff:127.0.0.1", 80, 0, 0))]
    )
    with pytest.raises(UnsafeURLError):
        resolve_public_address("http://sneaky/")


def test_resolve_rejects_when_any_returned_address_is_blocked(monkeypatch):
    # A rebinding-style answer that mixes a public and a private address must be
    # refused outright, not just have the public one picked.
    monkeypatch.setattr(
        guard.socket,
        "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 80)), (2, 1, 6, "", ("127.0.0.1", 80))],
    )
    with pytest.raises(UnsafeURLError):
        resolve_public_address("http://mixed.example/")


def test_resolve_returns_validated_public_address(monkeypatch):
    monkeypatch.setattr(guard.socket, "getaddrinfo", _resolver({"example.com": "93.184.216.34"}))
    assert resolve_public_address("http://example.com/listing") == "93.184.216.34"


def test_dev_flag_allows_private_fetch_outside_production(monkeypatch):
    monkeypatch.delenv("HOUSEFLAVOR_ENV", raising=False)
    monkeypatch.setenv("HOUSEFLAVOR_ALLOW_PRIVATE_FETCH", "1")
    monkeypatch.setattr(guard.socket, "getaddrinfo", _resolver({"localhost": "127.0.0.1"}))
    assert resolve_public_address("http://localhost:8899/") == "127.0.0.1"


def test_dev_flag_is_ignored_in_production(monkeypatch):
    monkeypatch.setenv("HOUSEFLAVOR_ENV", "production")
    monkeypatch.setenv("HOUSEFLAVOR_ALLOW_PRIVATE_FETCH", "1")
    monkeypatch.setattr(guard.socket, "getaddrinfo", _resolver({"localhost": "127.0.0.1"}))
    with pytest.raises(UnsafeURLError):
        resolve_public_address("http://localhost:8899/")


class _Transport(httpx.BaseTransport):
    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = responses
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._responses.pop(0)


def _patched_client(monkeypatch, transport):
    real_client = httpx.Client
    monkeypatch.setattr(guard.httpx, "Client", lambda **kw: real_client(transport=transport))


def test_safe_get_connects_to_the_validated_address(monkeypatch):
    # The connection goes to the IP that was validated, with the hostname kept
    # in the Host header and SNI, so a post-validation DNS flip cannot redirect
    # the connection.
    monkeypatch.setattr(guard.socket, "getaddrinfo", _resolver({"good.com": "93.184.216.34"}))
    transport = _Transport([httpx.Response(200, text="ok")])
    _patched_client(monkeypatch, transport)

    response = safe_get("http://good.com/listing?x=1")

    assert response.status_code == 200
    request = transport.requests[0]
    assert request.url.host == "93.184.216.34"
    assert request.url.path == "/listing"
    assert request.headers["host"] == "good.com"
    assert request.extensions["sni_hostname"] == "good.com"


def test_safe_get_validates_each_redirect_hop(monkeypatch):
    # First host resolves public; the redirect target resolves to loopback and
    # must be blocked before the second request is issued.
    monkeypatch.setattr(
        guard.socket, "getaddrinfo", _resolver({"good.com": "93.184.216.34", "evil.com": "127.0.0.1"})
    )
    transport = _Transport([httpx.Response(302, headers={"location": "http://evil.com/"})])
    _patched_client(monkeypatch, transport)

    with pytest.raises(UnsafeURLError):
        safe_get("http://good.com/")
    assert len(transport.requests) == 1


def test_safe_get_resolves_relative_redirects_against_the_hostname(monkeypatch):
    # The request URL is IP-pinned, so relative redirects must resolve against
    # the logical hostname URL, not the pinned one.
    monkeypatch.setattr(guard.socket, "getaddrinfo", _resolver({"good.com": "93.184.216.34"}))
    transport = _Transport(
        [httpx.Response(302, headers={"location": "/moved"}), httpx.Response(200, text="ok")]
    )
    _patched_client(monkeypatch, transport)

    response = safe_get("http://good.com/start")

    assert response.status_code == 200
    second = transport.requests[1]
    assert second.url.host == "93.184.216.34"
    assert second.url.path == "/moved"
    assert second.headers["host"] == "good.com"

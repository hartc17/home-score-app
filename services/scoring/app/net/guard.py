from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import anyio
import httpx

# Server-side fetches take user-supplied URLs (pasted listings, photo links), so
# they are an SSRF vector: a URL or a redirect can point at cloud metadata,
# loopback, or internal hosts. Every hop is validated to resolve only to public
# addresses, redirects are followed manually and bounded, and callers surface a
# generic error rather than echoing the target back.

MAX_REDIRECTS = 5
_TIMEOUT = 15.0
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HouseFlavorBot/1.0)"}


class UnsafeURLError(Exception):
    pass


def _ip_is_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def assert_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise UnsafeURLError("url must be an http(s) URL")
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise UnsafeURLError("host could not be resolved") from exc
    for info in infos:
        if _ip_is_blocked(ipaddress.ip_address(info[4][0])):
            raise UnsafeURLError("url resolves to a non-public address")


def _next_url(response: httpx.Response) -> str | None:
    if response.status_code not in (301, 302, 303, 307, 308):
        return None
    location = response.headers.get("location")
    return urljoin(str(response.request.url), location) if location else None


def safe_get(url: str) -> httpx.Response:
    with httpx.Client(follow_redirects=False, timeout=_TIMEOUT, headers=_HEADERS) as client:
        for _ in range(MAX_REDIRECTS + 1):
            assert_public_url(url)
            response = client.get(url)
            nxt = _next_url(response)
            if nxt is None:
                response.raise_for_status()
                return response
            url = nxt
    raise UnsafeURLError("too many redirects")


async def safe_get_async(url: str) -> httpx.Response:
    async with httpx.AsyncClient(follow_redirects=False, timeout=_TIMEOUT, headers=_HEADERS) as client:
        for _ in range(MAX_REDIRECTS + 1):
            await anyio.to_thread.run_sync(assert_public_url, url)
            response = await client.get(url)
            nxt = _next_url(response)
            if nxt is None:
                response.raise_for_status()
                return response
            url = nxt
    raise UnsafeURLError("too many redirects")

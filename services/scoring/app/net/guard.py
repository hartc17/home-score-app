from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import anyio
import httpx

# Server-side fetches take user-supplied URLs (pasted listings, photo links), so
# they are an SSRF vector: a URL or a redirect can point at cloud metadata,
# loopback, or internal hosts. Every hop is resolved once, every returned
# address is validated as public, and the connection is made to the validated
# address itself (Host header and SNI carry the hostname), so a DNS-rebinding
# flip between validation and connection has nothing to rebind. Redirects are
# followed manually and bounded, and callers surface a generic error rather
# than echoing the target back.

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


def resolve_public_address(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise UnsafeURLError("url must be an http(s) URL")
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise UnsafeURLError("host could not be resolved") from exc
    addresses = [info[4][0] for info in infos]
    if not addresses:
        raise UnsafeURLError("host could not be resolved")
    for address in addresses:
        if _ip_is_blocked(ipaddress.ip_address(address)):
            raise UnsafeURLError("url resolves to a non-public address")
    return addresses[0]


def _pin(url: str, address: str) -> tuple[str, dict[str, str], str]:
    # Swap the hostname for the validated address in the URL the request is
    # actually sent to, keeping the hostname in the Host header and SNI so
    # virtual hosting and certificate verification still work.
    parsed = urlparse(url)
    host_part = f"[{address}]" if ":" in address else address
    netloc = host_part if parsed.port is None else f"{host_part}:{parsed.port}"
    host_header = parsed.hostname if parsed.port is None else f"{parsed.hostname}:{parsed.port}"
    return parsed._replace(netloc=netloc).geturl(), {"Host": host_header}, parsed.hostname


def _pinned_request(client: httpx.Client | httpx.AsyncClient, url: str, address: str) -> httpx.Request:
    pinned_url, headers, hostname = _pin(url, address)
    request = client.build_request("GET", pinned_url, headers=headers)
    request.extensions["sni_hostname"] = hostname
    return request


def _next_url(response: httpx.Response, base_url: str) -> str | None:
    if response.status_code not in (301, 302, 303, 307, 308):
        return None
    location = response.headers.get("location")
    return urljoin(base_url, location) if location else None


def safe_get(url: str) -> httpx.Response:
    with httpx.Client(follow_redirects=False, timeout=_TIMEOUT, headers=_HEADERS) as client:
        for _ in range(MAX_REDIRECTS + 1):
            address = resolve_public_address(url)
            response = client.send(_pinned_request(client, url, address))
            nxt = _next_url(response, url)
            if nxt is None:
                response.raise_for_status()
                return response
            url = nxt
    raise UnsafeURLError("too many redirects")


async def safe_get_async(url: str) -> httpx.Response:
    async with httpx.AsyncClient(follow_redirects=False, timeout=_TIMEOUT, headers=_HEADERS) as client:
        for _ in range(MAX_REDIRECTS + 1):
            address = await anyio.to_thread.run_sync(resolve_public_address, url)
            response = await client.send(_pinned_request(client, url, address))
            nxt = _next_url(response, url)
            if nxt is None:
                response.raise_for_status()
                return response
            url = nxt
    raise UnsafeURLError("too many redirects")

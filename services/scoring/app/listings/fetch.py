from __future__ import annotations

import httpx

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HouseFlavorBot/1.0)"}
_TIMEOUT = 15.0


async def fetch_html(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT, headers=_HEADERS) as client:
        response = await client.get(url)
    response.raise_for_status()
    return response.text


def fetch_html_sync(url: str) -> str:
    with httpx.Client(follow_redirects=True, timeout=_TIMEOUT, headers=_HEADERS) as client:
        response = client.get(url)
    response.raise_for_status()
    return response.text

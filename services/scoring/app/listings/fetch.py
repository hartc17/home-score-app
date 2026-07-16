from __future__ import annotations

from app.net.guard import safe_get, safe_get_async


async def fetch_html(url: str) -> str:
    response = await safe_get_async(url)
    return response.text


def fetch_html_sync(url: str) -> str:
    return safe_get(url).text

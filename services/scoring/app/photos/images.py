from __future__ import annotations

import base64
import io
from collections.abc import Callable
from typing import Any

import httpx
from PIL import Image

# Photos are resized to a long edge near 1300px before they reach the vision
# model, which caps token cost without losing the detail the observation schema
# needs (scoring-contract.md section 8).

LONG_EDGE = 1300
JPEG_QUALITY = 82
_TIMEOUT = 15.0
_MEDIA_TYPE = "image/jpeg"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HouseFlavorBot/1.0)"}

Fetch = Callable[[str], bytes]


def fetch_bytes(url: str) -> bytes:
    response = httpx.get(url, timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True)
    response.raise_for_status()
    return response.content


def resize_to_long_edge(data: bytes, long_edge: int = LONG_EDGE) -> bytes:
    with Image.open(io.BytesIO(data)) as img:
        img = img.convert("RGB")
        longest = max(img.size)
        if longest > long_edge:
            scale = long_edge / longest
            img = img.resize((round(img.width * scale), round(img.height * scale)))
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=JPEG_QUALITY)
        return out.getvalue()


def url_block(url: str) -> dict[str, Any]:
    return {"type": "image", "source": {"type": "url", "url": url}}


def base64_block(data: bytes) -> dict[str, Any]:
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": _MEDIA_TYPE, "data": base64.b64encode(data).decode()},
    }


def prepare_image(url: str, fetch: Fetch = fetch_bytes) -> dict[str, Any]:
    # Fetching and decoding a remote image is a system boundary: a broken URL or
    # an undecodable body falls back to letting the model fetch the URL itself,
    # so one bad photo never fails the whole analysis.
    try:
        return base64_block(resize_to_long_edge(fetch(url)))
    except (httpx.HTTPError, httpx.InvalidURL, OSError, ValueError):
        return url_block(url)

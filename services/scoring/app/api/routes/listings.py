from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException

from app.listings.parser import parse_listing_html
from app.schemas import ListingFacts, ParseRequest

router = APIRouter()

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HouseFlavorBot/1.0)"}
_TIMEOUT = 15.0


async def fetch_html(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT, headers=_HEADERS) as client:
        response = await client.get(url)
    response.raise_for_status()
    return response.text


@router.post("/parse", response_model=ListingFacts)
async def parse_listing(request: ParseRequest) -> ListingFacts:
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=422, detail="url must be an http(s) listing URL")
    try:
        html = await fetch_html(request.url)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"could not fetch listing: {exc}") from exc
    return parse_listing_html(request.url, html)

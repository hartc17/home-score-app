from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException

from app.listings.fetch import fetch_html
from app.listings.parser import parse_listing_html
from app.schemas import ListingFacts, ParseRequest

router = APIRouter()


@router.post("/parse", response_model=ListingFacts)
async def parse_listing(request: ParseRequest) -> ListingFacts:
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=422, detail="url must be an http(s) listing URL")
    try:
        html = await fetch_html(request.url)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"could not fetch listing: {exc}") from exc
    return parse_listing_html(request.url, html)

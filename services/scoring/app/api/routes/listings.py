from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException

from app.listings.fetch import fetch_html
from app.listings.parser import parse_listing_html
from app.net.guard import UnsafeURLError
from app.schemas import ListingFacts, ParseRequest

router = APIRouter()


@router.post("/parse", response_model=ListingFacts)
async def parse_listing(request: ParseRequest) -> ListingFacts:
    try:
        html = await fetch_html(request.url)
    except UnsafeURLError as exc:
        raise HTTPException(status_code=422, detail="url is not a fetchable public listing URL") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="could not fetch the listing") from exc
    return parse_listing_html(request.url, html)

from fastapi import APIRouter

from app.schemas import ListingFacts, ParseRequest

router = APIRouter()


@router.post("/parse", response_model=ListingFacts)
async def parse_listing(request: ParseRequest) -> ListingFacts:
    return ListingFacts(url=request.url, photo_urls=[])

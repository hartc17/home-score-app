from fastapi import APIRouter

from app.photos.analyzer import analyze_photoset
from app.schemas import AnalyzeRequest, ListingObservations

router = APIRouter()


@router.post("/analyze", response_model=ListingObservations)
async def analyze_photos(request: AnalyzeRequest) -> ListingObservations:
    return analyze_photoset(request.listing)

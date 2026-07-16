from fastapi import APIRouter

from app.photos.analyzer import analyze_photoset
from app.schemas import AnalyzeRequest, ListingObservations

router = APIRouter()


# Sync so FastAPI runs the potentially blocking vision call in a threadpool
# rather than on the event loop.
@router.post("/analyze", response_model=ListingObservations)
def analyze_photos(request: AnalyzeRequest) -> ListingObservations:
    return analyze_photoset(request.listing)

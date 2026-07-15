from fastapi import APIRouter

from app.schemas import AnalyzeRequest, ListingObservations

router = APIRouter()


@router.post("/analyze", response_model=ListingObservations)
async def analyze_photos(request: AnalyzeRequest) -> ListingObservations:
    return ListingObservations(
        photos=[],
        flags=[],
        model="stub",
        schema_version="1.0",
    )

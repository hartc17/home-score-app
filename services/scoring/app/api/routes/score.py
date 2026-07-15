from fastapi import APIRouter

from app.schemas import ScoreRequest, ScoreResult
from app.scoring.engine import score

router = APIRouter()


@router.post("/score", response_model=ScoreResult)
async def score_listing(request: ScoreRequest) -> ScoreResult:
    return score(request.rubric, request.observations, request.facts)

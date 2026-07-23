from __future__ import annotations

from fastapi import APIRouter

from app.photos.analyzer import StubAnalyzer, resolve_analyzer
from app.schemas import HealthResponse

router = APIRouter()


# Reports whether the vision path is wired without making a billed API call:
# "configured" means a real analyzer would run, "unconfigured" means the stub.
# It confirms the key is present, not that it is valid; scoring a real listing
# confirms validity.
@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    analyzer = resolve_analyzer()
    configured = not isinstance(analyzer, StubAnalyzer)
    return HealthResponse(
        status="ok",
        vision="configured" if configured else "unconfigured",
        analysis_model=analyzer.model,
    )

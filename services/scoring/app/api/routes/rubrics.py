from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.rubrics.store import get_latest_rubric, get_rubric_versions, save_rubric
from app.schemas import RubricVersionInfo, SaveRubricRequest, StoredRubricResponse

router = APIRouter()


@router.post("", response_model=StoredRubricResponse)
def save(request: SaveRubricRequest, db: Session = Depends(get_db)) -> StoredRubricResponse:
    version, rubric = save_rubric(db, request.anon_id, request.rubric)
    return StoredRubricResponse(version=version, rubric=rubric)


@router.get("/{anon_id}", response_model=StoredRubricResponse)
def latest(anon_id: str, db: Session = Depends(get_db)) -> StoredRubricResponse:
    result = get_latest_rubric(db, anon_id)
    if result is None:
        raise HTTPException(status_code=404, detail="no rubric for this id")
    version, rubric = result
    return StoredRubricResponse(version=version, rubric=rubric)


@router.get("/{anon_id}/versions", response_model=list[RubricVersionInfo])
def versions(anon_id: str, db: Session = Depends(get_db)) -> list[RubricVersionInfo]:
    return [RubricVersionInfo(version=v, created_at=c) for v, c in get_rubric_versions(db, anon_id)]

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import RubricRow, User
from app.schemas import (
    CategoryWeights,
    Rubric,
    RubricArchetype,
    RubricDirections,
    RubricGates,
)


def _get_or_create_user(db: Session, anon_id: str) -> User:
    user = db.scalar(select(User).where(User.anon_id == anon_id))
    if user is None:
        user = User(anon_id=anon_id)
        db.add(user)
        db.flush()
    return user


def rubric_from_row(row: RubricRow) -> Rubric:
    return Rubric(
        version=row.schema_version,
        gates=RubricGates(**row.gates_json) if row.gates_json else None,
        category_weights=CategoryWeights(**row.category_weights_json),
        item_weights=row.item_weights_json,
        directions=RubricDirections(**row.directions_json),
        archetype=RubricArchetype(**row.archetype_json),
        confidence=row.confidence_json,
    )


def save_rubric_for_user(db: Session, user: User, rubric: Rubric) -> tuple[int, Rubric]:
    top = db.scalar(select(func.max(RubricRow.version)).where(RubricRow.user_id == user.id))
    version = (top + 1) if top is not None else 1
    row = RubricRow(
        user_id=user.id,
        version=version,
        schema_version=rubric.version,
        gates_json=rubric.gates.model_dump() if rubric.gates else None,
        category_weights_json=rubric.category_weights.model_dump(),
        item_weights_json=rubric.item_weights,
        directions_json=rubric.directions.model_dump(),
        archetype_json=rubric.archetype.model_dump(),
        confidence_json=rubric.confidence,
    )
    db.add(row)
    db.commit()
    return version, rubric_from_row(row)


def save_rubric(db: Session, anon_id: str, rubric: Rubric) -> tuple[int, Rubric]:
    return save_rubric_for_user(db, _get_or_create_user(db, anon_id), rubric)


def latest_rubric_for_user(db: Session, user: User) -> Rubric | None:
    row = db.scalar(
        select(RubricRow).where(RubricRow.user_id == user.id).order_by(RubricRow.version.desc()).limit(1)
    )
    return rubric_from_row(row) if row is not None else None


def get_latest_rubric_row(db: Session, anon_id: str) -> RubricRow | None:
    return db.scalar(
        select(RubricRow)
        .join(User)
        .where(User.anon_id == anon_id)
        .order_by(RubricRow.version.desc())
        .limit(1)
    )


def get_latest_rubric(db: Session, anon_id: str) -> tuple[int, Rubric] | None:
    row = db.scalar(
        select(RubricRow)
        .join(User)
        .where(User.anon_id == anon_id)
        .order_by(RubricRow.version.desc())
        .limit(1)
    )
    return (row.version, rubric_from_row(row)) if row is not None else None


def get_rubric_by_version(db: Session, anon_id: str, version: int) -> Rubric | None:
    row = db.scalar(
        select(RubricRow)
        .join(User)
        .where(User.anon_id == anon_id, RubricRow.version == version)
    )
    return rubric_from_row(row) if row is not None else None


def get_rubric_versions(db: Session, anon_id: str) -> list[tuple[int, datetime]]:
    rows = db.scalars(
        select(RubricRow)
        .join(User)
        .where(User.anon_id == anon_id)
        .order_by(RubricRow.version)
    ).all()
    return [(r.version, r.created_at) for r in rows]

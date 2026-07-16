from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Anonymous device id from the quiz. Real login (magic-link) later sets `email`
    # on the same row, so an anonymous rubric is claimed without any migration.
    anon_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rubrics: Mapped[list[RubricRow]] = relationship(
        back_populates="user", cascade="all, delete-orphan", order_by="RubricRow.version"
    )


class RubricRow(Base):
    __tablename__ = "rubrics"
    __table_args__ = (UniqueConstraint("user_id", "version", name="uq_rubric_user_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    schema_version: Mapped[str] = mapped_column(String(16))
    gates_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    category_weights_json: Mapped[dict] = mapped_column(JSON)
    item_weights_json: Mapped[dict] = mapped_column(JSON)
    directions_json: Mapped[dict] = mapped_column(JSON)
    archetype_json: Mapped[dict] = mapped_column(JSON)
    confidence_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="rubrics")

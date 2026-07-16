from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint, func
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


# A listing and its photo analysis are preference-neutral, so they are stored once
# and shared across users. A score is per-rubric, so it links the listing to the
# rubric that produced it.


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), unique=True, index=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    facts_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    analysis: Mapped[PhotoAnalysis | None] = relationship(
        back_populates="listing", cascade="all, delete-orphan", uselist=False
    )
    scores: Mapped[list[Score]] = relationship(back_populates="listing", cascade="all, delete-orphan")


class PhotoAnalysis(Base):
    __tablename__ = "photo_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), unique=True, index=True)
    model: Mapped[str] = mapped_column(String(64))
    schema_version: Mapped[str] = mapped_column(String(16))
    photoset_hash: Mapped[str] = mapped_column(String(64), index=True)
    observations_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    listing: Mapped[Listing] = relationship(back_populates="analysis")


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    rubric_id: Mapped[int] = mapped_column(ForeignKey("rubrics.id"), index=True)
    rubric_version: Mapped[int] = mapped_column(Integer)
    total: Mapped[float] = mapped_column(Float)
    verdict: Mapped[str] = mapped_column(String(16))
    category_scores_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    listing: Mapped[Listing] = relationship(back_populates="scores")
    dd_items: Mapped[list[DdItem]] = relationship(back_populates="score", cascade="all, delete-orphan")


class DdItem(Base):
    __tablename__ = "dd_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    score_id: Mapped[int] = mapped_column(ForeignKey("scores.id"), index=True)
    text: Mapped[str] = mapped_column(String(512))
    checked: Mapped[bool] = mapped_column(Boolean, default=False)

    score: Mapped[Score] = relationship(back_populates="dd_items")

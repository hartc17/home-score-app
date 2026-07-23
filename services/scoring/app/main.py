from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import auth, health, listings, photos, rubrics, score, scores
from app.db.base import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="HouseFlavor Scoring Service", version="0.0.1", lifespan=lifespan)

app.include_router(listings.router, prefix="/listings", tags=["listings"])
app.include_router(photos.router, prefix="/photos", tags=["photos"])
app.include_router(rubrics.router, prefix="/rubrics", tags=["rubrics"])
app.include_router(scores.router, prefix="/scores", tags=["scores"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(health.router, tags=["health"])
app.include_router(score.router, tags=["score"])

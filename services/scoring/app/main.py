from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import listings, photos, rubrics, score
from app.db.base import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="HouseFlavor Scoring Service", version="0.0.1", lifespan=lifespan)

app.include_router(listings.router, prefix="/listings", tags=["listings"])
app.include_router(photos.router, prefix="/photos", tags=["photos"])
app.include_router(rubrics.router, prefix="/rubrics", tags=["rubrics"])
app.include_router(score.router, tags=["score"])

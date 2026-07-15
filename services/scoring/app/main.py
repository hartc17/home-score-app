from fastapi import FastAPI

from app.api.routes import listings, photos, score

app = FastAPI(title="HouseFlavor Scoring Service", version="0.0.1")

app.include_router(listings.router, prefix="/listings", tags=["listings"])
app.include_router(photos.router, prefix="/photos", tags=["photos"])
app.include_router(score.router, tags=["score"])

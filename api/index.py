from fastapi import FastAPI
from src.phase3.api.routes_cities import router as cities_router
from src.phase3.api.routes_recommendations import router as rec_router

app = FastAPI(title="Vercel FastAPI Backend")

app.include_router(cities_router, prefix="/api/v1")
app.include_router(rec_router, prefix="/api/v1")

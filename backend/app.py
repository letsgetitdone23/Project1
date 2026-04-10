import os
from fastapi import FastAPI
from dotenv import load_dotenv

from .api import routes_health, routes_recommendations


load_dotenv()

app = FastAPI(title="AI Restaurant Recommender", version="0.1.0")


@app.on_event("startup")
async def on_startup() -> None:
    # Placeholder for future startup hooks (DB connectivity checks, etc.)
    _ = os.getenv("DATABASE_URL")


app.include_router(routes_health.router, prefix="/v1")
app.include_router(routes_recommendations.router, prefix="/v1")


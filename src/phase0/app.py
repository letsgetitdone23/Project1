import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.phase0.api import routes_health
from src.phase3.api import routes_cities
from src.phase3.api import routes_localities
from src.phase3.api import routes_recommendations
from src.phase5.ui import routes_ui
from src.phase6.api import routes_metrics


load_dotenv()


def _cors_allow_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if raw_origins:
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

@asynccontextmanager
async def lifespan(_app: FastAPI):
    _ = os.getenv("DATABASE_URL")
    yield


app = FastAPI(title="AI Restaurant Recommender", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(routes_health.router, prefix="/v1")
app.include_router(routes_cities.router, prefix="/v1")
app.include_router(routes_localities.router, prefix="/v1")
app.include_router(routes_recommendations.router, prefix="/v1")
app.include_router(routes_metrics.router, prefix="/v1")
app.include_router(routes_ui.router)


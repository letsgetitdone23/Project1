from fastapi import FastAPI
from backend.api import routes_health, routes_recommendations

app = FastAPI(title="Vercel FastAPI Backend")

# Vercel routes /api/v1/* to this file automatically, and passes the path to the app.
# We mount the routes with the prefix so FastAPI correctly matches /api/v1/cities.
app.include_router(routes_health.router, prefix="/api/v1")
app.include_router(routes_recommendations.router, prefix="/api/v1")

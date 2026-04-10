from __future__ import annotations

import asyncio

import streamlit as st
from fastapi import HTTPException

from src.phase0.api.routes_health import health
from src.phase2.api.schemas import RecommendationRequest
from src.phase3.api.routes_cities import list_cities
from src.phase3.api.routes_recommendations import recommend
from src.phase6.api.routes_metrics import get_metrics


st.set_page_config(page_title="Restaurant Backend Console", layout="wide")
st.title("Restaurant Recommender Backend (Streamlit)")
st.caption("Operational console for health, data lookup, and recommendation execution.")

health_col, cities_col, metrics_col = st.columns(3)

with health_col:
    st.subheader("Health")
    if st.button("Check Health"):
        response = asyncio.run(health())
        st.json(response)

with cities_col:
    st.subheader("Cities")
    if st.button("Load Cities"):
        st.json(list_cities())

with metrics_col:
    st.subheader("Metrics")
    if st.button("Load Metrics"):
        st.json(get_metrics())

st.divider()
st.subheader("Run Recommendation")

with st.form("recommendation_form"):
    location = st.text_input("Location", value="bangalore")
    budget = st.number_input("Budget (cost for two)", min_value=1.0, value=1200.0, step=100.0)
    cuisine_text = st.text_input("Cuisines (comma-separated)", value="Italian, Chinese")
    min_rating = st.slider("Minimum Rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
    tags_text = st.text_input("Additional Preferences (comma-separated)", value="family-friendly, quick service")
    top_k_raw = st.text_input("Max recommendations (optional)", value="")
    submitted = st.form_submit_button("Get Recommendations")

if submitted:
    cuisines = [value.strip() for value in cuisine_text.split(",") if value.strip()]
    tags = [value.strip() for value in tags_text.split(",") if value.strip()]
    try:
        top_k = int(top_k_raw) if top_k_raw.strip() else None
    except ValueError:
        st.error("Max recommendations must be a valid integer.")
        st.stop()

    request = RecommendationRequest(
        location=location,
        budget=budget,
        cuisine=cuisines or None,
        min_rating=min_rating,
        additional_preferences=tags or None,
        top_k=top_k,
    )
    try:
        response = recommend(request)
    except HTTPException as exc:
        st.error(f"API error {exc.status_code}: {exc.detail}")
    else:
        st.success("Recommendation response generated.")
        st.json(response.model_dump())

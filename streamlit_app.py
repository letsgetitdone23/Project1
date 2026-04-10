from __future__ import annotations

import streamlit as st
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.phase0.data.repository import init_db
from src.phase2.api.schemas import RecommendationRequest
from src.phase3.api.routes_cities import list_cities
from src.phase3.api.routes_recommendations import recommend


FALLBACK_CITIES = [
    "banashankari",
    "bannerghatta road",
    "basavanagudi",
    "bellandur",
    "brigade road",
    "brookefield",
    "btm",
    "church street",
    "electronic city",
    "frazer town",
    "hsr",
    "indiranagar",
    "jayanagar",
    "jp nagar",
    "kalyan nagar",
    "kammanahalli",
    "koramangala 4th block",
    "koramangala 5th block",
    "koramangala 6th block",
    "koramangala 7th block",
    "lavelle road",
    "malleshwaram",
    "marathahalli",
    "mg road",
    "new bel road",
    "old airport road",
    "rajajinagar",
    "residency road",
    "sarjapur road",
    "whitefield",
]


st.set_page_config(page_title="The Culinary Curator", layout="wide")
st.title("The Culinary Curator")
st.caption("Discover restaurants you'll love.")

try:
    init_db()
except SQLAlchemyError as exc:
    st.error(f"Database initialization failed: {exc}")

try:
    cities_payload = list_cities()
    city_options = cities_payload.get("cities", FALLBACK_CITIES)
    if not city_options:
        city_options = FALLBACK_CITIES
except HTTPException:
    city_options = FALLBACK_CITIES

with st.form("recommendation_form"):
    c1, c2 = st.columns(2)
    with c1:
        location = st.selectbox("Location", options=city_options, index=0)
        budget = st.number_input("Budget (cost for two)", min_value=1.0, value=1200.0, step=100.0)
        min_rating = st.slider("Minimum Rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
    with c2:
        cuisine_text = st.text_input("Cuisine Preferences (comma-separated)", value="Italian, Chinese")
        tags_text = st.text_input(
            "Additional Preferences (comma-separated)", value="family-friendly, quick service"
        )
        top_k_raw = st.text_input("Max Recommendations (optional)", value="")
    submitted = st.form_submit_button("Get Recommendations", use_container_width=True)

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
        recommendations = response.recommendations or []
        if response.summary:
            st.info(response.summary)
        if not recommendations:
            st.warning("No matches found. Try lowering rating, widening budget, or changing location.")
        else:
            st.subheader(f"Top Picks for You ({len(recommendations)})")
            for item in recommendations:
                cuisines_text = " • ".join(item.cuisine or []) or "Cuisine N/A"
                locality = f", {item.locality}" if item.locality else ""
                st.markdown(
                    f"### {item.name}\n"
                    f"**Location:** {item.city}{locality}  \n"
                    f"**Rating:** {item.rating if item.rating is not None else 'N/A'}  \n"
                    f"**Cost for two:** {item.estimated_cost_for_two if item.estimated_cost_for_two is not None else 'N/A'}  \n"
                    f"**Cuisine:** {cuisines_text}  \n"
                    f"**Why you'll love it:** {item.explanation}"
                )
                st.divider()

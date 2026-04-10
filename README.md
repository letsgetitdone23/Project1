## AI-Powered Restaurant Recommendation System

This project implements an AI-powered restaurant recommender inspired by Zomato.  
This README currently covers the **Phase 0** and **Phase 1** setup: project bootstrap and data ingestion.

### Phase-based `src` organization

The code is also organized phase-wise under `src/`:
- `src/phase0/` -> baseline app, health route, DB models/repository
- `src/phase1/` -> ingestion, transformation, quality checks, DB load
- `src/phase2/` -> request/response schemas and preference normalization
- `src/phase3/` -> candidate retrieval, deterministic scoring, recommendations route
- `src/phase4/` -> Groq prompt orchestration, parsing, grounding checks
- `src/phase5/` -> response composition and basic UI
- `src/phase6/` -> observability (metrics/logging) and offline evaluation harness

### Prerequisites

- Python 3.10+ recommended
- Internet access (for downloading the Hugging Face dataset)

### Install dependencies

```bash
pip install -r requirements.txt
```

### Environment configuration

Copy the example environment file and adjust as needed:

```bash
cp .env.example .env
```

Defaults will:
- Use SQLite at `restaurants.db`
- Use the Hugging Face dataset `ManikaSaini/zomato-restaurant-recommendation`

### Run the API skeleton (Phase 0, via `src/`)

The API currently exposes a health-check endpoint and recommendations route:

```bash
uvicorn src.phase0.app:app --reload
```

Then open:
- `GET http://localhost:8000/v1/health`
- `GET http://localhost:8000/v1/cities`
- `POST http://localhost:8000/v1/recommendations`
- `GET http://localhost:8000/v1/metrics`

### Run the data ingestion pipeline (Phase 1, via `src/`)

Run the following steps in order from the project root:

1. **Ingest raw dataset from Hugging Face**

```bash
python -m src.phase1.data_pipeline.ingest_hf_dataset
```

2. **Transform and normalize restaurants**

```bash
python -m src.phase1.data_pipeline.transform_restaurants
```

3. **Run data quality checks**

```bash
python -m src.phase1.data_pipeline.validate_quality
```

4. **Load clean data into the database**

```bash
python -m src.phase1.data_pipeline.load_to_db
```

After step 4, the `restaurants` table in the configured database will be populated and ready for later phases (retrieval, LLM ranking, etc.).

> Note: older `backend/` and `data_pipeline/` modules are now superseded by the phase-wise structure under `src/`. Prefer using the `src.phaseX...` imports and commands shown above.

### Phase 6 offline evaluation (optional)

Run benchmark profiles and generate a report:

```bash
python -m src.phase6.evaluation.run_offline_eval
```

Report path:
- `data/reports/offline_eval_report.json`

### City dropdown source (UI contract)

- Frontend location dropdown should consume `GET /v1/cities`.
- This endpoint returns all distinct values from the `city` column.
- Current processed dataset snapshot contains `30` city values.
- Frontend recommendation UI intentionally hides raw request tracing text (request id / timing) from end users.

### Deploy backend on Streamlit

Use Streamlit Community Cloud to run backend operations UI:

1. Add dependencies:
   - `requirements.txt` already includes `streamlit`.
2. Set Streamlit secrets (app settings):
   - `GROQ_API_KEY`
   - `DATABASE_URL`
   - `CORS_ALLOW_ORIGINS` (include your Vercel URL and local URL)
   - You can start from `.streamlit/secrets.toml.example`.
3. Streamlit entrypoint:
   - `streamlit_app.py`
4. Local check:

```bash
streamlit run streamlit_app.py
```

The Streamlit backend console supports:
- Cities lookup
- Metrics snapshot
- Recommendation execution using existing backend services

### Connect Vercel frontend to deployed backend

In Vercel project settings, set:
- `NEXT_PUBLIC_API_BASE_URL=<your_streamlit_backend_url>`

In backend secrets, set:
- `CORS_ALLOW_ORIGINS=https://<your-vercel-domain>,http://localhost:3000`


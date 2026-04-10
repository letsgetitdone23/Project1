# AI-Powered Restaurant Recommendation System

Detailed phase-wise architecture for the Zomato-style recommendation project described in `docs/problemstatement.md`.

## 1) System Vision and Scope

Build an intelligent recommendation service that combines:
- deterministic filtering over structured restaurant data, and
- LLM-powered ranking and explanations.

### Core user outcomes
- Users can provide preferences: location, budget, cuisine, minimum rating, additional preferences.
- System returns top recommendations with explainable "why this fits" text.
- Results are fast, consistent, and robust against LLM/API failures.

---

## 2) Reference High-Level Architecture

```text
[Web/Mobile UI]
      |
      v
[API Gateway / FastAPI Service]
      |
      +--> [Input Validation + Preference Normalizer]
      |
      +--> [Candidate Retrieval Engine]
      |        |
      |        +--> [Restaurant DB]
      |
      +--> [LLM Orchestrator + Prompt Builder]
      |        |
      |        +--> [LLM Provider]
      |
      +--> [Response Composer]
      |
      +--> [Observability: logs, metrics, traces]

[Batch ETL Pipeline] ---> [Restaurant DB]
```

---

## 3) Phase-Wise Detailed Architecture

## Phase 0: Planning and Baseline Setup

### Objective
Create foundational project setup, environments, and quality guardrails.

### Components
- **Repo structure**
  - `backend/` (API, services, retrieval, llm)
  - `data_pipeline/` (ingestion + preprocessing)
  - `frontend/` (optional in MVP, else simple template UI)
  - `docs/` (architecture, API contracts, prompt design)
- **Environment configs**
  - `.env` for DB URL, LLM key, logging level
- **Tooling**
  - formatter, linter, unit test framework

### Deliverables
- Running service skeleton with health endpoint
- CI checks for lint + unit tests
- Config templates (`.env.example`)

### Exit criteria
- Team can run app locally using one command
- CI validates code quality on each change

---

## Phase 1: Data Ingestion and Data Modeling

### Objective
Build repeatable ingestion from Hugging Face and create a clean queryable schema.

### Inputs
- Dataset: `https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation`

### Components
- **Dataset connector**
  - Pull latest dataset snapshot
- **Raw data store**
  - Persist raw records for reproducibility
- **Preprocessing engine**
  - Field mapping and type casting
  - Missing value treatment
  - Dedupe by restaurant + location key
  - Normalize cuisine lists and location names
- **Data quality checks**
  - Required fields present
  - Rating in valid range
  - Cost value parsable
- **Persisted model**
  - `restaurants` table and indexes

### Suggested schema (MVP)
- `id` (string/int)
- `name` (text)
- `city` (text, indexed)
- `locality` (text, indexed)
- `cuisines` (array/text)
- `avg_cost_for_two` (numeric, indexed)
- `rating` (numeric, indexed)
- `votes` (int, optional)
- `features` (json/text: family-friendly, quick service, etc.)
- `last_updated_at` (timestamp)

### Data pipeline flow
1. Fetch dataset snapshot
2. Validate schema and required columns
3. Transform and normalize
4. Run quality assertions
5. Upsert into DB
6. Publish ingestion report

### Deliverables
- ETL job script
- Data dictionary
- DQ report per run

### Exit criteria
- End-to-end ingestion reproducible and idempotent
- DB populated with clean searchable records

---

## Phase 2: User Input and Preference Normalization

### Objective
Convert raw user preferences into canonical query inputs.

### Components
- **Input contract**
  - API payload schema (Pydantic/JSON schema)
- **Validation layer**
  - Required checks and type checks
- **Preference normalizer**
  - Synonym mapping: "cheap" -> `low`, "banglore" -> `bangalore`
  - Cuisine canonicalization: `"north indian"` -> `"North Indian"`
  - Budget is accepted as a **numeric cost-for-two** and converted into a tolerance band for retrieval
- **Groq LLM readiness**
  - Phase 2 prepares normalized, structured inputs specifically for downstream **Groq LLM** prompting in Phases 3 and 4.
  - Groq credentials are loaded from `.env` (for example: `GROQ_API_KEY`).
- **Defaults and fallbacks**
  - If missing min rating, use default threshold (example: 3.5)
  - `top_k` is optional in API; if omitted, backend returns all ranked matches (no fixed default of 20)

### API contract (example)
`POST /v1/recommendations`

Request:
```json
{
  "location": "Bangalore",
  "budget": 1200,
  "cuisine": ["Italian", "Chinese"],
  "min_rating": 4.0,
  "additional_preferences": ["family-friendly", "quick service"]
}
```

Validated internal form:
```json
{
  "city": "bangalore",
  "budget_band": {"min": 780, "max": 1620},
  "cuisines": ["Italian", "Chinese"],
  "min_rating": 4.0,
  "tags": ["family_friendly", "quick_service"],
  "top_k": null
}
```

### Deliverables
- Input DTO/schema
- Normalization dictionaries and utilities
- Error response spec

### Exit criteria
- Invalid requests get meaningful errors
- Valid requests become deterministic normalized objects

---

## Phase 3: Candidate Retrieval and Deterministic Scoring

### Objective
Retrieve a relevant subset before calling the LLM.

### Components
- **Hard filter module**
  - city/location match
  - rating >= min_rating
  - cost within normalized budget band (strict min-max range, no extra widening)
- **Soft match module**
  - cuisine overlap score
  - tag preference score
- **Deterministic scorer**
  - Weighted score:
    - rating weight (example 0.4)
    - cuisine match (0.3)
    - budget fit (0.2)
    - preference tags (0.1)
- **Candidate selector**
  - pick top N candidates for LLM context window
  - current backend uses a fixed candidate shortlist size (40) for LLM ranking
- **Groq integration handoff**
  - Phase 3 sends shortlisted candidates to **Groq LLM** in a structured format for final reasoning and ranking in Phase 4.
  - Groq API key is read from `.env` (for example: `GROQ_API_KEY`).

### Query strategy
- Use indexed filters first for speed.
- Apply scorer in app layer or SQL window functions.
- Return a consistent sorted list for observability.

### Response from retrieval (internal)
```json
[
  {
    "restaurant_id": "r123",
    "name": "Trattoria Roma",
    "city": "bangalore",
    "cuisines": ["Italian"],
    "rating": 4.3,
    "avg_cost_for_two": 1400,
    "match_score": 0.87,
    "matched_tags": ["family_friendly"]
  }
]
```

### Deliverables
- Retrieval service
- Scoring module
- Unit tests for filter/scoring logic

### Exit criteria
- Candidate set quality acceptable without LLM
- P95 retrieval latency target met (example <150 ms)

---

## Phase 4: LLM Ranking and Explainability Layer

### Objective
Use LLM to rank shortlisted candidates and generate grounded explanations.

### Components
- **Prompt builder**
  - System rules: use only provided candidates
  - User preferences + candidate JSON
  - Budget is represented as numeric target and normalized budget band in prompt context
- **LLM orchestrator**
  - retries, timeout, circuit breaker
  - model fallback (optional)
  - provider: **Groq LLM API**
  - authentication via `.env` key (for example: `GROQ_API_KEY`)
- **Output schema validator**
  - Parse and validate JSON output
- **Safety/grounding checks**
  - Reject outputs containing unknown restaurant names

### Prompt template (conceptual)
- Role: recommendation analyst
- Inputs:
  - normalized user preferences
  - candidate restaurants list
- Instructions:
  - rank top K
  - explanation for each
  - concise summary paragraph
  - do not invent any restaurant not in candidate list

### LLM output schema
```json
{
  "summary": "Top picks balancing budget and cuisine.",
  "recommendations": [
    {
      "restaurant_id": "r123",
      "rank": 1,
      "fit_reason": "Matches Italian preference, strong rating, and medium budget fit."
    }
  ]
}
```

### Failure handling
- If parse fails or timeout occurs:
  - return deterministic ranked list with template explanations
  - log failure event for analysis

### Deliverables
- Prompt versions and changelog
- LLM integration module
- Schema parser and guardrails

### Exit criteria
- Stable structured output for >95% valid calls
- Hallucination rate near zero via grounding checks

---

## Phase 5: API Response Composition and UI Experience

### Objective
Present clear user-friendly recommendations with transparent rationale.

### Current implementation plan
- **Now:** implement Phase 5 backend (response composer + presentation contract + metadata).
- **Later:** implement frontend website updates (results cards, loading/empty/error states) after backend stabilization.
  - Update completed: frontend now uses dropdown location + numeric budget input.
  - Location options are fetched from backend `GET /v1/cities`, which returns all distinct values from the `city` column (30 values in current dataset snapshot).
  - New direction: build a richer **Next.js frontend** inspired by `design/screen.png` and `design/screen2.png` for iterative UI enhancement.
  - Implemented design direction:
    - landing hero with dark visual style, dual CTA buttons, and concierge side card
    - curation form panel with location/min-rating/budget/cuisine/preferences controls
    - results experience with left filter rail and central "Top Picks for You" stacked cards
    - recommendation cards now include compact metadata chips (rating/cuisine/cost), AI "why you'll love it" panel, and action buttons
    - frontend keeps existing backend integration (`GET /v1/cities`, `POST /v1/recommendations`) while adopting the new presentation layout

### Components
- **Response composer**
  - Merge DB fields + LLM rank/explanation
  - Add metadata (request id, timing, fallback_used, optional summary)
  - For "no match" scenarios, return `200` with empty `recommendations` plus a user-guidance `summary` (instead of raising `404`)
- **Presentation contract**
  - list of recommendations with:
    - name, cuisine, rating, estimated cost, AI explanation
- **Client UI (Next.js direction)**
  - Next.js app (`frontend-next`) with hero section + curation panel + recommendation cards
  - top navigation includes location selector, search box, and user entry area in line with design direction
  - fetches selectable values from backend (`GET /v1/cities`)
  - submits recommendation requests to backend (`POST /v1/recommendations`)
  - supports loading, error, and recommendation summary display (request id/timing metadata is not shown in frontend)

### Response shape (client-facing)
```json
{
  "request_id": "req_abc",
  "used_fallback": false,
  "summary": "Optional recommendation summary or no-match guidance text.",
  "recommendations": [
    {
      "name": "Trattoria Roma",
      "cuisine": ["Italian"],
      "rating": 4.3,
      "estimated_cost_for_two": 1400,
      "explanation": "Great Italian option with strong ratings in your budget."
    }
  ]
}
```

### Deliverables
- Stable external API (backend-first delivery)
- Next.js frontend scaffold with API integration (iterative enhancement path)
- API documentation

### Exit criteria
- Users can submit preferences and receive understandable top-K recommendations
- API and UI handle errors gracefully
- No-match requests are handled gracefully in UI without API 404 interruption

---

## Phase 6: Observability, Evaluation, and Continuous Improvement

### Objective
Measure quality, reliability, and user impact; iterate safely.

### Components
- **Metrics**
  - API latency, retrieval latency, LLM latency
  - fallback rate, parse failure rate
  - user engagement (CTR on recommended restaurant)
- **Structured logging**
  - request context, filter counts, selected candidates, model used
- **Offline evaluation harness**
  - curated test profiles and expected behavior
- **Prompt and model versioning**
  - compare quality across versions

### Quality framework
- **Functional**
  - correct filtering and ranking constraints
- **Behavioral**
  - explanation relevance
- **Reliability**
  - service uptime and graceful degradation

### Deliverables
- Dashboard for operational metrics
- Evaluation suite with benchmark scenarios
- Iteration playbook (when to tune filters vs prompt)

### Exit criteria
- Baseline KPI dashboard active
- Regression checks part of release workflow

---

## 4) Cross-Cutting Architecture Decisions

### Security and privacy
- Keep secrets in environment variables or secret manager.
- Mask user-identifying data in logs.

### Performance
- DB indexes on `city`, `rating`, `avg_cost_for_two`.
- Cache frequent normalized queries (short TTL).

### Scalability
- Stateless API instances behind load balancer.
- Separate batch ETL from online serving.

### Reliability
- Timeouts and retries for external LLM calls.
- Deterministic fallback for degraded mode.

### Maintainability
- Versioned prompt templates.
- Clear module boundaries: retrieval, llm, composition.

---

## 4.1) Deployment Architecture

### Target hosting
- **Backend deployment:** Streamlit
- **Frontend deployment:** Vercel

### Runtime topology
```text
[User Browser]
      |
      v
[Vercel: Next.js Frontend]
      |
      v  (HTTPS API calls)
[Streamlit-hosted Backend Service]
      |
      +--> [Restaurant DB]
      |
      +--> [Groq LLM API]
```

### Deployment responsibilities
- **Vercel (frontend)**
  - Hosts `frontend-next` (Next.js app).
  - Uses environment variable `NEXT_PUBLIC_API_BASE_URL` to call backend endpoints.
  - Serves UI assets, SSR/static routes, and recommendation screens.
- **Streamlit (backend)**
  - Hosts backend API runtime and recommendation pipeline.
  - Exposes API endpoints consumed by frontend (`/v1/health`, `/v1/cities`, `/v1/recommendations`, `/v1/metrics`).
  - Stores runtime secrets as environment variables (for example `GROQ_API_KEY`, DB URL).

### Environment and configuration checklist
- **Frontend on Vercel**
  - Set `NEXT_PUBLIC_API_BASE_URL` to the public Streamlit backend URL.
  - Ensure CORS on backend allows the Vercel frontend domain.
- **Backend on Streamlit**
  - Set database connection configuration and `.env` values in Streamlit secrets/settings.
  - Keep API keys server-side only; never expose backend secrets to frontend.
  - Enable structured logs for request tracing and fallback diagnostics.

### Release flow (recommended)
1. Deploy backend to Streamlit and validate `GET /v1/health`.
2. Deploy frontend to Vercel with updated backend URL.
3. Smoke test: city load, recommendation request, and fallback behavior.
4. Monitor API latency, fallback rate, and error logs after release.

---

## 4.2) Operational Validation Snapshot

### Verified API/UI runtime behavior
- `GET /v1/cities` returns `30` normalized location values used by frontend dropdowns.
- Frontends use backend city list first and include full 30-city fallback options if city API is unavailable.
- Recommendation no-match flow returns `200` with:
  - empty `recommendations`
  - explanatory `summary` for user guidance
- Next.js frontend hides raw request tracing text (request id and latency), while still using backend metadata internally.
- Backend and frontend run successfully on local ports:
  - backend: `127.0.0.1:8000`
  - frontend: `127.0.0.1:3000`

### Sample successful recommendation outcomes (validated)
- `banashankari` -> top picks include `Onesta`, `The Blue Wagon - Kitchen`, `Stoned Monkey`
- `hsr` -> top picks include `Tipsy Bull - The Bar Exchange`, `Shift`, `Opus Food Stories`
- `indiranagar` -> top picks include `Delhi Highway`, `Burma Burma`, `Toit`

---

## 5) Suggested Service Modules (Backend)

```text
backend/
  app.py
  api/
    routes_recommendations.py
    schemas.py
  services/
    preference_normalizer.py
    retrieval_engine.py
    deterministic_scorer.py
    llm_prompt_builder.py
    llm_orchestrator.py
    response_composer.py
  data/
    repository.py
    models.py
  observability/
    logger.py
    metrics.py

data_pipeline/
  ingest_hf_dataset.py
  transform_restaurants.py
  validate_quality.py
  load_to_db.py
```

---

## 6) Phase-to-Timeline Mapping (Practical Execution)

- **Week 1:** Phase 0 + Phase 1 (data ready and queryable)
- **Week 2:** Phase 2 + Phase 3 (deterministic recommender API works)
- **Week 3:** Phase 4 (LLM ranking + fallback)
- **Week 4:** Phase 5 + Phase 6 baseline (UI, docs, metrics, evaluation)

---

## 7) Definition of Done (Project Level)

- End user can request recommendations using all required preferences.
- API returns top restaurants with grounded AI explanations.
- System handles LLM failures with deterministic fallback.
- Metrics and logs are available for operational monitoring.
- Documentation covers architecture, API contract, and run instructions.


from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter()


@router.get("/", response_class=HTMLResponse, summary="Basic end-to-end UI")
def home() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Restaurant Recommender</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background: #f7f7fb; color: #222; }
    .card { background: #fff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); padding: 16px; margin-bottom: 14px; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    label { font-size: 13px; font-weight: 600; display: block; margin-bottom: 6px; }
    input, select { width: 100%; padding: 10px; border: 1px solid #d9d9e3; border-radius: 8px; }
    button { background: #2d6cdf; color: white; border: 0; border-radius: 8px; padding: 10px 16px; cursor: pointer; font-weight: 600; }
    button:disabled { opacity: 0.7; cursor: not-allowed; }
    .muted { color: #666; font-size: 13px; }
    .error { color: #b00020; font-weight: 600; }
    .pill { display: inline-block; background: #eef3ff; color: #2d6cdf; padding: 2px 8px; border-radius: 999px; font-size: 12px; margin-right: 6px; }
  </style>
</head>
<body>
  <h2>AI-Powered Restaurant Recommendation</h2>
  <p class="muted">Restaurant recommendations</p>

  <div class="card">
    <div class="row">
      <div>
        <label for="location">Location</label>
        <select id="location"></select>
      </div>
      <div>
        <label for="budget">Budget (cost for two)</label>
        <input id="budget" type="number" min="100" step="50" value="1200" />
      </div>
      <div>
        <label for="cuisine">Cuisine (comma separated)</label>
        <input id="cuisine" value="Italian, Chinese" />
      </div>
      <div>
        <label for="rating">Minimum Rating (0-5)</label>
        <input id="rating" type="number" min="0" max="5" step="0.1" value="4.0" />
      </div>
      <div>
        <label for="preferences">Additional Preferences (comma separated)</label>
        <input id="preferences" value="family-friendly, quick service" />
      </div>
    </div>
    <div style="margin-top: 14px;">
      <button id="submitBtn">Get Recommendations</button>
    </div>
  </div>

  <div id="status" class="muted"></div>
  <div id="results"></div>

  <script>
    const statusEl = document.getElementById("status");
    const resultsEl = document.getElementById("results");
    const submitBtn = document.getElementById("submitBtn");
    const locationEl = document.getElementById("location");

    function splitCsv(raw) {
      return raw.split(",").map(x => x.trim()).filter(Boolean);
    }

    function renderResultCard(item) {
      const cuisines = (item.cuisine || []).join(", ");
      return `
        <div class="card">
          <h3 style="margin:0 0 8px 0;">${item.name}</h3>
          <div class="muted">${item.city}${item.locality ? " - " + item.locality : ""}</div>
          <div style="margin:8px 0;">
            <span class="pill">Rating: ${item.rating ?? "N/A"}</span>
            <span class="pill">Cost for two: ${item.estimated_cost_for_two ?? "N/A"}</span>
          </div>
          <div><strong>Cuisine:</strong> ${cuisines || "N/A"}</div>
          <div style="margin-top:8px;"><strong>Why:</strong> ${item.explanation}</div>
        </div>
      `;
    }

    async function loadCities() {
      locationEl.innerHTML = `<option value="">Loading cities...</option>`;
      try {
        const response = await fetch("/v1/cities");
        if (!response.ok) throw new Error("Failed to load cities");
        const data = await response.json();
        const list = Array.isArray(data.cities) ? data.cities : [];
        locationEl.innerHTML = "";
        list.forEach((name, idx) => {
          const opt = document.createElement("option");
          opt.value = name;
          opt.textContent = name;
          if (idx === 0) opt.selected = true;
          locationEl.appendChild(opt);
        });
        if (!list.length) {
          const opt = document.createElement("option");
          opt.value = "bangalore";
          opt.textContent = "bangalore";
          locationEl.appendChild(opt);
        }
      } catch (_err) {
        locationEl.innerHTML = `<option value="bangalore">bangalore</option>`;
      }
    }

    submitBtn.addEventListener("click", async () => {
      submitBtn.disabled = true;
      statusEl.textContent = "Loading recommendations...";
      statusEl.className = "muted";
      resultsEl.innerHTML = "";

      const payload = {
        location: locationEl.value.trim(),
        budget: Number(document.getElementById("budget").value),
        cuisine: splitCsv(document.getElementById("cuisine").value),
        min_rating: Number(document.getElementById("rating").value),
        additional_preferences: splitCsv(document.getElementById("preferences").value)
      };

      try {
        const response = await fetch("/v1/recommendations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          const errText = await response.text();
          throw new Error(`API ${response.status}: ${errText}`);
        }

        const data = await response.json();
        const fallbackText = data.used_fallback ? "Yes" : "No";
        statusEl.textContent = `Request ${data.request_id} | Fallback: ${fallbackText} | Time: ${data.timing_ms} ms`;

        if (data.summary) {
          resultsEl.innerHTML += `<div class="card"><strong>Summary:</strong> ${data.summary}</div>`;
        }

        if (!data.recommendations || data.recommendations.length === 0) {
          resultsEl.innerHTML += `<div class="card">No recommendations found.</div>`;
        } else {
          data.recommendations.forEach(item => {
            resultsEl.innerHTML += renderResultCard(item);
          });
        }
      } catch (err) {
        statusEl.textContent = "Failed to fetch recommendations.";
        statusEl.className = "error";
        const msg = err && err.message ? err.message : String(err);
        resultsEl.innerHTML = `<div class="card error">${msg}</div>`;
      } finally {
        submitBtn.disabled = false;
      }
    });

    loadCities();
  </script>
</body>
</html>
"""


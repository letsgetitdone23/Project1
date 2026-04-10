"use client";

import { useEffect, useMemo, useState } from "react";

type Recommendation = {
  name: string;
  cuisine?: string[];
  rating?: number;
  estimated_cost_for_two?: number;
  city: string;
  locality?: string | null;
  explanation: string;
};

type ApiResponse = {
  request_id: string;
  used_fallback: boolean;
  timing_ms: number;
  summary?: string | null;
  recommendations: Recommendation[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export default function HomePage() {
  const [cities, setCities] = useState<string[]>([]);
  const [location, setLocation] = useState("");
  const [budget, setBudget] = useState(1200);
  const [cuisine, setCuisine] = useState("Italian, Chinese");
  const [minRating, setMinRating] = useState(4.0);
  const [topK, setTopK] = useState("");
  const [preferences, setPreferences] = useState("family-friendly, quick service");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ApiResponse | null>(null);

  useEffect(() => {
    const loadCities = async () => {
      try {
        const res = await fetch(`${API_BASE}/v1/cities`);
        const data = await res.json();
        const list = Array.isArray(data.cities) ? data.cities : [];
        setCities(list);
        if (list.length > 0) setLocation(list[0]);
      } catch {
        setCities(["bangalore"]);
        setLocation("bangalore");
      }
    };
    loadCities();
  }, []);

  const cuisines = useMemo(
    () => cuisine.split(",").map((v) => v.trim()).filter(Boolean),
    [cuisine]
  );
  const tags = useMemo(
    () => preferences.split(",").map((v) => v.trim()).filter(Boolean),
    [preferences]
  );

  const onSubmit = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const payload = {
        location,
        budget,
        cuisine: cuisines,
        min_rating: minRating,
        additional_preferences: tags,
        ...(topK.trim() ? { top_k: Number(topK) } : {})
      };
      const res = await fetch(`${API_BASE}/v1/recommendations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const data = (await res.json()) as ApiResponse;
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch recommendations");
    } finally {
      setLoading(false);
    }
  };

  const curatedCount = (result?.recommendations ?? []).length;
  const hasResults = curatedCount > 0;

  return (
    <>
      <header className="topbar">
        <div className="container">
          <div className="brand">The Culinary Curator</div>
          <nav className="topbar-nav muted">
            <span className="active-nav">Explore</span>
            <span>AI Picks</span>
            <span>Preferences</span>
          </nav>
          <div className="topbar-controls">
            <select
              className="topbar-select"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            >
              {cities.map((c) => (
                <option key={`top-${c}`} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <input
              className="topbar-search"
              placeholder="Search for restaurant, cuisine or dish"
              value={cuisine}
              onChange={(e) => setCuisine(e.target.value)}
            />
            <span className="muted">User</span>
          </div>
        </div>
      </header>

      <main className="container">
        <section className="hero hero-bg">
          <div className="hero-left">
            <span className="hero-tag">The Future of Dining</span>
            <h1>
              Discover restaurants
              <br />
              <span>you&apos;ll love</span>
            </h1>
            <p>
              Powered by AI recommendations that understand your palate better than
              you do.
            </p>
            <div className="hero-actions">
              <button className="btn btn-primary" onClick={onSubmit} disabled={loading}>
                {loading ? "Loading..." : "Get Recommendations"}
              </button>
              <button className="btn btn-secondary" type="button">
                Explore Nearby
              </button>
            </div>
          </div>
          <div className="hero-right">
            <div className="hero-plate">🥞</div>
          </div>
        </section>

        <section className="panel">
          <div>
            <h2 className="form-title">Curate Your Experience</h2>
            <p className="muted">Tell our AI what your palate is craving today.</p>

            <div className="grid">
              <div>
                <label>Location</label>
                <select value={location} onChange={(e) => setLocation(e.target.value)}>
                  {cities.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label>Budget (cost for two)</label>
                <input
                  type="number"
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                />
              </div>
              <div>
                <label>Minimum Rating</label>
                <select value={minRating} onChange={(e) => setMinRating(Number(e.target.value))}>
                  <option value={4.5}>4.5+ Exceptional</option>
                  <option value={4}>4.0+ Great</option>
                  <option value={3.5}>3.5+ Good</option>
                  <option value={3}>3.0+ Above Average</option>
                </select>
              </div>
              <div>
                <label>Max Recommendations (optional)</label>
                <input
                  type="number"
                  min={1}
                  value={topK}
                  onChange={(e) => setTopK(e.target.value)}
                  placeholder="Leave blank for all matches"
                />
              </div>
              <div>
                <label>Cuisine Preferences</label>
                <input value={cuisine} onChange={(e) => setCuisine(e.target.value)} />
              </div>
              <div className="full chip-row">
                {cuisines.slice(0, 5).map((item) => (
                  <span key={item} className="mini-chip">
                    {item}
                  </span>
                ))}
                <button className="mini-chip ghost-chip" type="button">
                  + Explore More
                </button>
              </div>
              <div className="full">
                <label>What are you in the mood for?</label>
                <textarea
                  value={preferences}
                  onChange={(e) => setPreferences(e.target.value)}
                  placeholder="e.g., A quiet rooftop spot for a date with great cocktails and vegetarian options..."
                />
              </div>
            </div>
          </div>

          <div className="concierge">
            <h3>AI Concierge</h3>
            <p className="muted">
              Budget target: <strong className="light">{budget}</strong>
            </p>
            <div className="budget-line" />
            <button className="btn btn-primary" onClick={onSubmit} disabled={loading}>
              Find My Perfect Meal
            </button>
            {result && (
              <p className="muted" style={{ marginTop: 14 }}>
                Request {result.request_id.slice(0, 8)}... | {result.timing_ms}ms
              </p>
            )}
          </div>
        </section>

        {error && <p style={{ color: "#ef4444", marginTop: 16 }}>{error}</p>}

        {hasResults && <section className="results-shell">
          <aside className="filters">
            <h3>Fine Dining Filters</h3>
            <p className="muted">Refine your palate</p>
            <button className="filter-pill active">Cuisine</button>
            <button className="filter-pill">Price Range</button>
            <button className="filter-pill">Rating</button>
            <button className="btn btn-primary apply-btn" onClick={onSubmit} disabled={loading}>
              Apply Filters
            </button>
          </aside>

          <div className="results-main">
            <div className="results-header">
              <div>
                <span className="eyebrow">Personalized Recommendations</span>
                <h2>Top Picks for You</h2>
              </div>
              <span className="curated-chip">{curatedCount} Curated Venues</span>
            </div>

            {result?.summary && <p className="summary-line">{result.summary}</p>}

            <section className="results-list">
              {(result?.recommendations ?? []).map((r, idx) => (
                <article className="result-card" key={`${r.name}-${idx}`}>
                  <div className="card-top">
                    <h3>{r.name}</h3>
                    <span className="score-chip">⭐ {r.rating ?? "N/A"}</span>
                  </div>
                  <p className="location-row">
                    {r.city}
                    {r.locality ? `, ${r.locality}` : ""}
                  </p>
                  <div className="meta-row">
                    <span className="tag-chip">{(r.cuisine ?? []).join(" • ") || "Cuisine N/A"}</span>
                    <span className="tag-chip">
                      Cost {r.estimated_cost_for_two ?? "N/A"}
                    </span>
                  </div>
                  <div className="why-box">
                    <strong>Why you&apos;ll love it</strong>
                    <p>{r.explanation}</p>
                  </div>
                  <div className="card-actions">
                    <button className="btn btn-ghost" type="button">
                      View Menu
                    </button>
                    <button className="btn btn-primary" type="button">
                      Book a Table
                    </button>
                  </div>
                </article>
              ))}
            </section>
          </div>
        </section>}
      </main>
    </>
  );
}


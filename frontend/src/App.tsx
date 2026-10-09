
import { useEffect, useState } from "react";
import RiskMap from "./components/RiskMap";
import "./App.css";

type RiskLevel = "CRITICAL" | "HIGH" | "MODERATE" | "LOW";

type RiskZone = {
  id: number;
  latitude: number;
  longitude: number;
  rainfall_mm: number;
  water_level_m: number;
  elevation_m: number;
  historical_risk: number;
  risk_score: number;
  risk_level: RiskLevel;
  observed_at: string;
};

type RiskApiResponse = {
  count: number;
  zones: RiskZone[];
  data_note: string;
};

const USER_LOCATION = {
  latitude: 18.525,
  longitude: 73.8567,
};

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [zones, setZones] = useState<RiskZone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadRiskZones() {
      try {
        const response = await fetch(`${API_URL}/api/risk/zones`);

        if (!response.ok) {
          throw new Error(`API returned HTTP ${response.status}`);
        }

        const data: RiskApiResponse = await response.json();
        setZones(data.zones);
        setError("");
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Could not load risk zones."
        );
      } finally {
        setLoading(false);
      }
    }

    loadRiskZones();
  }, []);

  const countByLevel = (level: RiskLevel) =>
    zones.filter((zone) => zone.risk_level === level).length;

  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">AI-POWERED DISASTER RESPONSE</p>
          <h1>ResQNet</h1>
          <p className="subtitle">
            Disaster risk monitoring and emergency preparedness
          </p>
        </div>
        <span className="status-pill">● API connection</span>
      </header>

      <section className="risk-summary">
        {(
          [
            ["CRITICAL", "#dc2626"],
            ["HIGH", "#f97316"],
            ["MODERATE", "#eab308"],
            ["LOW", "#16a34a"],
          ] as [RiskLevel, string][]
        ).map(([level, color]) => (
          <article className="risk-card" key={level}>
            <span className="risk-dot" style={{ background: color }} />
            <div>
              <p>{level}</p>
              <strong>{loading ? "—" : countByLevel(level)}</strong>
              <small>risk zones</small>
            </div>
          </article>
        ))}
      </section>

      {error && (
        <div className="error-message">
          Could not load risk data: {error}
        </div>
      )}

      <section className="map-panel">
        <div className="panel-heading">
          <div>
            <h2>Disaster Risk Map</h2>
            <p>Risk observation locations · Pune demo area</p>
          </div>
          <span className="zone-count">
            {loading ? "Loading…" : `${zones.length} observations`}
          </span>
        </div>

        {loading ? (
          <div className="map-placeholder">Loading risk data…</div>
        ) : zones.length === 0 ? (
          <div className="map-placeholder">
            No risk observations are available.
          </div>
        ) : (
          <RiskMap observations={zones} userLocation={USER_LOCATION} />
        )}
      </section>

      <section className="observations-panel">
        <h2>Risk observations</h2>
        <div className="observation-list">
          {zones.map((zone) => (
            <article className="observation-row" key={zone.id}>
              <span
                className={`level-badge ${zone.risk_level.toLowerCase()}`}
              >
                {zone.risk_level}
              </span>
              <div className="observation-details">
                <strong>Risk score: {zone.risk_score.toFixed(2)}</strong>
                <small>
                  {zone.latitude}, {zone.longitude}
                </small>
                <small>
                  Rainfall {zone.rainfall_mm} mm · Water level{" "}
                  {zone.water_level_m} m
                </small>
              </div>
            </article>
          ))}
        </div>
      </section>

      <footer>
        Prototype risk scores based on seeded observations. Not validated
        flood predictions.
      </footer>
    </main>
  );
}

export default App;

import { useCallback, useEffect, useState } from "react";
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

type Shelter = {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  capacity: number;
  current_occupancy: number;
  available_capacity: number;
  has_medical: boolean;
  has_food: boolean;
  has_water: boolean;
  is_active: boolean;
};

type RiskApiResponse = {
  count: number;
  zones: RiskZone[];
  data_note?: string;
};

type ShelterApiResponse = {
  count: number;
  shelters: Shelter[];
};

const USER_LOCATION = {
  latitude: 18.525,
  longitude: 73.8567,
};

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [zones, setZones] = useState<RiskZone[]>([]);
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [shelterError, setShelterError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async (manualRefresh = false) => {
    if (manualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setError("");
    setShelterError("");

    try {
      const [riskResponse, shelterResponse] = await Promise.all([
        fetch(`${API_URL}/api/risk/zones`),
        fetch(`${API_URL}/api/shelters`),
      ]);

      if (!riskResponse.ok) {
        throw new Error(`Risk API returned HTTP ${riskResponse.status}`);
      }

      if (!shelterResponse.ok) {
        throw new Error(
          `Shelter API returned HTTP ${shelterResponse.status}`
        );
      }

      const riskData: RiskApiResponse = await riskResponse.json();
      const shelterData: ShelterApiResponse =
        await shelterResponse.json();

      setZones(riskData.zones ?? []);
      setShelters(shelterData.shelters ?? []);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load dashboard data."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const countByLevel = (level: RiskLevel) =>
    zones.filter((zone) => zone.risk_level === level).length;

  const availableShelterPlaces = shelters.reduce(
    (total, shelter) => total + shelter.available_capacity,
    0
  );

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

        <div className="header-actions">
          <span className="status-pill">
            {error || shelterError ? "Check connection" : "API connected"}
          </span>
          <button
            className="refresh-button"
            type="button"
            onClick={() => void loadData(true)}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing..." : "Refresh data"}
          </button>
        </div>
      </header>

      {error && (
        <div className="error-message">
          Could not load dashboard data: {error}
        </div>
      )}

      {shelterError && (
        <div className="error-message">
          Could not load shelters: {shelterError}
        </div>
      )}

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

      <section className="risk-summary shelter-summary">
        <article className="risk-card">
          <span className="risk-dot shelter-dot" />
          <div>
            <p>ACTIVE SHELTERS</p>
            <strong>{loading ? "—" : shelters.length}</strong>
            <small>locations</small>
          </div>
        </article>

        <article className="risk-card">
          <span className="risk-dot capacity-dot" />
          <div>
            <p>AVAILABLE PLACES</p>
            <strong>
              {loading ? "—" : availableShelterPlaces.toLocaleString()}
            </strong>
            <small>demo capacity total</small>
          </div>
        </article>
      </section>

      <section className="map-panel">
        <div className="panel-heading">
          <div>
            <h2>Disaster Risk & Shelter Map</h2>
            <p>Risk observations and active shelter locations · Pune demo area</p>
          </div>
          <span className="zone-count">
            {loading
              ? "Loading..."
              : `${zones.length} risk observations · ${shelters.length} shelters`}
          </span>
        </div>

        {loading ? (
          <div className="map-placeholder">Loading map data...</div>
        ) : zones.length === 0 && shelters.length === 0 ? (
          <div className="map-placeholder">
            No risk observations or shelters are available.
          </div>
        ) : (
          <RiskMap
            observations={zones}
            shelters={shelters}
            userLocation={USER_LOCATION}
          />
        )}
      </section>

      <section className="observations-panel">
        <h2>Active shelters</h2>

        {shelters.length === 0 ? (
          <p>No active shelters returned by the API.</p>
        ) : (
          <div className="observation-list">
            {shelters.map((shelter) => (
              <article className="observation-row" key={shelter.id}>
                <span className="shelter-list-icon" aria-hidden="true">
                  ⛑
                </span>

                <div className="observation-details">
                  <strong>{shelter.name}</strong>
                  <small>
                    {shelter.available_capacity} places available of{" "}
                    {shelter.capacity}
                  </small>
                  <small>
                    Occupancy: {shelter.current_occupancy}
                  </small>
                  <small>
                    Medical: {shelter.has_medical ? "Available" : "Unavailable"}
                    {" · "}
                    Food: {shelter.has_food ? "Available" : "Unavailable"}
                    {" · "}
                    Water: {shelter.has_water ? "Available" : "Unavailable"}
                  </small>
                </div>
              </article>
            ))}
          </div>
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
                <strong>Risk score: {zone.risk_score.toFixed(2)}/100</strong>
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
        Prototype risk scores use seeded observations and a rule-based formula.
        They are not validated flood predictions. Shelter data is currently
        seeded demo data.
      </footer>
    </main>
  );
}

export default App;
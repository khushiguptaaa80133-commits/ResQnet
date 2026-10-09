
import {
  Circle,
  CircleMarker,
  MapContainer,
  Marker,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";
import { useEffect } from "react";
import L from "leaflet";
import type { LatLngExpression } from "leaflet";
import "leaflet/dist/leaflet.css";

type RiskLevel = "CRITICAL" | "HIGH" | "MODERATE" | "LOW";

type RiskObservation = {
  id: number;
  latitude: number;
  longitude: number;
  rainfall_mm: number;
  water_level_m: number;
  elevation_m: number;
  historical_risk: number;
  risk_score: number;
  risk_level: RiskLevel;
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

type RiskMapProps = {
  observations: RiskObservation[];
  shelters: Shelter[];
  userLocation: {
    latitude: number;
    longitude: number;
  };
};

const riskColors: Record<RiskLevel, string> = {
  CRITICAL: "#dc2626",
  HIGH: "#f97316",
  MODERATE: "#eab308",
  LOW: "#16a34a",
};

const riskDescriptions: Record<RiskLevel, string> = {
  CRITICAL: "75–100 · Critical risk",
  HIGH: "55–74.99 · High risk",
  MODERATE: "30–54.99 · Moderate risk",
  LOW: "0–29.99 · Low risk",
};

const shelterIcon = L.divIcon({
  className: "resqnet-shelter-icon",
  html: '<div class="shelter-marker-pin">S</div>',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

function MapRefresher({
  position,
}: {
  position: LatLngExpression;
}) {
  const map = useMap();

  useEffect(() => {
    map.setView(position, 14);

    const timer = window.setTimeout(() => {
      map.invalidateSize();
    }, 300);

    return () => window.clearTimeout(timer);
  }, [map, position]);

  return null;
}

function RiskLegend() {
  const levels: RiskLevel[] = [
    "CRITICAL",
    "HIGH",
    "MODERATE",
    "LOW",
  ];

  return (
    <div className="risk-map-legend">
      <strong>Map legend</strong>

      {levels.map((level) => (
        <div className="risk-legend-item" key={level}>
          <span
            className="risk-legend-color"
            style={{ backgroundColor: riskColors[level] }}
          />
          <div>
            <span className="risk-legend-label">{level}</span>
            <small>{riskDescriptions[level]}</small>
          </div>
        </div>
      ))}

      <div className="risk-legend-item">
        <span className="shelter-legend-marker">S</span>
        <div>
          <span className="risk-legend-label">SHELTER</span>
          <small>Click for capacity and facilities</small>
        </div>
      </div>

      <div className="risk-legend-item">
        <span className="user-legend-marker" />
        <div>
          <span className="risk-legend-label">USER</span>
          <small>Configured demo location</small>
        </div>
      </div>

      <p className="risk-legend-note">
        Risk circles are illustrative 250 m zones around demo observations,
        not verified flood boundaries.
      </p>
    </div>
  );
}

export default function RiskMap({
  observations,
  shelters,
  userLocation,
}: RiskMapProps) {
  const center: LatLngExpression = [
    userLocation.latitude,
    userLocation.longitude,
  ];

  return (
    <div className="risk-map-wrapper">
      <MapContainer
        center={center}
        zoom={14}
        className="risk-map"
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          eventHandlers={{
            tileerror: () => {
              console.warn("A map tile failed to load.");
            },
          }}
        />

        <MapRefresher position={center} />

        <CircleMarker
          center={center}
          radius={8}
          pathOptions={{
            color: "#ffffff",
            weight: 3,
            fillColor: "#2563eb",
            fillOpacity: 1,
          }}
        >
          <Tooltip>
            <strong>Demo user location</strong>
            <br />
            Latitude: {userLocation.latitude}
            <br />
            Longitude: {userLocation.longitude}
          </Tooltip>
        </CircleMarker>

        {observations.map((observation) => (
          <Circle
            key={observation.id}
            center={[
              observation.latitude,
              observation.longitude,
            ]}
            radius={250}
            pathOptions={{
              color: riskColors[observation.risk_level],
              fillColor: riskColors[observation.risk_level],
              fillOpacity: 0.3,
              weight: 2,
            }}
          >
            <Tooltip>
              <strong>{observation.risk_level} RISK</strong>
              <br />
              Risk score: {observation.risk_score.toFixed(2)}/100
              <br />
              Rainfall: {observation.rainfall_mm} mm
              <br />
              Water level: {observation.water_level_m} m
              <br />
              Elevation: {observation.elevation_m} m
              <br />
              Historical risk: {observation.historical_risk}
            </Tooltip>
          </Circle>
        ))}

        {shelters.map((shelter) => (
          <Marker
            key={shelter.id}
            position={[shelter.latitude, shelter.longitude]}
            icon={shelterIcon}
          >
            <Tooltip>
              <strong>{shelter.name}</strong>
              <br />
              Available capacity: {shelter.available_capacity}
              <br />
              Occupancy: {shelter.current_occupancy}/{shelter.capacity}
              <br />
              Medical: {shelter.has_medical ? "Available" : "Unavailable"}
              <br />
              Food: {shelter.has_food ? "Available" : "Unavailable"}
              <br />
              Water: {shelter.has_water ? "Available" : "Unavailable"}
            </Tooltip>
          </Marker>
        ))}
      </MapContainer>

      <RiskLegend />
    </div>
  );
}
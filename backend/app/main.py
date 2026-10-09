from fastapi import FastAPI, Query
from sqlalchemy import text

from app.database import engine

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="ResQNet API",
    description="AI-Powered Disaster Management & Emergency Response Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Welcome to ResQNet API",
        "status": "running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "project": "ResQNet"
    }


@app.get("/api/shelters/recommend")
def recommend_shelters(
    latitude: float = Query(...),
    longitude: float = Query(...),
    people: int = Query(1, ge=1)
):
    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    s.id,
                    s.name,
                    s.latitude,
                    s.longitude,
                    s.capacity,
                    s.current_occupancy,

                    (s.capacity - s.current_occupancy)
                        AS available_capacity,

                    s.has_medical,
                    s.has_food,
                    s.has_water,

                    ST_Distance(
                        s.location::geography,
                        ST_SetSRID(
                            ST_MakePoint(:longitude, :latitude),
                            4326
                        )::geography
                    ) AS distance_meters,

                    r.rainfall_mm,
                    r.water_level_m,
                    r.elevation_m,
                    r.historical_risk,

                    ST_Distance(
                        r.location::geography,
                        s.location::geography
                    ) AS risk_observation_distance

                FROM shelters s

                LEFT JOIN LATERAL (
                    SELECT
                        rainfall_mm,
                        water_level_m,
                        elevation_m,
                        historical_risk,
                        location
                    FROM risk_observations r
                    ORDER BY ST_Distance(
                        r.location::geography,
                        s.location::geography
                    )
                    LIMIT 1
                ) r ON TRUE

                WHERE s.is_active = TRUE
                  AND (s.capacity - s.current_occupancy) >= :people

                ORDER BY distance_meters
            """),
            {
                "latitude": latitude,
                "longitude": longitude,
                "people": people
            }
        )

        shelters = result.fetchall()

        if not shelters:
            return {
                "message": "No suitable shelters found for the requested number of people."
            }

        recommendations = []

        for shelter in shelters:

            # -----------------------------------
            # 1. Distance Score - Maximum 40
            # -----------------------------------

            distance_score = max(
                0,
                40 - (shelter.distance_meters / 100)
            )

            # -----------------------------------
            # 2. Capacity Score - Maximum 30
            # -----------------------------------

            capacity_score = min(
                30,
                (shelter.available_capacity / people) * 15
            )

            # -----------------------------------
            # 3. Facility Score - Maximum 30
            # -----------------------------------

            facility_score = 0

            if shelter.has_medical:
                facility_score += 10

            if shelter.has_food:
                facility_score += 10

            if shelter.has_water:
                facility_score += 10

            # Existing shelter suitability score
            suitability_score = (
                distance_score +
                capacity_score +
                facility_score
            )

            suitability_score = min(
                100,
                suitability_score
            )

            # -----------------------------------
            # 4. Disaster Risk Score
            # -----------------------------------

            if shelter.rainfall_mm is not None:

                rainfall_score = min(
                    shelter.rainfall_mm / 100,
                    1
                )

                water_level_score = min(
                    shelter.water_level_m / 5,
                    1
                )

                elevation_score = max(
                    0,
                    min(
                        (600 - shelter.elevation_m) / 200,
                        1
                    )
                )

                historical_score = max(
                    0,
                    min(
                        shelter.historical_risk,
                        1
                    )
                )

                risk_score = (
                    rainfall_score * 0.35 +
                    water_level_score * 0.35 +
                    elevation_score * 0.10 +
                    historical_score * 0.20
                ) * 100

                risk_score = round(
                    risk_score,
                    2
                )

                # Higher risk = lower safety score
                safety_score = 100 - risk_score

                if risk_score < 30:
                    risk_level = "LOW"

                elif risk_score < 55:
                    risk_level = "MODERATE"

                elif risk_score < 75:
                    risk_level = "HIGH"

                else:
                    risk_level = "CRITICAL"

            else:
                risk_score = None
                safety_score = None
                risk_level = "UNKNOWN"

            # -----------------------------------
            # 5. Risk-Adjusted Recommendation
            # -----------------------------------

            if safety_score is not None:

                final_score = (
                    suitability_score * 0.70
                    + safety_score * 0.30
                )

            else:

                final_score = suitability_score

            final_score = round(
                final_score,
                2
            )

            # -----------------------------------
            # Recommendation Reasons
            # -----------------------------------

            reasons = []

            if shelter.has_medical:
                reasons.append("medical support available")

            if shelter.has_food:
                reasons.append("food available")

            if shelter.has_water:
                reasons.append("water available")

            if shelter.available_capacity >= people * 2:
                reasons.append("high available capacity")

            else:
                reasons.append("sufficient capacity")

            if risk_level == "LOW":
                reasons.append("low disaster risk")

            elif risk_level == "MODERATE":
                reasons.append("moderate disaster risk")

            elif risk_level == "HIGH":
                reasons.append("high disaster risk")

            elif risk_level == "CRITICAL":
                reasons.append("critical disaster risk")

            recommendations.append(
                {
                    "id": shelter.id,
                    "name": shelter.name,
                    "latitude": shelter.latitude,
                    "longitude": shelter.longitude,

                    "capacity": shelter.capacity,
                    "current_occupancy": shelter.current_occupancy,
                    "available_capacity": shelter.available_capacity,

                    "has_medical": shelter.has_medical,
                    "has_food": shelter.has_food,
                    "has_water": shelter.has_water,

                    "distance_meters": round(
                        shelter.distance_meters,
                        2
                    ),

                    "suitability_score": round(
                        suitability_score,
                        2
                    ),

                    "risk_score": risk_score,
                    "risk_level": risk_level,

                    "safety_score": (
                        round(safety_score, 2)
                        if safety_score is not None
                        else None
                    ),

                    "final_score": final_score,

                    "reasons": reasons
                }
            )

        # Highest final score = best recommendation
        recommendations.sort(
            key=lambda x: x["final_score"],
            reverse=True
        )

        return {
            "requested_people": people,
            "user_location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "recommendations": recommendations[:5]
        }

@app.get("/api/risk/nearest")
def get_nearest_risk(
    latitude: float = Query(...),
    longitude: float = Query(...)
):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    id,
                    latitude,
                    longitude,
                    rainfall_mm,
                    water_level_m,
                    elevation_m,
                    historical_risk,
                    observed_at,

                    ST_Distance(
                        location::geography,
                        ST_SetSRID(
                            ST_MakePoint(:longitude, :latitude),
                            4326
                        )::geography
                    ) AS distance_meters

                FROM risk_observations

                ORDER BY distance_meters

                LIMIT 1
            """),
            {
                "latitude": latitude,
                "longitude": longitude
            }
        )

        observation = result.fetchone()

        if not observation:
            return {
                "message": "No risk observations found."
            }

        return {
            "id": observation.id,
            "latitude": observation.latitude,
            "longitude": observation.longitude,
            "rainfall_mm": observation.rainfall_mm,
            "water_level_m": observation.water_level_m,
            "elevation_m": observation.elevation_m,
            "historical_risk": observation.historical_risk,
            "observed_at": observation.observed_at,
            "distance_meters": round(
                observation.distance_meters,
                2
            )
        }

@app.get("/api/risk/score")
def calculate_risk_score(
    latitude: float = Query(...),
    longitude: float = Query(...)
):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    id,
                    latitude,
                    longitude,
                    rainfall_mm,
                    water_level_m,
                    elevation_m,
                    historical_risk,
                    observed_at,
                    ST_Distance(
                        location::geography,
                        ST_SetSRID(
                            ST_MakePoint(:longitude, :latitude),
                            4326
                        )::geography
                    ) AS distance_meters
                FROM risk_observations
                ORDER BY distance_meters
                LIMIT 1
            """),
            {
                "latitude": latitude,
                "longitude": longitude
            }
        )

        observation = result.fetchone()

        if not observation:
            return {
                "message": "No risk observations found."
            }

        # -----------------------------------
        # Normalize individual risk factors
        # -----------------------------------

        # Rainfall:
        # 100 mm or more = maximum rainfall risk
        rainfall_score = min(
            observation.rainfall_mm / 100,
            1
        )

        # Water level:
        # 5 meters or more = maximum water-level risk
        water_level_score = min(
            observation.water_level_m / 5,
            1
        )

        # Elevation:
        # Lower elevation = higher flood risk.
        # This is a prototype assumption.
        elevation_score = max(
            0,
            min(
                (600 - observation.elevation_m) / 200,
                1
            )
        )

        # Historical risk is already stored between 0 and 1
        historical_score = max(
            0,
            min(
                observation.historical_risk,
                1
            )
        )

        # -----------------------------------
        # Weighted Risk Score
        # -----------------------------------

        risk_score = (
            rainfall_score * 0.35 +
            water_level_score * 0.35 +
            elevation_score * 0.10 +
            historical_score * 0.20
        ) * 100

        risk_score = round(risk_score, 2)

        # -----------------------------------
        # Risk Classification
        # -----------------------------------

        if risk_score < 30:
            risk_level = "LOW"

        elif risk_score < 55:
            risk_level = "MODERATE"

        elif risk_score < 75:
            risk_level = "HIGH"

        else:
            risk_level = "CRITICAL"

        return {
            "location": {
                "latitude": observation.latitude,
                "longitude": observation.longitude
            },

            "risk_score": risk_score,

            "risk_level": risk_level,

            "factors": {
                "rainfall_mm": observation.rainfall_mm,
                "water_level_m": observation.water_level_m,
                "elevation_m": observation.elevation_m,
                "historical_risk": observation.historical_risk
            },

            "factor_scores": {
                "rainfall_score": round(rainfall_score * 100, 2),
                "water_level_score": round(water_level_score * 100, 2),
                "elevation_score": round(elevation_score * 100, 2),
                "historical_risk_score": round(historical_score * 100, 2)
            },

            "distance_from_observation_meters": round(
                observation.distance_meters,
                2
            ),

            "observed_at": observation.observed_at
        }


@app.get("/api/risk/zones")
def get_risk_zones():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    id,
                    latitude,
                    longitude,
                    rainfall_mm,
                    water_level_m,
                    elevation_m,
                    historical_risk,
                    observed_at
                FROM risk_observations
                ORDER BY id
            """)
        )

        observations = result.fetchall()

    zones = []

    for observation in observations:
        rainfall_score = min(observation.rainfall_mm / 100, 1)
        water_level_score = min(observation.water_level_m / 5, 1)

        elevation_score = max(
            0,
            min((600 - observation.elevation_m) / 200, 1)
        )

        historical_score = max(
            0,
            min(observation.historical_risk, 1)
        )

        risk_score = round(
            (
                rainfall_score * 0.35
                + water_level_score * 0.35
                + elevation_score * 0.10
                + historical_score * 0.20
            ) * 100,
            2
        )

        if risk_score < 30:
            risk_level = "LOW"
        elif risk_score < 55:
            risk_level = "MODERATE"
        elif risk_score < 75:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        zones.append({
            "id": observation.id,
            "latitude": observation.latitude,
            "longitude": observation.longitude,
            "rainfall_mm": observation.rainfall_mm,
            "water_level_m": observation.water_level_m,
            "elevation_m": observation.elevation_m,
            "historical_risk": observation.historical_risk,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "observed_at": observation.observed_at,
        })

    return {
        "count": len(zones),
        "zones": zones,
        "data_note": "Prototype risk scores based on seeded observations and a rule-based formula; not validated flood predictions."
    }
from fastapi import FastAPI, Query
from sqlalchemy import text

from app.database import engine


app = FastAPI(
    title="ResQNet API",
    description="AI-Powered Disaster Management & Emergency Response Platform",
    version="1.0.0"
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
                    id,
                    name,
                    latitude,
                    longitude,
                    capacity,
                    current_occupancy,
                    (capacity - current_occupancy) AS available_capacity,
                    has_medical,
                    has_food,
                    has_water,

                    ST_Distance(
                        location::geography,
                        ST_SetSRID(
                            ST_MakePoint(:longitude, :latitude),
                            4326
                        )::geography
                    ) AS distance_meters,

                    -- Distance score: maximum 40 points
                    GREATEST(
                        0,
                        40 - (
                            ST_Distance(
                                location::geography,
                                ST_SetSRID(
                                    ST_MakePoint(:longitude, :latitude),
                                    4326
                                )::geography
                            ) / 100
                        )
                    ) AS distance_score,

                    -- Capacity score: maximum 30 points
                    LEAST(
                        30,
                        (
                            (capacity - current_occupancy)::float
                            / :people
                        ) * 15
                    ) AS capacity_score,

                    -- Facility score: maximum 30 points
                    (
                        CASE WHEN has_medical THEN 10 ELSE 0 END +
                        CASE WHEN has_food THEN 10 ELSE 0 END +
                        CASE WHEN has_water THEN 10 ELSE 0 END
                    ) AS facility_score

                FROM shelters

                WHERE is_active = TRUE
                  AND (capacity - current_occupancy) >= :people

                ORDER BY
                    (
                        GREATEST(
                            0,
                            40 - (
                                ST_Distance(
                                    location::geography,
                                    ST_SetSRID(
                                        ST_MakePoint(:longitude, :latitude),
                                        4326
                                    )::geography
                                ) / 100
                            )
                        )
                        +
                        LEAST(
                            30,
                            (
                                (capacity - current_occupancy)::float
                                / :people
                            ) * 15
                        )
                        +
                        CASE WHEN has_medical THEN 10 ELSE 0 END
                        +
                        CASE WHEN has_food THEN 10 ELSE 0 END
                        +
                        CASE WHEN has_water THEN 10 ELSE 0 END
                    ) DESC

                LIMIT 5
            """),
            {
                "latitude": latitude,
                "longitude": longitude,
                "people": people
            }
        )

        shelters = result.fetchall()

        recommendations = []

        for shelter in shelters:

            suitability_score = (
                shelter.distance_score
                + shelter.capacity_score
                + shelter.facility_score
            )

            reasons = []

            if shelter.has_medical:
                reasons.append("medical support")

            if shelter.has_food:
                reasons.append("food available")

            if shelter.has_water:
                reasons.append("water available")

            if shelter.available_capacity >= people * 2:
                reasons.append("high available capacity")
            else:
                reasons.append("sufficient capacity")

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
                    "reason": ", ".join(reasons)
                }
            )

        return {
            "requested_people": people,
            "recommendations": recommendations
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
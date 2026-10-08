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
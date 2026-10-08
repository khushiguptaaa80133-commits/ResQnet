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
                    ) AS distance_meters

                FROM shelters

                WHERE is_active = TRUE
                  AND (capacity - current_occupancy) >= :people

                ORDER BY
                    (
                        ST_Distance(
                            location::geography,
                            ST_SetSRID(
                                ST_MakePoint(:longitude, :latitude),
                                4326
                            )::geography
                        )
                        - CASE WHEN has_medical THEN 300 ELSE 0 END
                        - CASE WHEN has_water THEN 150 ELSE 0 END
                        - CASE WHEN has_food THEN 150 ELSE 0 END
                    )

                LIMIT 5
            """),
            {
                "latitude": latitude,
                "longitude": longitude,
                "people": people
            }
        )

        shelters = result.fetchall()

        return {
            "requested_people": people,
            "recommendations": [
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
                    "distance_meters": round(shelter.distance_meters, 2)
                }
                for shelter in shelters
            ]
        }
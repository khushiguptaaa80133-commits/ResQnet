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


@app.get("/api/shelters/nearest")
def get_nearest_shelter(
    latitude: float = Query(...),
    longitude: float = Query(...)
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
                ORDER BY distance_meters
                LIMIT 1
            """),
            {
                "latitude": latitude,
                "longitude": longitude
            }
        )

        shelter = result.fetchone()

        if not shelter:
            return {
                "message": "No active shelters found."
            }

        return {
            "id": shelter.id,
            "name": shelter.name,
            "latitude": shelter.latitude,
            "longitude": shelter.longitude,
            "capacity": shelter.capacity,
            "current_occupancy": shelter.current_occupancy,
            "has_medical": shelter.has_medical,
            "has_food": shelter.has_food,
            "has_water": shelter.has_water,
            "distance_meters": round(shelter.distance_meters, 2)
        }
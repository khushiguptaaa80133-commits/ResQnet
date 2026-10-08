from sqlalchemy import text

from app.database import engine


with engine.begin() as connection:
    connection.execute(
        text("""
            INSERT INTO shelters (
                name,
                latitude,
                longitude,
                location,
                capacity,
                current_occupancy,
                has_medical,
                has_food,
                has_water,
                is_active
            )
            VALUES (
                :name,
                :latitude,
                :longitude,
                ST_SetSRID(
                    ST_MakePoint(:longitude, :latitude),
                    4326
                ),
                :capacity,
                :current_occupancy,
                :has_medical,
                :has_food,
                :has_water,
                :is_active
            )
        """),
        {
            "name": "ResQNet Demo Shelter",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "capacity": 500,
            "current_occupancy": 120,
            "has_medical": True,
            "has_food": True,
            "has_water": True,
            "is_active": True,
        }
    )

print("Sample shelter added successfully!")
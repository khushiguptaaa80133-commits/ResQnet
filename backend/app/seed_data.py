from sqlalchemy import text

from app.database import engine

from datetime import datetime

shelters = [
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
    },
    {
        "name": "ResQNet Shelter A",
        "latitude": 18.5265,
        "longitude": 73.8515,
        "capacity": 300,
        "current_occupancy": 100,
        "has_medical": False,
        "has_food": False,
        "has_water": True,
        "is_active": True,
    },
    {
        "name": "ResQNet Shelter B",
        "latitude": 18.5290,
        "longitude": 73.8600,
        "capacity": 600,
        "current_occupancy": 150,
        "has_medical": True,
        "has_food": True,
        "has_water": True,
        "is_active": True,
    },
    {
        "name": "ResQNet Shelter C",
        "latitude": 18.5150,
        "longitude": 73.8650,
        "capacity": 400,
        "current_occupancy": 100,
        "has_medical": False,
        "has_food": True,
        "has_water": False,
        "is_active": True,
    },
]


with engine.begin() as connection:
    for shelter in shelters:

        existing = connection.execute(
            text("""
                SELECT id
                FROM shelters
                WHERE name = :name
            """),
            {"name": shelter["name"]}
        ).fetchone()

        if existing:
            print(f"Already exists: {shelter['name']}")
            continue

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
            shelter
        )

        print(f"Added: {shelter['name']}")


print("Shelter seed process completed!")    

with engine.begin() as connection:

    existing = connection.execute(
        text("""
            SELECT id
            FROM risk_observations
            WHERE latitude = :latitude
              AND longitude = :longitude
        """),
        {
            "latitude": 18.5250,
            "longitude": 73.8567,
        }
    ).fetchone()

    if existing:
        print("Demo risk observation already exists.")
    else:
        connection.execute(
            text("""
                INSERT INTO risk_observations (
                    latitude,
                    longitude,
                    location,
                    rainfall_mm,
                    water_level_m,
                    elevation_m,
                    historical_risk,
                    observed_at
                )
                VALUES (
                    :latitude,
                    :longitude,
                    ST_SetSRID(
                        ST_MakePoint(:longitude, :latitude),
                        4326
                    ),
                    :rainfall_mm,
                    :water_level_m,
                    :elevation_m,
                    :historical_risk,
                    :observed_at
                )
            """),
            {
                "latitude": 18.5250,
                "longitude": 73.8567,
                "rainfall_mm": 85.0,
                "water_level_m": 4.2,
                "elevation_m": 560.0,
                "historical_risk": 0.65,
                "observed_at": datetime.now(),
            }
        )

        print("Demo risk observation added successfully!")
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

risk_observations = [
    {
        "latitude": 18.5250,
        "longitude": 73.8567,
        "rainfall_mm": 85.0,
        "water_level_m": 4.2,
        "elevation_m": 560.0,
        "historical_risk": 0.65,
    },
    {
        "latitude": 18.5270,
        "longitude": 73.8520,
        "rainfall_mm": 40.0,
        "water_level_m": 2.0,
        "elevation_m": 575.0,
        "historical_risk": 0.25,
    },
    {
        "latitude": 18.5300,
        "longitude": 73.8610,
        "rainfall_mm": 120.0,
        "water_level_m": 5.5,
        "elevation_m": 545.0,
        "historical_risk": 0.85,
    },
    {
        "latitude": 18.5140,
        "longitude": 73.8660,
        "rainfall_mm": 65.0,
        "water_level_m": 3.0,
        "elevation_m": 565.0,
        "historical_risk": 0.45,
    },
]


with engine.begin() as connection:

    for observation in risk_observations:

        existing = connection.execute(
            text("""
                SELECT id
                FROM risk_observations
                WHERE latitude = :latitude
                  AND longitude = :longitude
            """),
            {
                "latitude": observation["latitude"],
                "longitude": observation["longitude"],
            }
        ).fetchone()

        if existing:
            print(
                f"Risk observation already exists: "
                f"{observation['latitude']}, "
                f"{observation['longitude']}"
            )
            continue

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
                "latitude": observation["latitude"],
                "longitude": observation["longitude"],
                "rainfall_mm": observation["rainfall_mm"],
                "water_level_m": observation["water_level_m"],
                "elevation_m": observation["elevation_m"],
                "historical_risk": observation["historical_risk"],
                "observed_at": datetime.now(),
            }
        )

        print(
            f"Added risk observation: "
            f"{observation['latitude']}, "
            f"{observation['longitude']}"
        )


print("Risk observation seed process completed!")
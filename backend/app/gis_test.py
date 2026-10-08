from sqlalchemy import text

from app.database import engine


# Demo citizen location
citizen_latitude = 18.5250
citizen_longitude = 73.8567


with engine.connect() as connection:
    result = connection.execute(
        text("""
            SELECT
                name,
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
            "latitude": citizen_latitude,
            "longitude": citizen_longitude,
        }
    )

    shelter = result.fetchone()

    if shelter:
        print("Nearest shelter:", shelter[0])
        print("Distance:", round(shelter[1], 2), "meters")
    else:
        print("No active shelters found.")
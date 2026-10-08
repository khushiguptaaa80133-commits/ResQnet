from sqlalchemy import text

from app.database import engine


try:
    with engine.connect() as connection:

        # Test PostgreSQL
        result = connection.execute(text("SELECT version();"))
        print("PostgreSQL connection successful!")
        print(result.fetchone())

        # Test PostGIS
        result = connection.execute(text("SELECT PostGIS_Version();"))
        print("PostGIS connection successful!")
        print("PostGIS version:", result.fetchone()[0])

except Exception as e:
    print("Database connection failed!")
    print(e)
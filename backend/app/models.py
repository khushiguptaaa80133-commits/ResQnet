from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from geoalchemy2 import Geometry


class Base(DeclarativeBase):
    pass


class Shelter(Base):
    __tablename__ = "shelters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    location = mapped_column(
        Geometry(
            geometry_type="POINT",
            srid=4326,
            spatial_index=True
        ),
        nullable=False
    )

    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    current_occupancy: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    has_medical: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    has_food: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    has_water: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

from datetime import datetime

from sqlalchemy import DateTime


class RiskObservation(Base):
    __tablename__ = "risk_observations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    location = mapped_column(
        Geometry(
            geometry_type="POINT",
            srid=4326,
            spatial_index=True
        ),
        nullable=False
    )

    rainfall_mm: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    water_level_m: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    elevation_m: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    historical_risk: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )
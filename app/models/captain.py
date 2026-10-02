from sqlalchemy import (
    Column,
    Integer,
    String,
    DECIMAL,
    DateTime,
    ForeignKey,
    func,
)

from app.core.database import Base


class Captain(Base):
    __tablename__ = "captains"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )

    experience_years = Column(Integer, default=0)

    kyc_status = Column(
        String(20),
        default="PENDING",
        nullable=False,
    )

    availability_status = Column(
        String(20),
        default="OFFLINE",
        nullable=False,
    )

    current_latitude = Column(DECIMAL(10, 8), nullable=True)
    current_longitude = Column(DECIMAL(11, 8), nullable=True)

    rating = Column(DECIMAL(3, 2), default=0.00)

    total_jobs = Column(Integer, default=0)

    completed_jobs = Column(Integer, default=0)

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
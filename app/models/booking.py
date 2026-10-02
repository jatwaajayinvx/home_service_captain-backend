from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    Time,
    DECIMAL,
    DateTime,
    ForeignKey,
    func,
)

from app.core.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    booking_number = Column(
        String(30),
        nullable=False,
        unique=True,
    )

    customer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    captain_id = Column(
        Integer,
        ForeignKey("captains.id"),
        nullable=True,
    )

    service_id = Column(
        Integer,
        ForeignKey("services.id"),
        nullable=False,
    )

    address_id = Column(
        Integer,
        ForeignKey("user_addresses.id"),
        nullable=False,
    )

    problem_description = Column(
        Text,
        nullable=True,
    )

    problem_image = Column(
        String(500),
        nullable=True,
    )

    scheduled_date = Column(
        Date,
        nullable=True,
    )

    scheduled_time = Column(
        Time,
        nullable=True,
    )

    estimated_amount = Column(
        DECIMAL(10, 2),
        nullable=False,
        default=0.00,
    )

    final_amount = Column(
        DECIMAL(10, 2),
        nullable=True,
    )

    status = Column(
        String(30),
        nullable=False,
        default="PENDING",
    )

    cancellation_reason = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
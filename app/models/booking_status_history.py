from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    func,
)

from app.core.database import Base


class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    booking_id = Column(
        BigInteger,
        ForeignKey("bookings.id"),
        nullable=False,
    )

    old_status = Column(
        String(50),
        nullable=True,
    )

    new_status = Column(
        String(50),
        nullable=False,
    )

    changed_by = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )

    remarks = Column(
        String(500),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )
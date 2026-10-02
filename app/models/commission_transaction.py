from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    DECIMAL,
    ForeignKey,
    func,
)

from app.core.database import Base


class CommissionTransaction(Base):
    __tablename__ = "commission_transactions"

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

    captain_id = Column(
        BigInteger,
        ForeignKey("captains.id"),
        nullable=False,
    )

    booking_amount = Column(
        DECIMAL(10, 2),
        nullable=False,
    )

    commission_percent = Column(
        DECIMAL(5, 2),
        nullable=False,
    )

    commission_amount = Column(
        DECIMAL(10, 2),
        nullable=False,
    )

    captain_amount = Column(
        DECIMAL(10, 2),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )
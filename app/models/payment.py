from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    DECIMAL,
    Enum,
    ForeignKey,
    String,
    func,
)

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    booking_id = Column(
        BigInteger,
        ForeignKey("bookings.id"),
        nullable=False,
        unique=True,
    )

    amount = Column(
        DECIMAL(10, 2),
        nullable=False,
    )

    payment_method = Column(
        Enum("CASH", "UPI", "CARD", "ONLINE"),
        nullable=False,
    )

    payment_status = Column(
        Enum(
            "PENDING",
            "SUCCESS",
            "FAILED",
            "REFUNDED",
        ),
        nullable=True,
        default="PENDING",
    )

    transaction_id = Column(
        String(150),
        nullable=True,
    )

    paid_at = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )
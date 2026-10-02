from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    DECIMAL,
    ForeignKey,
    String,
    func,
)

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(BigInteger, primary_key=True, index=True)

    booking_id = Column(
        BigInteger,
        ForeignKey("bookings.id"),
        nullable=False,
        unique=True,
    )

    customer_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    captain_id = Column(
        BigInteger,
        ForeignKey("captains.id"),
        nullable=False,
    )

    rating = Column(
        DECIMAL(2, 1),
        nullable=False,
    )

    review_text = Column(
        String(1000),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )
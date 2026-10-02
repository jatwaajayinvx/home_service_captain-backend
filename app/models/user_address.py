from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    BigInteger,
    String,
    DECIMAL,
    ForeignKey,
    func,
)

from app.core.database import Base


class UserAddress(Base):
    __tablename__ = "user_addresses"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    address_line = Column(String(500), nullable=False)
    landmark = Column(String(200), nullable=True)

    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)

    latitude = Column(DECIMAL(10, 7), nullable=True)
    longitude = Column(DECIMAL(10, 7), nullable=True)

    address_type = Column(
        Enum("HOME", "OFFICE", "OTHER"),
        nullable=True,
        default="HOME",
    )

    is_default = Column(Boolean, default=False)

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )
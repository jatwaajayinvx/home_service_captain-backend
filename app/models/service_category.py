from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, func

from app.core.database import Base


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(100),
        nullable=False,
        unique=True,
    )

    description = Column(
        String(500),
        nullable=True,
    )

    image_url = Column(
        String(500),
        nullable=True,
    )

    is_active = Column(
        Boolean,
        nullable=True,
        default=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )
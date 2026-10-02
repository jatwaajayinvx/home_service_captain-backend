from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    DECIMAL,
    ForeignKey,
    func,
)

from app.core.database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)

    category_id = Column(
        Integer,
        ForeignKey("service_categories.id"),
        nullable=False,
    )

    name = Column(
        String(150),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    base_price = Column(
        DECIMAL(10, 2),
        nullable=True,
        default=0.00,
    )

    estimated_minutes = Column(
        Integer,
        nullable=True,
        default=60,
    )

    is_active = Column(
        Boolean,
        default=True,
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
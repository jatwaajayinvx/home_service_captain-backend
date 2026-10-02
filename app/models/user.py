from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    func,
)

from app.core.database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(100),
        nullable=False,
    )

    mobile = Column(
        String(15),
        nullable=False,
        unique=True,
        index=True,
    )

    email = Column(
        String(150),
        nullable=True,
    )

    password_hash = Column(
        String(255),
        nullable=True,
    )

    role = Column(
        Enum(
            "CUSTOMER",
            "CAPTAIN",
            "ADMIN",
        ),
        nullable=False,
        default="CUSTOMER",
    )

    profile_image = Column(
        String(500),
        nullable=True,
    )

    is_active = Column(
        Boolean,
        default=True,
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
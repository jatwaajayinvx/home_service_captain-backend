from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint

from app.core.database import Base


class CaptainService(Base):
    __tablename__ = "captain_services"

    id = Column(Integer, primary_key=True, index=True)

    captain_id = Column(
        Integer,
        ForeignKey("captains.id"),
        nullable=False,
    )

    service_id = Column(
        Integer,
        ForeignKey("services.id"),
        nullable=False,
    )

    experience_years = Column(
        Integer,
        default=0,
    )

    __table_args__ = (
        UniqueConstraint(
            "captain_id",
            "service_id",
            name="uq_captain_service",
        ),
    )
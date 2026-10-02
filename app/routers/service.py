from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.service import Service

router = APIRouter(
    prefix="/api/services",
    tags=["Services"],
)


@router.get("/category/{category_id}")
def get_services_by_category(
    category_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    services = (
        db.query(Service)
        .filter(
            Service.category_id == category_id,
            Service.is_active == True,
        )
        .order_by(Service.id.asc())
        .all()
    )

    return [
        {
            "id": service.id,
            "category_id": service.category_id,
            "name": service.name,
            "description": service.description,
            "base_price": float(service.base_price or 0),
            "estimated_minutes": service.estimated_minutes,
        }
        for service in services
    ]
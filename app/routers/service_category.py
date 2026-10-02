from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.service_category import ServiceCategory

router = APIRouter(
    prefix="/api/service-categories",
    tags=["Service Categories"],
)


@router.get("")
def get_service_categories(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    categories = (
        db.query(ServiceCategory)
        .filter(ServiceCategory.is_active == True)
        .order_by(ServiceCategory.id.asc())
        .all()
    )

    return [
        {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "image_url": category.image_url,
        }
        for category in categories
    ]
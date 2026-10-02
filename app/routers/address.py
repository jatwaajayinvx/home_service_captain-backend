from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.user_address import UserAddress
from app.schemas.address import (
    AddressCreateRequest,
    AddressResponse,
)


router = APIRouter(
    prefix="/api/addresses",
    tags=["Addresses"],
)


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_address(
    request: AddressCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = UserAddress(
        user_id=current_user.id,
        address_line=request.address_line,
        landmark=request.landmark,
        city=request.city,
        state=request.state,
        pincode=request.pincode,
        latitude=request.latitude,
        longitude=request.longitude,
        address_type=request.address_type,
        is_default=request.is_default,
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    return address


@router.get(
    "",
    response_model=list[AddressResponse],
)
def get_my_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(UserAddress)
        .filter(UserAddress.user_id == current_user.id)
        .order_by(UserAddress.id.desc())
        .all()
    )


@router.get(
    "/{address_id}",
    response_model=AddressResponse,
)
def get_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = (
        db.query(UserAddress)
        .filter(
            UserAddress.id == address_id,
            UserAddress.user_id == current_user.id,
        )
        .first()
    )

    if not address:
        raise HTTPException(
            status_code=404,
            detail="Address not found",
        )

    return address
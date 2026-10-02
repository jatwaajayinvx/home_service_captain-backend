import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user

from app.models.booking import Booking
from app.models.booking_status_history import BookingStatusHistory
from app.models.captain import Captain
from app.models.captain_service import CaptainService
from app.models.notification import Notification
from app.models.service import Service
from app.models.user import User
from app.models.user_address import UserAddress

from app.routers import address
from app.schemas.booking import (
    BookingAcceptResponse,
    BookingCreateRequest,
    BookingResponse,
    BookingStatusHistoryResponse,
    BookingStatusRequest,
)

router = APIRouter(
    prefix="/api/bookings",
    tags=["Bookings"],
)


@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_booking(
    request: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = (
        db.query(Service)
        .filter(
            Service.id == request.service_id,
            Service.is_active == True,
        )
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    address = (
        db.query(UserAddress)
        .filter(
            UserAddress.id == request.address_id,
            UserAddress.user_id == current_user.id,
        )
        .first()
    )

    if not address:
        raise HTTPException(
            status_code=404,
            detail="Address not found",
        )

    booking = Booking(
        booking_number=f"HSC-{uuid.uuid4().hex[:10].upper()}",
        customer_id=current_user.id,
        service_id=service.id,
        address_id=address.id,
        problem_description=request.problem_description,
        problem_image=request.problem_image,
        scheduled_date=request.scheduled_date,
        scheduled_time=request.scheduled_time,
        estimated_amount=service.base_price,
        status="SEARCHING",
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return booking


@router.get(
    "/my",
    response_model=list[BookingResponse],
)
def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return (
        db.query(Booking)
        .filter(
            Booking.customer_id == current_user.id
        )
        .order_by(Booking.id.desc())
        .all()
    )
    
@router.post(
    "/{booking_id}/accept",
    response_model=BookingAcceptResponse,
)
def accept_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Check Captain eligibility
    captain = (
        db.query(Captain)
        .filter(
            Captain.user_id == current_user.id,
            Captain.availability_status == "ONLINE",
            Captain.kyc_status == "VERIFIED",
        )
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=403,
            detail="You are not an eligible Captain",
        )

    # 2. Check service mapping first
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    captain_service = (
        db.query(CaptainService)
        .filter(
            CaptainService.captain_id == captain.id,
            CaptainService.service_id == booking.service_id,
        )
        .first()
    )

    if not captain_service:
        raise HTTPException(
            status_code=403,
            detail="Captain is not registered for this service",
        )

    # 3. Lock this booking row
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.status == "SEARCHING",
            Booking.captain_id.is_(None),
        )
        .with_for_update()
        .first()
    )

    # 4. If another Captain already accepted it
    if not booking:
        raise HTTPException(
            status_code=400,
            detail="Booking is no longer available",
        )

    # 5. Assign Captain
    booking.captain_id = captain.id
    booking.status = "ACCEPTED"

    # 6. Captain becomes busy
    captain.availability_status = "BUSY"
    
    # 7. Notify customer
    notification = Notification(
    user_id=booking.customer_id,
    booking_id=booking.id,
    title="Captain Assigned",
    message=f"Captain {current_user.name} has accepted your booking.",
    notification_type="BOOKING_ACCEPTED",
    is_read=False,
    )

    db.add(notification)

    db.commit()
    db.refresh(booking)

    return booking

@router.put(
    "/{booking_id}/status",
    response_model=BookingResponse,
)
def update_booking_status(
    booking_id: int,
    request: BookingStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Find Captain
    captain = (
        db.query(Captain)
        .filter(
            Captain.user_id == current_user.id
        )
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=403,
            detail="Captain profile not found",
        )

    # 2. Lock the assigned booking row
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.captain_id == captain.id,
        )
        .with_for_update()
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    # 2.5. Get booking address
    booking_address = (
        db.query(UserAddress)
        .filter(
            UserAddress.id == booking.address_id
        )
        .first()
    )

    if not booking_address:
        raise HTTPException(
            status_code=404,
            detail="Booking address not found",
        )

    # 3. Allowed status transitions
    allowed_transitions = {
        "ACCEPTED": ["ON_THE_WAY"],
        "ON_THE_WAY": ["ARRIVED"],
        "ARRIVED": ["STARTED"],
        "STARTED": ["COMPLETED"],
    }

    current_status = booking.status
    new_status = request.status.upper().strip()

    # 4. Validate transition
    if new_status not in allowed_transitions.get(
        current_status,
        [],
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid status transition: "
                f"{current_status} -> {new_status}"
            ),
        )

    # 5. Update booking status
    booking.status = new_status

    # 6. Create status history
    history = BookingStatusHistory(
        booking_id=booking.id,
        old_status=current_status,
        new_status=new_status,
        changed_by=current_user.id,
    )

    db.add(history)

    # 7. Customer notification
    notification_messages = {
        "ON_THE_WAY": (
            "Captain On The Way",
            "Your Captain is on the way to your location.",
        ),
        "ARRIVED": (
            "Captain Arrived",
            "Your Captain has arrived at the service location.",
        ),
        "STARTED": (
            "Service Started",
            "Your service has now started.",
        ),
        "COMPLETED": (
            "Service Completed",
            "Your service has been completed successfully.",
        ),
    }

    if new_status in notification_messages:
        title, message = notification_messages[new_status]

        notification = Notification(
            user_id=booking.customer_id,
            booking_id=booking.id,
            title=title,
            message=message,
            notification_type=f"BOOKING_{new_status}",
            is_read=False,
        )

        db.add(notification)

    # 8. Keep Captain availability synchronized
    if new_status == "COMPLETED":
        captain.availability_status = "ONLINE"
        captain.total_jobs += 1
        captain.completed_jobs += 1

    # 9. Find nearby eligible Captains
    nearby_captains_query = text("""
        SELECT DISTINCT c.id, c.user_id
        FROM captains c
        JOIN captain_services cs
            ON cs.captain_id = c.id
        JOIN users u
            ON u.id = c.user_id
        WHERE
            cs.service_id = :service_id
            AND c.availability_status = 'ONLINE'
            AND c.kyc_status = 'VERIFIED'
            AND u.is_active = 1
            AND c.current_latitude IS NOT NULL
            AND c.current_longitude IS NOT NULL
            AND :latitude IS NOT NULL
            AND :longitude IS NOT NULL
            AND (
                6371 * ACOS(
                    COS(RADIANS(:latitude))
                    * COS(RADIANS(c.current_latitude))
                    * COS(
                        RADIANS(c.current_longitude)
                        - RADIANS(:longitude)
                    )
                    + SIN(RADIANS(:latitude))
                    * SIN(RADIANS(c.current_latitude))
                )
            ) <= 20
    """)

    nearby_captains = db.execute(
        nearby_captains_query,
        {
            "service_id": booking.service_id,
            "latitude": booking_address.latitude,
            "longitude": booking_address.longitude,
        },
    ).fetchall()

    # 10. Notify nearby Captains
    for captain_row in nearby_captains:
        # Don't notify the Captain who currently owns this booking
        if captain_row.id == captain.id:
            continue

        notification = Notification(
            user_id=captain_row.user_id,
            booking_id=booking.id,
            title="New Job Available",
            message="A new service booking is available near you.",
            notification_type="NEW_JOB",
            is_read=False,
        )

        db.add(notification)

    # 11. Save everything in one transaction
    db.commit()

    # 12. Refresh booking
    db.refresh(booking)

    return booking
@router.get(
    "/{booking_id}/history",
    response_model=list[BookingStatusHistoryResponse],
)
def get_booking_history(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    is_customer = (
        booking.customer_id == current_user.id
    )

    captain = (
        db.query(Captain)
        .filter(
            Captain.user_id == current_user.id
        )
        .first()
    )

    is_captain = (
        captain is not None
        and booking.captain_id == captain.id
    )

    if not is_customer and not is_captain:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to view this booking",
        )

    return (
        db.query(BookingStatusHistory)
        .filter(
            BookingStatusHistory.booking_id == booking_id
        )
        .order_by(
            BookingStatusHistory.id.asc()
        )
        .all()
    )
    
@router.get(
    "/captain/my",
    response_model=list[BookingResponse],
)
def get_captain_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(
            Captain.user_id == current_user.id
        )
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=403,
            detail="Captain profile not found",
        )

    return (
        db.query(Booking)
        .filter(
            Booking.captain_id == captain.id
        )
        .order_by(
            Booking.id.desc()
        )
        .all()
    )
    
@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.customer_id == current_user.id,
        )
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    response = BookingResponse.model_validate(booking)

    if booking.captain_id:
        captain = (
            db.query(Captain)
            .filter(Captain.id == booking.captain_id)
            .first()
        )

        if captain:
            captain_user = (
                db.query(User)
                .filter(User.id == captain.user_id)
                .first()
            )

            response.captain_name = (
                captain_user.name if captain_user else None
            )

            response.captain_mobile = (
                captain_user.mobile if captain_user else None
            )

            response.captain_rating = float(
                captain.rating or 0
            )

            response.captain_experience = (
                captain.experience_years
            )

    return response

@router.get("", response_model=list[BookingResponse])
def get_my_bookings(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bookings = (
        db.query(Booking)
        .filter(Booking.customer_id == current_user.id)
        .order_by(Booking.id.desc())
        .all()
    )

    responses = []

    for booking in bookings:
        response = BookingResponse.model_validate(booking)

        if booking.captain_id:
            captain = (
                db.query(Captain)
                .filter(Captain.id == booking.captain_id)
                .first()
            )

            if captain:
                captain_user = (
                    db.query(User)
                    .filter(User.id == captain.user_id)
                    .first()
                )

                response.captain_name = (
                    captain_user.name
                    if captain_user
                    else None
                )

                response.captain_mobile = (
                    captain_user.mobile
                    if captain_user
                    else None
                )

                response.captain_rating = float(
                    captain.rating or 0
                )

                response.captain_experience = (
                    captain.experience_years
                )

        responses.append(response)

    return responses
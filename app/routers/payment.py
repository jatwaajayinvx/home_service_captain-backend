from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.booking import Booking
from app.models.captain import Captain
from app.models.commission_transaction import CommissionTransaction
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentResponse,
)

router = APIRouter(
    prefix="/api/payments",
    tags=["Payments"],
)


COMMISSION_PERCENT = 20.0


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    request: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Find customer's booking
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == request.booking_id,
            Booking.customer_id == current_user.id,
        )
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    # 2. Booking must be completed
    if booking.status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Payment is allowed only for completed bookings",
        )

    # 3. Captain must be assigned
    if not booking.captain_id:
        raise HTTPException(
            status_code=400,
            detail="Booking has no assigned Captain",
        )

    # 4. Check duplicate payment
    existing_payment = (
        db.query(Payment)
        .filter(Payment.booking_id == booking.id)
        .first()
    )

    if existing_payment:
        raise HTTPException(
            status_code=400,
            detail="Payment already exists for this booking",
        )

    # 5. Validate payment method
    allowed_methods = {
        "CASH",
        "UPI",
        "CARD",
        "ONLINE",
    }

    if request.payment_method not in allowed_methods:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment method",
        )

    # 6. Determine amount
    amount = booking.final_amount

    if amount is None:
        amount = booking.estimated_amount

    if amount is None or float(amount) <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid booking amount",
        )

    # 7. Calculate commission
    commission_amount = (
        float(amount) * COMMISSION_PERCENT / 100
    )

    captain_amount = (
        float(amount) - commission_amount
    )

    # 8. Create payment
    payment = Payment(
        booking_id=booking.id,
        amount=amount,
        payment_method=request.payment_method,
        payment_status="SUCCESS",
        transaction_id=None,
        paid_at=datetime.now(),
    )

    db.add(payment)

    # 9. Create commission transaction
    commission = CommissionTransaction(
        booking_id=booking.id,
        captain_id=booking.captain_id,
        booking_amount=amount,
        commission_percent=COMMISSION_PERCENT,
        commission_amount=commission_amount,
        captain_amount=captain_amount,
    )

    db.add(commission)

    # 10. Save both together
    db.commit()

    db.refresh(payment)

    return payment
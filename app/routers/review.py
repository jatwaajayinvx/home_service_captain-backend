from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user

from app.models.booking import Booking
from app.models.captain import Captain
from app.models.review import Review

from app.schemas.review import (
    CaptainRatingSummary,
    CaptainReviewResponse,
    ReviewCreateRequest,
    ReviewResponse,
)


router = APIRouter(
    prefix="/api/reviews",
    tags=["Reviews"],
)


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    request: ReviewCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Check booking belongs to customer
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

    # 2. Review only after job completion
    if booking.status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Review can only be added after booking is completed",
        )

    # 3. Captain must be assigned
    if not booking.captain_id:
        raise HTTPException(
            status_code=400,
            detail="No captain assigned to this booking",
        )

    # 4. Check duplicate review
    existing_review = (
        db.query(Review)
        .filter(Review.booking_id == booking.id)
        .first()
    )

    if existing_review:
        raise HTTPException(
            status_code=400,
            detail="Review already submitted for this booking",
        )

    # 5. Create review
    review = Review(
        booking_id=booking.id,
        customer_id=current_user.id,
        captain_id=booking.captain_id,
        rating=request.rating,
        review_text=request.review_text,
    )

    db.add(review)
    db.flush()

    # 6. Recalculate captain's average rating
    rating_result = (
        db.query(
            func.avg(Review.rating).label("average_rating")
        )
        .filter(
            Review.captain_id == booking.captain_id
        )
        .first()
    )

    captain = (
        db.query(Captain)
        .filter(Captain.id == booking.captain_id)
        .first()
    )

    if captain:
        captain.rating = (
            round(float(rating_result.average_rating), 2)
            if rating_result.average_rating is not None
            else 0.00
        )

    db.commit()
    db.refresh(review)

    return review


@router.get(
    "/booking/{booking_id}",
    response_model=ReviewResponse,
)
def get_booking_review(
    booking_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check booking exists
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

    # Only customer or assigned captain can view review
    is_customer = booking.customer_id == current_user.id

    captain = (
        db.query(Captain)
        .filter(Captain.user_id == current_user.id)
        .first()
    )

    is_captain = (
        captain is not None
        and booking.captain_id == captain.id
    )

    if not is_customer and not is_captain:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to view this review",
        )

    review = (
        db.query(Review)
        .filter(Review.booking_id == booking_id)
        .first()
    )

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found",
        )

    return review

@router.get(
    "/captain/{captain_id}",
    response_model=list[CaptainReviewResponse],
)
def get_captain_reviews(
    captain_id: int,
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(Captain.id == captain_id)
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=404,
            detail="Captain not found",
        )

    reviews = (
        db.query(Review)
        .filter(Review.captain_id == captain_id)
        .order_by(Review.id.desc())
        .all()
    )

    return reviews

@router.get(
    "/captain/{captain_id}/summary",
    response_model=CaptainRatingSummary,
)
def get_captain_rating_summary(
    captain_id: int,
    db: Session = Depends(get_db),
):
    captain = (
        db.query(Captain)
        .filter(Captain.id == captain_id)
        .first()
    )

    if not captain:
        raise HTTPException(
            status_code=404,
            detail="Captain not found",
        )

    result = (
        db.query(
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.id).label("total_reviews"),
        )
        .filter(Review.captain_id == captain_id)
        .first()
    )

    average_rating = (
        round(float(result.average_rating), 2)
        if result.average_rating is not None
        else 0.0
    )

    return {
        "captain_id": captain_id,
        "average_rating": average_rating,
        "total_reviews": result.total_reviews,
    }
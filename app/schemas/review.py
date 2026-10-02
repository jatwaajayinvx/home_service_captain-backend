from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreateRequest(BaseModel):
    booking_id: int
    rating: float = Field(..., ge=1.0, le=5.0)
    review_text: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    booking_id: int
    customer_id: int
    captain_id: int
    rating: float
    review_text: Optional[str] = None

    class Config:
        from_attributes = True
        
class CaptainReviewResponse(BaseModel):
    id: int
    booking_id: int
    customer_id: int
    captain_id: int
    rating: float
    review_text: Optional[str] = None

    class Config:
        from_attributes = True


class CaptainRatingSummary(BaseModel):
    captain_id: int
    average_rating: float
    total_reviews: int
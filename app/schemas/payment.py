from typing import Optional

from pydantic import BaseModel


class PaymentCreateRequest(BaseModel):
    booking_id: int
    payment_method: str


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    amount: float
    payment_method: str
    payment_status: str
    transaction_id: Optional[str] = None

    class Config:
        from_attributes = True


class CommissionResponse(BaseModel):
    id: int
    booking_id: int
    captain_id: int
    booking_amount: float
    commission_percent: float
    commission_amount: float
    captain_amount: float

    class Config:
        from_attributes = True
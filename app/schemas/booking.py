from datetime import date, time
from typing import Optional

from pydantic import BaseModel
from typing import Optional


class BookingCreateRequest(BaseModel):
    service_id: int
    address_id: int
    problem_description: Optional[str] = None
    problem_image: Optional[str] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None


# class BookingResponse(BaseModel):
#     id: int
#     booking_number: str
#     customer_id: int
#     captain_id: Optional[int] = None
#     service_id: int
#     address_id: int
#     problem_description: Optional[str] = None
#     scheduled_date: Optional[date] = None
#     scheduled_time: Optional[time] = None
#     estimated_amount: float
#     final_amount: Optional[float] = None
#     status: str

#     class Config:
#         from_attributes = True
        
class BookingAcceptResponse(BaseModel):
    id: int
    booking_number: str
    captain_id: int
    status: str

    class Config:
        from_attributes = True
        
class BookingAcceptResponse(BaseModel):
    id: int
    booking_number: str
    captain_id: int
    status: str

    class Config:
        from_attributes = True
        
class BookingStatusRequest(BaseModel):
    status: str
    
class BookingStatusHistoryResponse(BaseModel):
    id: int
    booking_id: int
    old_status: str | None = None
    new_status: str
    changed_by: int | None = None
    remarks: str | None = None

    class Config:
        from_attributes = True


from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel


class BookingResponse(BaseModel):
    id: int
    booking_number: str
    customer_id: int
    captain_id: Optional[int] = None
    service_id: int
    address_id: int

    problem_description: Optional[str] = None
    problem_image: Optional[str] = None

    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None

    estimated_amount: float
    final_amount: Optional[float] = None
    status: str

    captain_name: Optional[str] = None
    captain_rating: Optional[float] = None
    captain_experience: Optional[int] = None
    captain_mobile: Optional[str] = None

    class Config:
        from_attributes = True
        from_attributes = True
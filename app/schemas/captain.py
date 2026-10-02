from typing import Optional

from pydantic import BaseModel

from datetime import date, time, datetime

class CaptainStatusRequest(BaseModel):
    availability_status: str
    
class CaptainRegisterRequest(BaseModel):
    experience_years: int = 0
    
class CaptainLocationRequest(BaseModel):
    latitude: float
    longitude: float


class CaptainResponse(BaseModel):
    id: int
    user_id: int
    experience_years: int
    kyc_status: str
    availability_status: str
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    rating: float
    total_jobs: int
    completed_jobs: int

    class Config:
        from_attributes = True
        
class NearbyCaptainResponse(BaseModel):
    captain_id: int
    user_id: int
    name: str
    rating: float
    experience_years: int
    distance_km: float
    
class CaptainEarningResponse(BaseModel):
    id: int
    booking_id: int
    captain_id: int
    booking_amount: float
    commission_percent: float
    commission_amount: float
    captain_amount: float

class Config:
    from_attributes = True


class CaptainEarningsSummary(BaseModel):
    total_bookings: int
    total_booking_amount: float
    total_commission: float
    total_earnings: float
    
class CaptainJobResponse(BaseModel):
    booking_id: int
    booking_number: str
    service_name: str
    customer_name: str
    problem_description: Optional[str] = None
    address_line: str
    city: str
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    estimated_amount: float
    distance_km: float
    status: str
    
class CaptainJobDetailResponse(BaseModel):
    booking_id: int
    booking_number: str
    service_name: str
    customer_name: str
    customer_mobile: str
    problem_description: Optional[str] = None
    address_line: str
    landmark: Optional[str] = None
    city: str
    state: str
    pincode: str
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    estimated_amount: float
    distance_km: float
    status: str
    
class CaptainJobHistoryResponse(BaseModel):
    booking_id: int
    booking_number: str
    service_name: str
    customer_name: str
    problem_description: str | None = None
    address_line: str
    city: str
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    estimated_amount: float
    final_amount: float | None = None
    status: str
    completed_at: datetime | None = None
    
class CaptainProfileUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    experience_years: int | None = None
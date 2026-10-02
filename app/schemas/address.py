from typing import Optional

from pydantic import BaseModel


class AddressCreateRequest(BaseModel):
    address_line: str
    landmark: Optional[str] = None
    city: str
    state: str
    pincode: str

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    address_type: str = "HOME"
    is_default: bool = False


class AddressResponse(BaseModel):
    id: int
    user_id: int
    address_line: str
    landmark: Optional[str] = None
    city: str
    state: str
    pincode: str

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    address_type: Optional[str] = None
    is_default: bool

    class Config:
        from_attributes = True
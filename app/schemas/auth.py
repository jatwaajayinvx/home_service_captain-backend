from typing import Optional

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):

    name: str
    mobile: str
    email: Optional[EmailStr] = None
    password: str


class LoginRequest(BaseModel):

    mobile: str
    password: str


class UserResponse(BaseModel):

    id: int
    name: str
    mobile: str
    email: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):

    access_token: str
    token_type: str
    user: UserResponse
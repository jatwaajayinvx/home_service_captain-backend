from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    booking_id: Optional[int] = None
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UnreadNotificationCountResponse(BaseModel):
    unread_count: int   
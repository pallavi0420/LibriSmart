from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    body: str
    category: str  # "CIRCULATION", "RESERVATION", "FINE", "ANNOUNCEMENT"
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationMarkReadResponse(BaseModel):
    id: str
    is_read: bool
    message: str

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class OccupancyMetricsResponse(BaseModel):
    total_spots: int
    occupied_spots: int
    reserved_spots: int
    available_spots: int
    maintenance_spots: int
    occupancy_percentage: float
    updated_at: datetime

    class Config:
        from_attributes = True


class StudySeatResponse(BaseModel):
    id: str
    area_id: int
    floor_id: int
    floor_number: int
    seat_number: str
    grid_x: int
    grid_y: int
    qr_identifier: str
    seat_status: str
    current_occupancy_state: str  # "AVAILABLE", "OCCUPIED", "RESERVED", "MAINTENANCE"
    active_reservation_id: Optional[str] = None

    class Config:
        from_attributes = True


class StudyAreaResponse(BaseModel):
    id: int
    floor_id: int
    name: str
    noise_policy: str
    has_power_outlets: bool
    has_computers: bool
    total_seats_count: int = 0
    available_seats_count: int = 0

    class Config:
        from_attributes = True


class LibraryFloorResponse(BaseModel):
    id: int
    floor_number: int
    floor_name: str
    is_active: bool
    areas: List[StudyAreaResponse] = []

    class Config:
        from_attributes = True


class SeatReserveRequest(BaseModel):
    seat_id: str = Field(..., description="ID of the seat to reserve")
    start_time: datetime = Field(..., description="Start of time slot (UTC or ISO-8601 with timezone)")
    end_time: datetime = Field(..., description="End of time slot (UTC or ISO-8601 with timezone)")


class SeatReservationResponse(BaseModel):
    id: str
    seat_id: str
    seat_number: str
    area_name: str
    floor_name: str
    student_user_id: str
    student_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: str
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    qr_token: str

    class Config:
        from_attributes = True


class SeatBlockRequest(BaseModel):
    status: str = Field(..., description="OPERATIONAL, MAINTENANCE, or PERMANENTLY_BLOCKED")
    reason: Optional[str] = Field(None, description="Administrative reason for status change")


class SeatCheckInRequest(BaseModel):
    reservation_id: str = Field(..., description="Active reservation ID")
    qr_identifier: str = Field(..., description="Scanned or input QR code string from desk")


class SeatCheckOutRequest(BaseModel):
    reservation_id: str = Field(..., description="Active reservation ID to check out from")


class DemoQrResponse(BaseModel):
    seat_id: str
    seat_number: str
    area_name: str
    floor_name: str
    qr_identifier: str
    instructions: str

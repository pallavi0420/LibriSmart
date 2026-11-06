from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DigitalStudentCardResponse(BaseModel):
    student_user_id: str
    student_name: str
    student_id_number: str
    email: str
    department: str
    batch_year: int
    membership_status: str  # "ACTIVE", "SUSPENDED"
    digital_card_barcode: str  # e.g. "CARD-STU-2026-001"
    digital_card_qr: str  # e.g. "LIBRISMART:STU-2026-001:VERIFIED"
    member_since: datetime
    valid_until: datetime
    active_loans_count: int
    max_borrow_limit: int
    unpaid_fines_cents: int

    class Config:
        from_attributes = True

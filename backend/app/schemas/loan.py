from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class BookLoanResponse(BaseModel):
    id: str
    book_copy_id: str
    barcode: str
    book_id: str
    book_title: str
    book_author: str
    cover_image_url: Optional[str] = None
    shelf_location: Optional[str] = None
    student_user_id: str
    student_name: Optional[str] = None
    student_id_number: Optional[str] = None
    issue_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    status: str
    renewal_count: int
    max_renewals_allowed: int
    is_overdue: bool = False
    days_overdue: int = 0
    fine_amount_cents: int = 0

    class Config:
        from_attributes = True


class LoanRequestCreate(BaseModel):
    book_id: str = Field(..., description="ID of the book to request")


class LoanIssueRequest(BaseModel):
    student_id_or_email: str = Field(..., description="Student ID number (e.g. STU-2026-001) or university email")
    barcode: str = Field(..., description="Physical copy barcode (e.g. BAR-350884-C01)")
    loan_duration_days: int = Field(default=14, ge=1, le=60, description="Duration of loan in days")


class LoanReturnRequest(BaseModel):
    barcode: str = Field(..., description="Physical copy barcode scanned at circulation desk")
    condition_notes: Optional[str] = Field(None, description="Condition observation (e.g. Good, Minor page wear, Damaged)")
    mark_as_damaged: bool = Field(default=False, description="Flag if copy requires maintenance/replacement")


class LoanRenewalResponse(BaseModel):
    loan_id: str
    new_due_date: datetime
    renewal_count: int
    max_renewals_allowed: int
    message: str


class FineRecordResponse(BaseModel):
    id: str
    loan_id: str
    book_title: str
    amount_cents: int
    amount_display: str
    days_overdue: int
    status: str
    waiver_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FinePaymentRequest(BaseModel):
    amount_paid_cents: int = Field(..., gt=0, description="Amount paid in cents")
    payment_method: str = Field(default="CASH_OFFLINE", description="CASH_OFFLINE or CAMPUS_CARD")
    receipt_number: Optional[str] = Field(None, description="Custom receipt identifier, auto-generated if omitted")


class FinePaymentResponse(BaseModel):
    id: str
    fine_record_id: str
    amount_paid_cents: int
    receipt_number: str
    payment_date: datetime
    remaining_fine_cents: int
    status: str

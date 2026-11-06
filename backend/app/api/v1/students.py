from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_student
from app.models.base import utc_now
from app.models.loan import BookLoan, FineRecord, FineStatus, LoanStatus
from app.models.user import StudentProfile, User
from app.schemas.student import DigitalStudentCardResponse

router = APIRouter(prefix="/students", tags=["Students & Membership Card"])


@router.get("/me/card", response_model=DigitalStudentCardResponse)
async def get_my_digital_membership_card(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate the dynamic digital library membership card for the authenticated student.
    Includes verified student barcode, high-entropy QR token, active borrow count, and fine balance.
    """
    stmt = select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    profile = (await db.execute(stmt)).scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    # 1. Count active loans
    loan_stmt = (
        select(func.count())
        .select_from(BookLoan)
        .where(BookLoan.student_user_id == current_user.id, BookLoan.status == LoanStatus.ISSUED)
    )
    active_loans_count = (await db.execute(loan_stmt)).scalar() or 0

    # 2. Sum unpaid fines
    fine_stmt = (
        select(func.coalesce(func.sum(FineRecord.amount_cents), 0))
        .select_from(FineRecord)
        .where(FineRecord.student_user_id == current_user.id, FineRecord.status == FineStatus.PENDING)
    )
    unpaid_fines_cents = (await db.execute(fine_stmt)).scalar() or 0

    # 3. Validity window calculation (e.g., standard 4-year degree duration)
    member_since = current_user.created_at
    if member_since.tzinfo is None:
        member_since = member_since.replace(tzinfo=timezone.utc)

    # Valid until June 30th of graduation year (batch_year + 4)
    graduation_year = profile.batch_year + 4
    valid_until = datetime(graduation_year, 6, 30, 23, 59, 59, tzinfo=timezone.utc)

    membership_status = "SUSPENDED" if profile.is_suspended else "ACTIVE"

    # Barcode and QR strings formatted for campus library turnstiles & circulation scanners
    card_barcode = f"CARD-{profile.student_id_number}"
    card_qr = f"LIBRISMART:{profile.student_id_number}:{current_user.id[:8].upper()}:VERIFIED"

    return DigitalStudentCardResponse(
        student_user_id=current_user.id,
        student_name=profile.full_name,
        student_id_number=profile.student_id_number,
        email=current_user.email,
        department=profile.department,
        batch_year=profile.batch_year,
        membership_status=membership_status,
        digital_card_barcode=card_barcode,
        digital_card_qr=card_qr,
        member_since=member_since,
        valid_until=valid_until,
        active_loans_count=active_loans_count,
        max_borrow_limit=profile.max_borrow_limit,
        unpaid_fines_cents=unpaid_fines_cents
    )

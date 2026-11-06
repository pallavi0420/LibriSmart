import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_librarian, require_student
from app.models.base import utc_now
from app.models.book import Book, BookCopy, BookCopyStatus
from app.models.loan import BookLoan, BookWaitlist, FinePayment, FineRecord, FineStatus, LoanStatus
from app.models.user import StudentProfile, User
from app.schemas.loan import (
    BookLoanResponse,
    FinePaymentRequest,
    FinePaymentResponse,
    FineRecordResponse,
    LoanIssueRequest,
    LoanRenewalResponse,
    LoanReturnRequest,
)

router = APIRouter(prefix="/loans", tags=["Circulation & Loans"])
fines_router = APIRouter(prefix="/fines", tags=["Fines & Payments"])


def _normalize_dt(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _calculate_loan_overdue(loan: BookLoan, now: datetime) -> tuple[bool, int, int]:
    """Helper to compute overdue flag, days overdue, and accrued fine amount in cents."""
    if loan.status == LoanStatus.RETURNED:
        return False, 0, 0

    now = utc_now()
    curr = _normalize_dt(now)
    due = _normalize_dt(loan.due_date)
    if curr > due:
        days = max(1, (curr.date() - due.date()).days)
        fine_cents = days * settings.DEFAULT_FINE_PER_DAY_CENTS
        return True, days, fine_cents
    return False, 0, 0


def _build_loan_response(
    loan: BookLoan,
    copy: BookCopy,
    book: Book,
    student_user: Optional[User],
    student_profile: Optional[StudentProfile],
    explicit_fine_cents: Optional[int] = None
) -> BookLoanResponse:
    now = utc_now()
    is_overdue, days_overdue, live_fine = _calculate_loan_overdue(loan, now)

    fine_amount = live_fine
    if explicit_fine_cents is not None:
        fine_amount = explicit_fine_cents
    else:
        # Avoid triggering async lazy load if fine is not yet loaded in session
        from sqlalchemy import inspect
        insp = inspect(loan)
        if "fine" in insp.dict and insp.dict["fine"] is not None:
            fine_amount = insp.dict["fine"].amount_cents

    return BookLoanResponse(
        id=loan.id,
        book_copy_id=copy.id,
        barcode=copy.barcode,
        book_id=book.id,
        book_title=book.title,
        book_author=book.author,
        cover_image_url=book.cover_image_url,
        shelf_location=book.shelf_location,
        student_user_id=loan.student_user_id,
        student_name=student_profile.full_name if student_profile else (student_user.email if student_user else None),
        student_id_number=student_profile.student_id_number if student_profile else None,
        issue_date=loan.issue_date,
        due_date=loan.due_date,
        return_date=loan.return_date,
        status=loan.status.value,
        renewal_count=loan.renewal_count,
        max_renewals_allowed=loan.max_renewals_allowed,
        is_overdue=is_overdue or (loan.status == LoanStatus.OVERDUE),
        days_overdue=days_overdue,
        fine_amount_cents=fine_amount
    )


# ---------------------------------------------------------------------------
# Student Circulation Endpoints
# ---------------------------------------------------------------------------

@router.get("/my-active", response_model=List[BookLoanResponse])
async def get_my_active_loans(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all active book loans for the currently authenticated student.
    Includes live overdue calculations and fine tracking.
    """
    stmt = (
        select(BookLoan, BookCopy, Book, StudentProfile)
        .join(BookCopy, BookLoan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .outerjoin(StudentProfile, BookLoan.student_user_id == StudentProfile.user_id)
        .options(selectinload(BookLoan.fine))
        .where(
            BookLoan.student_user_id == current_user.id,
            BookLoan.status.in_([LoanStatus.ISSUED, LoanStatus.REQUESTED, LoanStatus.RETURN_REQUESTED, LoanStatus.OVERDUE])
        )
        .order_by(BookLoan.due_date.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        _build_loan_response(loan, copy, book, current_user, profile)
        for loan, copy, book, profile in rows
    ]


@router.get("/my-history", response_model=List[BookLoanResponse])
async def get_my_borrowing_history(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve past completed book borrowing history for the current student.
    """
    stmt = (
        select(BookLoan, BookCopy, Book, StudentProfile)
        .join(BookCopy, BookLoan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .outerjoin(StudentProfile, BookLoan.student_user_id == StudentProfile.user_id)
        .options(selectinload(BookLoan.fine))
        .where(
            BookLoan.student_user_id == current_user.id,
            BookLoan.status == LoanStatus.RETURNED
        )
        .order_by(BookLoan.return_date.desc().nullslast())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        _build_loan_response(loan, copy, book, current_user, profile)
        for loan, copy, book, profile in rows
    ]


@router.post("/{loan_id}/renew", response_model=LoanRenewalResponse)
async def renew_loan(
    loan_id: str,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Request a 14-day renewal extension for an active loan.
    Validates ownership, renewal limit, overdue status, and waitlist conflicts.
    """
    stmt = (
        select(BookLoan, BookCopy, Book)
        .join(BookCopy, BookLoan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(BookLoan.id == loan_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan record not found.")

    loan, copy, book = row

    if loan.student_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Loan belongs to another student.")

    if loan.status != LoanStatus.ISSUED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot renew loan with status '{loan.status.value}'. Must be currently ISSUED."
        )

    if loan.renewal_count >= loan.max_renewals_allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Renewal limit reached ({loan.renewal_count}/{loan.max_renewals_allowed}). Please return the book."
        )

    now = utc_now()
    curr = _normalize_dt(now)
    due = _normalize_dt(loan.due_date)
    if curr > due:
        days_late = (curr.date() - due.date()).days
        if days_late > 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Loan is overdue. Please settle outstanding fines at the circulation desk."
            )

    # Check for active waitlist reservations for this book
    waitlist_stmt = select(func.count()).select_from(BookWaitlist).where(
        BookWaitlist.book_id == book.id,
        BookWaitlist.status == "WAITING"
    )
    waiting_count = (await db.execute(waitlist_stmt)).scalar() or 0
    if waiting_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot renew: Another student is waiting on the reservation queue for this title."
        )

    # Apply 14 days renewal
    new_due_date = loan.due_date + timedelta(days=settings.DEFAULT_LOAN_DURATION_DAYS)
    loan.due_date = new_due_date
    loan.renewal_count += 1
    await db.commit()

    return LoanRenewalResponse(
        loan_id=loan.id,
        new_due_date=loan.due_date,
        renewal_count=loan.renewal_count,
        max_renewals_allowed=loan.max_renewals_allowed,
        message=f"Loan renewed successfully. New return deadline is {new_due_date.strftime('%b %d, %Y')}."
    )


# ---------------------------------------------------------------------------
# Librarian Circulation Endpoints
# ---------------------------------------------------------------------------

@router.get("/active", response_model=List[BookLoanResponse])
async def list_all_active_loans(
    student_id_number: Optional[str] = Query(None, description="Filter by Student ID number"),
    barcode: Optional[str] = Query(None, description="Filter by copy barcode"),
    overdue_only: bool = Query(False, description="Filter only loans past due date"),
    current_user: User = Depends(require_librarian),
    db: AsyncSession = Depends(get_db)
):
    """
    Librarian tool: View all active book circulation records across the institution.
    """
    stmt = (
        select(BookLoan, BookCopy, Book, User, StudentProfile)
        .join(BookCopy, BookLoan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .join(User, BookLoan.student_user_id == User.id)
        .outerjoin(StudentProfile, User.id == StudentProfile.user_id)
        .options(selectinload(BookLoan.fine))
        .where(BookLoan.status.in_([LoanStatus.ISSUED, LoanStatus.REQUESTED, LoanStatus.RETURN_REQUESTED, LoanStatus.OVERDUE]))
        .order_by(BookLoan.due_date.asc())
    )

    if student_id_number and student_id_number.strip():
        stmt = stmt.where(StudentProfile.student_id_number.ilike(f"%{student_id_number.strip()}%"))

    if barcode and barcode.strip():
        stmt = stmt.where(BookCopy.barcode.ilike(f"%{barcode.strip()}%"))

    if overdue_only:
        stmt = stmt.where(BookLoan.due_date < utc_now())

    result = await db.execute(stmt)
    rows = result.all()

    return [
        _build_loan_response(loan, copy, book, student, profile)
        for loan, copy, book, student, profile in rows
    ]


@router.post("/issue", response_model=BookLoanResponse, status_code=status.HTTP_201_CREATED)
async def issue_book_to_student(
    request: LoanIssueRequest,
    current_user: User = Depends(require_librarian),
    db: AsyncSession = Depends(get_db)
):
    """
    Librarian Circulation Desk: Formally issue a physical copy barcode to a student ID.
    Performs institutional limit verification, availability checks, and atomic state transition.
    """
    # 1. Resolve Student
    student_query = (
        select(User, StudentProfile)
        .outerjoin(StudentProfile, User.id == StudentProfile.user_id)
        .where(
            (User.email == request.student_id_or_email.strip().lower()) |
            (StudentProfile.student_id_number == request.student_id_or_email.strip())
        )
    )
    student_result = (await db.execute(student_query)).first()
    if not student_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student account not found for '{request.student_id_or_email}'."
        )

    student_user, student_profile = student_result

    if not student_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student account is deactivated.")

    if student_profile and student_profile.is_suspended:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student borrowing privileges are currently suspended.")

    if student_profile and student_profile.current_borrowed_count >= student_profile.max_borrow_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Borrow limit exceeded ({student_profile.current_borrowed_count}/{student_profile.max_borrow_limit} books). Student must return a book first."
        )

    # 2. Resolve Physical Copy by Barcode
    copy_query = (
        select(BookCopy, Book)
        .join(Book, BookCopy.book_id == Book.id)
        .where(BookCopy.barcode == request.barcode.strip())
    )
    copy_result = (await db.execute(copy_query)).first()
    if not copy_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No physical copy found with barcode '{request.barcode}'."
        )

    copy, book = copy_result

    if copy.status != BookCopyStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Copy '{copy.barcode}' is not available for issue (Current Status: {copy.status.value})."
        )

    # 3. Check for existing active loan on this copy
    existing_loan = await db.execute(
        select(BookLoan).where(
            BookLoan.book_copy_id == copy.id,
            BookLoan.status.in_([LoanStatus.ISSUED, LoanStatus.OVERDUE])
        )
    )
    if existing_loan.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Physical copy '{copy.barcode}' is already checked out on an active loan."
        )

    # 4. Atomic Issue Transaction
    now = utc_now()
    due_date = now + timedelta(days=request.loan_duration_days)

    copy.status = BookCopyStatus.ISSUED
    book.available_copies_count = max(0, book.available_copies_count - 1)

    if student_profile:
        student_profile.current_borrowed_count += 1

    new_loan = BookLoan(
        book_copy_id=copy.id,
        student_user_id=student_user.id,
        issued_by_librarian_id=current_user.id,
        issue_date=now,
        due_date=due_date,
        status=LoanStatus.ISSUED,
        renewal_count=0,
        max_renewals_allowed=2
    )
    db.add(new_loan)
    await db.commit()
    await db.refresh(new_loan)

    return _build_loan_response(new_loan, copy, book, student_user, student_profile, explicit_fine_cents=0)


@router.post("/return", response_model=BookLoanResponse)
async def process_book_return(
    request: LoanReturnRequest,
    current_user: User = Depends(require_librarian),
    db: AsyncSession = Depends(get_db)
):
    """
    Librarian Circulation Desk: Process book return by scanning copy barcode.
    Verifies loan, records return date, calculates late fines, and restocks inventory.
    """
    # 1. Resolve Copy and Active Loan
    stmt = (
        select(BookLoan, BookCopy, Book, User, StudentProfile)
        .join(BookCopy, BookLoan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .join(User, BookLoan.student_user_id == User.id)
        .outerjoin(StudentProfile, User.id == StudentProfile.user_id)
        .where(
            BookCopy.barcode == request.barcode.strip(),
            BookLoan.status.in_([LoanStatus.ISSUED, LoanStatus.RETURN_REQUESTED, LoanStatus.OVERDUE, LoanStatus.REQUESTED])
        )
        .options(selectinload(BookLoan.fine))
    )
    result = (await db.execute(stmt)).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active loan record found for barcode '{request.barcode}'."
        )

    loan, copy, book, student_user, student_profile = result
    now = utc_now()

    # 2. Update Loan Status
    loan.status = LoanStatus.RETURNED
    loan.return_date = now

    # 3. Update Copy Status & Inventory
    if request.condition_notes:
        copy.condition_notes = request.condition_notes

    if request.mark_as_damaged:
        copy.status = BookCopyStatus.DAMAGED
    else:
        copy.status = BookCopyStatus.AVAILABLE
        book.available_copies_count = min(book.total_copies_count, book.available_copies_count + 1)

    if student_profile:
        student_profile.current_borrowed_count = max(0, student_profile.current_borrowed_count - 1)

    # 4. Overdue Fine Calculation Engine
    now = utc_now()
    curr = _normalize_dt(now)
    due = _normalize_dt(loan.due_date)
    if curr.date() > due.date():
        days_overdue = (curr.date() - due.date()).days
        fine_cents = days_overdue * settings.DEFAULT_FINE_PER_DAY_CENTS

        fine_record = FineRecord(
            loan_id=loan.id,
            student_user_id=student_user.id,
            amount_cents=fine_cents,
            days_overdue=days_overdue,
            status=FineStatus.PENDING
        )
        db.add(fine_record)
        loan.fine = fine_record

    # 5. Check Waitlist Auto-Notification
    waitlist_stmt = (
        select(BookWaitlist)
        .where(
            BookWaitlist.book_id == book.id,
            BookWaitlist.status == "WAITING"
        )
        .order_by(BookWaitlist.queue_position.asc())
    )
    waitlist_entry = (await db.execute(waitlist_stmt)).scalars().first()
    if waitlist_entry:
        waitlist_entry.status = "NOTIFIED"
        waitlist_entry.notified_at = now
        waitlist_entry.claim_deadline = now + timedelta(hours=48)

    await db.commit()
    await db.refresh(loan)

    recorded_fine = fine_cents if (curr.date() > due.date()) else 0
    return _build_loan_response(loan, copy, book, student_user, student_profile, explicit_fine_cents=recorded_fine)


# ---------------------------------------------------------------------------
# Fines & Payments Endpoints
# ---------------------------------------------------------------------------

@fines_router.get("/my-fines", response_model=List[FineRecordResponse])
async def get_my_fines(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all outstanding and historical fines for the authenticated student.
    """
    stmt = (
        select(FineRecord, BookLoan, BookCopy, Book)
        .join(BookLoan, FineRecord.loan_id == BookLoan.id)
        .join(BookCopy, BookLoan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(FineRecord.student_user_id == current_user.id)
        .order_by(FineRecord.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        FineRecordResponse(
            id=fine.id,
            loan_id=fine.loan_id,
            book_title=book.title,
            amount_cents=fine.amount_cents,
            amount_display=f"${fine.amount_cents / 100:.2f}",
            days_overdue=fine.days_overdue,
            status=fine.status.value,
            waiver_reason=fine.waiver_reason,
            created_at=fine.created_at
        )
        for fine, loan, copy, book in rows
    ]


@fines_router.post("/{fine_id}/pay-offline", response_model=FinePaymentResponse)
async def settle_fine_offline(
    fine_id: str,
    request: FinePaymentRequest,
    current_user: User = Depends(require_librarian),
    db: AsyncSession = Depends(get_db)
):
    """
    Librarian Settlement: Record an offline cash or campus counter payment for a fine.
    Generates an official audit receipt and updates the fine status.
    """
    fine_query = select(FineRecord).where(FineRecord.id == fine_id)
    fine = (await db.execute(fine_query)).scalar_one_or_none()
    if not fine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fine record not found.")

    if fine.status == FineStatus.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This fine has already been fully paid.")

    receipt_no = request.receipt_number or f"RCPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    payment = FinePayment(
        fine_record_id=fine.id,
        amount_paid_cents=request.amount_paid_cents,
        received_by_librarian_id=current_user.id,
        payment_method=request.payment_method,
        receipt_number=receipt_no
    )
    db.add(payment)

    # If amount covers the fine, mark PAID
    if request.amount_paid_cents >= fine.amount_cents:
        fine.status = FineStatus.PAID
        remaining = 0
    else:
        remaining = fine.amount_cents - request.amount_paid_cents

    await db.commit()
    await db.refresh(payment)

    return FinePaymentResponse(
        id=payment.id,
        fine_record_id=fine.id,
        amount_paid_cents=payment.amount_paid_cents,
        receipt_number=payment.receipt_number,
        payment_date=payment.created_at,
        remaining_fine_cents=remaining,
        status=fine.status.value
    )

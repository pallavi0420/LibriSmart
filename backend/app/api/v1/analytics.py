from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_librarian
from app.models.base import utc_now
from app.models.book import Book, BookCategory, BookCopy, BookCopyStatus
from app.models.loan import BookLoan, FineRecord, FineStatus, LoanStatus
from app.models.seat import ReservationStatus, SeatReservation, SeatStatus, StudySeat
from app.models.user import User, UserRole
from app.schemas.analytics import (
    CategorySharePoint,
    DailyCirculationPoint,
    DashboardAnalyticsResponse,
)

router = APIRouter(prefix="/analytics", tags=["Librarian & Administrative Analytics"])


def _normalize_dt(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.get("/dashboard", response_model=DashboardAnalyticsResponse)
async def get_library_dashboard_analytics(
    current_user: User = Depends(require_librarian),
    db: AsyncSession = Depends(get_db)
):
    """
    Comprehensive Librarian Administrative Analytics:
    Aggregates library inventory velocity, student circulation metrics, fine recoveries,
    and real-time space occupancy analytics for campus administrative reporting.
    """
    now = utc_now()

    # 1. Total Registered Students
    students_stmt = select(func.count()).select_from(User).where(User.role == UserRole.STUDENT)
    total_students = (await db.execute(students_stmt)).scalar() or 0

    # 2. Books & Physical Copies
    books_stmt = select(func.count()).select_from(Book)
    total_books = (await db.execute(books_stmt)).scalar() or 0

    copies_stmt = select(func.count()).select_from(BookCopy)
    total_copies = (await db.execute(copies_stmt)).scalar() or 0

    avail_copies_stmt = select(func.count()).select_from(BookCopy).where(BookCopy.status == BookCopyStatus.AVAILABLE)
    available_copies = (await db.execute(avail_copies_stmt)).scalar() or 0

    issued_copies_stmt = select(func.count()).select_from(BookCopy).where(BookCopy.status == BookCopyStatus.ISSUED)
    issued_copies = (await db.execute(issued_copies_stmt)).scalar() or 0

    # 3. Active & Overdue Loans
    overdue_stmt = (
        select(func.count())
        .select_from(BookLoan)
        .where(
            or_(
                BookLoan.status == LoanStatus.OVERDUE,
                (BookLoan.status == LoanStatus.ISSUED) & (BookLoan.due_date < now)
            )
        )
    )
    overdue_loans = (await db.execute(overdue_stmt)).scalar() or 0

    # 4. Fines Collected & Pending
    fines_unpaid_stmt = (
        select(func.coalesce(func.sum(FineRecord.amount_cents), 0))
        .select_from(FineRecord)
        .where(FineRecord.status == FineStatus.PENDING)
    )
    total_fines_unpaid = (await db.execute(fines_unpaid_stmt)).scalar() or 0

    fines_paid_stmt = (
        select(func.coalesce(func.sum(FineRecord.amount_cents), 0))
        .select_from(FineRecord)
        .where(FineRecord.status == FineStatus.PAID)
    )
    total_fines_collected = (await db.execute(fines_paid_stmt)).scalar() or 0

    # 5. Study Spot Occupancy
    spots_stmt = (
        select(func.count())
        .select_from(StudySeat)
        .where(StudySeat.status != SeatStatus.PERMANENTLY_BLOCKED)
    )
    total_spots = (await db.execute(spots_stmt)).scalar() or 0

    active_res_stmt = (
        select(SeatReservation)
        .where(
            SeatReservation.start_time <= now,
            SeatReservation.end_time > now,
            SeatReservation.status.in_([ReservationStatus.CHECKED_IN, ReservationStatus.PENDING_CHECKIN])
        )
    )
    active_res = (await db.execute(active_res_stmt)).scalars().all()

    occupied_spots = sum(1 for r in active_res if r.status == ReservationStatus.CHECKED_IN)
    reserved_spots = sum(1 for r in active_res if r.status == ReservationStatus.PENDING_CHECKIN)

    occupancy_pct = round(((occupied_spots + reserved_spots) / total_spots) * 100, 1) if total_spots > 0 else 0.0

    # 6. Category Distribution
    cat_stmt = (
        select(BookCategory.name, func.count(Book.id))
        .join(Book, Book.category_id == BookCategory.id)
        .group_by(BookCategory.name)
        .order_by(func.count(Book.id).desc())
    )
    cat_rows = (await db.execute(cat_stmt)).all()
    category_distribution = [
        CategorySharePoint(category_name=cat_name, books_count=count)
        for cat_name, count in cat_rows
    ]

    # 7. Daily Circulation Trends (Last 7 Days)
    circulation_trends: List[DailyCirculationPoint] = []
    for day_offset in range(6, -1, -1):
        target_day = now - timedelta(days=day_offset)
        start_of_day = target_day.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Count issues on this day
        issue_stmt = (
            select(func.count())
            .select_from(BookLoan)
            .where(BookLoan.issue_date >= start_of_day, BookLoan.issue_date < end_of_day)
        )
        day_issues = (await db.execute(issue_stmt)).scalar() or 0

        # Count returns on this day
        return_stmt = (
            select(func.count())
            .select_from(BookLoan)
            .where(BookLoan.return_date >= start_of_day, BookLoan.return_date < end_of_day)
        )
        day_returns = (await db.execute(return_stmt)).scalar() or 0

        circulation_trends.append(
            DailyCirculationPoint(
                date_str=target_day.strftime("%b %d"),
                issues_count=day_issues,
                returns_count=day_returns
            )
        )

    return DashboardAnalyticsResponse(
        total_students=total_students,
        total_books=total_books,
        total_copies=total_copies,
        available_copies=available_copies,
        issued_copies=issued_copies,
        overdue_loans=overdue_loans,
        total_fines_unpaid_cents=total_fines_unpaid,
        total_fines_collected_cents=total_fines_collected,
        total_study_spots=total_spots,
        occupied_study_spots=occupied_spots,
        reserved_study_spots=reserved_spots,
        occupancy_percentage=occupancy_pct,
        circulation_trends=circulation_trends,
        category_distribution=category_distribution,
        generated_at=now
    )

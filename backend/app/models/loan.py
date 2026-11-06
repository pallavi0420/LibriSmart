import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid, utc_now


class LoanStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    ISSUED = "ISSUED"
    RETURN_REQUESTED = "RETURN_REQUESTED"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"


class FineStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    WAIVED = "WAIVED"


class BookLoan(Base, TimestampMixin):
    __tablename__ = "book_loans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    book_copy_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("book_copies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    student_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    issued_by_librarian_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    issue_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    return_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus, name="loan_status_enum", native_enum=False),
        default=LoanStatus.REQUESTED,
        nullable=False,
        index=True
    )
    renewal_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_renewals_allowed: Mapped[int] = mapped_column(Integer, default=2, nullable=False)

    # Relationships
    copy: Mapped["BookCopy"] = relationship("BookCopy")
    student: Mapped["User"] = relationship("User", foreign_keys=[student_user_id])
    fine: Mapped[Optional["FineRecord"]] = relationship(
        "FineRecord",
        back_populates="loan",
        uselist=False,
        cascade="all, delete-orphan"
    )


class FineRecord(Base, TimestampMixin):
    __tablename__ = "fine_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    loan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("book_loans.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    student_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    days_overdue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[FineStatus] = mapped_column(
        Enum(FineStatus, name="fine_status_enum", native_enum=False),
        default=FineStatus.PENDING,
        nullable=False,
        index=True
    )
    waiver_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    loan: Mapped["BookLoan"] = relationship("BookLoan", back_populates="fine")
    payments: Mapped[list["FinePayment"]] = relationship(
        "FinePayment",
        back_populates="fine_record",
        cascade="all, delete-orphan"
    )


class FinePayment(Base, TimestampMixin):
    __tablename__ = "fine_payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    fine_record_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("fine_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    amount_paid_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    received_by_librarian_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    payment_method: Mapped[str] = mapped_column(String(50), default="CASH_OFFLINE", nullable=False)
    receipt_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    fine_record: Mapped["FineRecord"] = relationship("FineRecord", back_populates="payments")


class BookWaitlist(Base, TimestampMixin):
    __tablename__ = "book_waitlists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    book_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    queue_position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="WAITING", nullable=False)
    notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    claim_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

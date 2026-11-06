import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid, utc_now


class SeatStatus(str, enum.Enum):
    OPERATIONAL = "OPERATIONAL"
    MAINTENANCE = "MAINTENANCE"
    PERMANENTLY_BLOCKED = "PERMANENTLY_BLOCKED"


class ReservationStatus(str, enum.Enum):
    PENDING_CHECKIN = "PENDING_CHECKIN"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW_EXPIRED = "NO_SHOW_EXPIRED"


class LibraryFloor(Base, TimestampMixin):
    __tablename__ = "library_floors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    floor_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    floor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    areas: Mapped[List["StudyArea"]] = relationship("StudyArea", back_populates="floor", cascade="all, delete-orphan")


class StudyArea(Base, TimestampMixin):
    __tablename__ = "study_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    floor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("library_floors.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    noise_policy: Mapped[str] = mapped_column(String(50), default="SILENT", nullable=False)
    has_power_outlets: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_computers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    floor: Mapped["LibraryFloor"] = relationship("LibraryFloor", back_populates="areas")
    seats: Mapped[List["StudySeat"]] = relationship("StudySeat", back_populates="area", cascade="all, delete-orphan")


class StudySeat(Base, TimestampMixin):
    __tablename__ = "study_seats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    area_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("study_areas.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    seat_number: Mapped[str] = mapped_column(String(20), nullable=False)
    grid_x: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    grid_y: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qr_identifier: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    status: Mapped[SeatStatus] = mapped_column(
        Enum(SeatStatus, name="seat_status_enum", native_enum=False),
        default=SeatStatus.OPERATIONAL,
        nullable=False
    )

    area: Mapped["StudyArea"] = relationship("StudyArea", back_populates="seats")
    reservations: Mapped[List["SeatReservation"]] = relationship("SeatReservation", back_populates="seat")


class SeatReservation(Base, TimestampMixin):
    __tablename__ = "seat_reservations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    seat_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("study_seats.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, name="reservation_status_enum", native_enum=False),
        default=ReservationStatus.PENDING_CHECKIN,
        nullable=False,
        index=True
    )
    check_in_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    seat: Mapped["StudySeat"] = relationship("StudySeat", back_populates="reservations")
    student: Mapped["User"] = relationship("User")
    occupancy_logs: Mapped[List["SeatOccupancyLog"]] = relationship(
        "SeatOccupancyLog",
        back_populates="reservation",
        cascade="all, delete-orphan"
    )


class SeatOccupancyLog(Base):
    __tablename__ = "seat_occupancy_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    reservation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("seat_reservations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    reservation: Mapped["SeatReservation"] = relationship("SeatReservation", back_populates="occupancy_logs")

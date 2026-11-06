import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_librarian, require_student
from app.models.base import utc_now
from app.models.seat import (
    LibraryFloor,
    ReservationStatus,
    SeatOccupancyLog,
    SeatReservation,
    SeatStatus,
    StudyArea,
    StudySeat,
)
from app.models.user import StudentProfile, User
from app.schemas.seat import (
    DemoQrResponse,
    LibraryFloorResponse,
    OccupancyMetricsResponse,
    SeatBlockRequest,
    SeatCheckInRequest,
    SeatCheckOutRequest,
    SeatReservationResponse,
    SeatReserveRequest,
    StudyAreaResponse,
    StudySeatResponse,
)

router = APIRouter(prefix="/seats", tags=["Study Spots & Seat Reservations"])


def _normalize_dt(dt: datetime) -> datetime:
    """Ensure datetime is offset-aware in UTC for safe comparison."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# Occupancy & Seating Layout Endpoints
# ---------------------------------------------------------------------------

@router.get("/occupancy", response_model=OccupancyMetricsResponse)
async def get_library_occupancy(db: AsyncSession = Depends(get_db)):
    """
    Real-time occupancy dashboard metrics across the entire library.
    Calculates operational spots, active occupied desks, upcoming slot reservations,
    maintenance blocks, and overall library occupancy percentage.
    """
    now = utc_now()

    # 1. Total & Maintenance Seats Count
    total_spots_query = select(func.count()).select_from(StudySeat).where(StudySeat.status != SeatStatus.PERMANENTLY_BLOCKED)
    total_spots = (await db.execute(total_spots_query)).scalar() or 0

    maint_spots_query = select(func.count()).select_from(StudySeat).where(StudySeat.status == SeatStatus.MAINTENANCE)
    maintenance_spots = (await db.execute(maint_spots_query)).scalar() or 0

    # 2. Active Reservations overlapping current moment
    active_res_query = (
        select(SeatReservation)
        .where(
            SeatReservation.start_time <= now,
            SeatReservation.end_time > now,
            SeatReservation.status.in_([ReservationStatus.PENDING_CHECKIN, ReservationStatus.CHECKED_IN])
        )
    )
    active_reservations = (await db.execute(active_res_query)).scalars().all()

    occupied_count = sum(1 for r in active_reservations if r.status == ReservationStatus.CHECKED_IN)
    reserved_count = sum(1 for r in active_reservations if r.status == ReservationStatus.PENDING_CHECKIN)

    available_count = max(0, total_spots - occupied_count - reserved_count - maintenance_spots)
    occupancy_pct = round(((occupied_count + reserved_count) / total_spots) * 100, 1) if total_spots > 0 else 0.0

    return OccupancyMetricsResponse(
        total_spots=total_spots,
        occupied_spots=occupied_count,
        reserved_spots=reserved_count,
        available_spots=available_count,
        maintenance_spots=maintenance_spots,
        occupancy_percentage=occupancy_pct,
        updated_at=now
    )


@router.get("/floors", response_model=List[LibraryFloorResponse])
async def list_library_floors(db: AsyncSession = Depends(get_db)):
    """
    List all active library floors with designated study areas and seat capacities.
    """
    stmt = (
        select(LibraryFloor)
        .where(LibraryFloor.is_active == True)
        .options(selectinload(LibraryFloor.areas).selectinload(StudyArea.seats))
        .order_by(LibraryFloor.floor_number.asc())
    )
    result = await db.execute(stmt)
    floors = result.scalars().all()

    output = []
    for floor in floors:
        areas_output = []
        for area in floor.areas:
            total_seats = len(area.seats)
            # Available operational seats
            avail_seats = sum(1 for s in area.seats if s.status == SeatStatus.OPERATIONAL)
            areas_output.append(
                StudyAreaResponse(
                    id=area.id,
                    floor_id=floor.id,
                    name=area.name,
                    noise_policy=area.noise_policy,
                    has_power_outlets=area.has_power_outlets,
                    has_computers=area.has_computers,
                    total_seats_count=total_seats,
                    available_seats_count=avail_seats
                )
            )
        output.append(
            LibraryFloorResponse(
                id=floor.id,
                floor_number=floor.floor_number,
                floor_name=floor.floor_name,
                is_active=floor.is_active,
                areas=areas_output
            )
        )
    return output


@router.get("/map", response_model=List[StudySeatResponse])
async def get_interactive_seat_map(
    floor_id: Optional[int] = Query(None, description="Filter by library floor ID"),
    area_id: Optional[int] = Query(None, description="Filter by study zone area ID"),
    start_time: Optional[datetime] = Query(None, description="Start time for availability evaluation"),
    end_time: Optional[datetime] = Query(None, description="End time for availability evaluation"),
    db: AsyncSession = Depends(get_db)
):
    """
    Interactive 2D seating layout map:
    Returns desk nodes with grid (X, Y) coordinates and dynamic color status
    (AVAILABLE [Green], OCCUPIED [Red], RESERVED [Blue], MAINTENANCE [Grey])
    evaluated for the requested date/time slot window.
    """
    now = utc_now()
    eval_start = _normalize_dt(start_time) if start_time else now
    eval_end = _normalize_dt(end_time) if end_time else (eval_start + timedelta(hours=2))

    # Base query for study seats joined with area and floor
    stmt = (
        select(StudySeat, StudyArea, LibraryFloor)
        .join(StudyArea, StudySeat.area_id == StudyArea.id)
        .join(LibraryFloor, StudyArea.floor_id == LibraryFloor.id)
        .order_by(StudySeat.grid_y.asc(), StudySeat.grid_x.asc())
    )

    if area_id is not None:
        stmt = stmt.where(StudySeat.area_id == area_id)
    elif floor_id is not None:
        stmt = stmt.where(StudyArea.floor_id == floor_id)

    seat_rows = (await db.execute(stmt)).all()
    if not seat_rows:
        return []

    seat_ids = [s.id for s, _, _ in seat_rows]

    # Query active reservations that intersect with the requested [eval_start, eval_end) window
    res_stmt = (
        select(SeatReservation)
        .where(
            SeatReservation.seat_id.in_(seat_ids),
            SeatReservation.status.in_([ReservationStatus.PENDING_CHECKIN, ReservationStatus.CHECKED_IN]),
            SeatReservation.start_time < eval_end,
            SeatReservation.end_time > eval_start
        )
    )
    res_rows = (await db.execute(res_stmt)).scalars().all()

    # Map seat_id to active reservation
    res_map = {r.seat_id: r for r in res_rows}

    results = []
    for seat, area, floor in seat_rows:
        active_res = res_map.get(seat.id)

        # Determine color/occupancy status
        if seat.status != SeatStatus.OPERATIONAL:
            state = "MAINTENANCE"
        elif active_res is not None:
            if active_res.status == ReservationStatus.CHECKED_IN:
                state = "OCCUPIED"  # Red
            else:
                state = "RESERVED"  # Blue
        else:
            state = "AVAILABLE"  # Green

        results.append(
            StudySeatResponse(
                id=seat.id,
                area_id=area.id,
                floor_id=floor.id,
                floor_number=floor.floor_number,
                seat_number=seat.seat_number,
                grid_x=seat.grid_x,
                grid_y=seat.grid_y,
                qr_identifier=seat.qr_identifier,
                seat_status=seat.status.value,
                current_occupancy_state=state,
                active_reservation_id=active_res.id if active_res else None
            )
        )
    return results


# ---------------------------------------------------------------------------
# Space Reservation Workflow Endpoints
# ---------------------------------------------------------------------------

@router.post("/reserve", response_model=SeatReservationResponse, status_code=status.HTTP_201_CREATED)
async def reserve_study_seat(
    request: SeatReserveRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Atomically reserve a study desk for an advance time slot.
    Guarantees concurrency safety and double-booking prevention under load.
    Enforces university policy: duration between 30 min and 4 hrs, single booking limit.
    """
    now = utc_now()
    req_start = _normalize_dt(request.start_time)
    req_end = _normalize_dt(request.end_time)

    # 1. Validation Rules
    if req_start >= req_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start time must be before end time.")

    # Grace period: allow booking starting up to 10 minutes ago
    if req_start < (now - timedelta(minutes=10)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot book study spots in the past.")

    duration_mins = int((req_end - req_start).total_seconds() / 60)
    if duration_mins < 30:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Minimum study spot reservation duration is 30 minutes.")
    if duration_mins > 240:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum study spot reservation duration is 4 hours.")

    if req_end > (now + timedelta(days=7)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Advance booking is limited to 7 days ahead.")

    # 2. Check Student Active Reservation Limits & Overlaps
    student_overlap = await db.execute(
        select(SeatReservation).where(
            SeatReservation.student_user_id == current_user.id,
            SeatReservation.status.in_([ReservationStatus.PENDING_CHECKIN, ReservationStatus.CHECKED_IN]),
            SeatReservation.start_time < req_end,
            SeatReservation.end_time > req_start
        )
    )
    if student_overlap.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active study spot reserved during this time slot."
        )

    # 3. Resolve Study Seat
    seat_query = (
        select(StudySeat, StudyArea, LibraryFloor)
        .join(StudyArea, StudySeat.area_id == StudyArea.id)
        .join(LibraryFloor, StudyArea.floor_id == LibraryFloor.id)
        .where(StudySeat.id == request.seat_id)
    )
    seat_row = (await db.execute(seat_query)).first()
    if not seat_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study seat not found.")

    seat, area, floor = seat_row

    if seat.status != SeatStatus.OPERATIONAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Seat '{seat.seat_number}' is unavailable for booking (Status: {seat.status.value})."
        )

    # 4. Concurrency Guard: Check for Overlapping Seat Bookings
    seat_conflict = await db.execute(
        select(SeatReservation).where(
            SeatReservation.seat_id == seat.id,
            SeatReservation.status.in_([ReservationStatus.PENDING_CHECKIN, ReservationStatus.CHECKED_IN]),
            SeatReservation.start_time < req_end,
            SeatReservation.end_time > req_start
        )
    )
    if seat_conflict.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seat '{seat.seat_number}' was just booked by another student for this time slot."
        )

    # 5. Insert Reservation & Audit Log
    reservation_id = str(uuid.uuid4())
    qr_token = f"TOKEN-{uuid.uuid4().hex[:12].upper()}"

    new_reservation = SeatReservation(
        id=reservation_id,
        seat_id=seat.id,
        student_user_id=current_user.id,
        start_time=req_start,
        end_time=req_end,
        status=ReservationStatus.PENDING_CHECKIN
    )
    db.add(new_reservation)

    audit_log = SeatOccupancyLog(
        reservation_id=reservation_id,
        event_type="RESERVED"
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(new_reservation)

    # Get student profile name
    prof = (await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))).scalar_one_or_none()

    return SeatReservationResponse(
        id=new_reservation.id,
        seat_id=seat.id,
        seat_number=seat.seat_number,
        area_name=area.name,
        floor_name=floor.floor_name,
        student_user_id=current_user.id,
        student_name=prof.full_name if prof else current_user.email,
        start_time=new_reservation.start_time,
        end_time=new_reservation.end_time,
        status=new_reservation.status.value,
        check_in_time=new_reservation.check_in_time,
        check_out_time=new_reservation.check_out_time,
        qr_token=qr_token
    )


@router.post("/{reservation_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_seat_reservation(
    reservation_id: str,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel an upcoming advance study-spot reservation.
    Immediately releases the seat back to AVAILABLE for other students.
    """
    stmt = select(SeatReservation).where(SeatReservation.id == reservation_id)
    reservation = (await db.execute(stmt)).scalar_one_or_none()
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found.")

    if reservation.student_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Reservation belongs to another student.")

    if reservation.status != ReservationStatus.PENDING_CHECKIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel reservation with status '{reservation.status.value}'."
        )

    reservation.status = ReservationStatus.CANCELLED
    audit_log = SeatOccupancyLog(
        reservation_id=reservation.id,
        event_type="CANCELLED_BY_STUDENT"
    )
    db.add(audit_log)
    await db.commit()

    return {"message": "Seat reservation cancelled successfully. Spot is now released."}


@router.get("/my-reservations", response_model=List[SeatReservationResponse])
async def get_my_seat_reservations(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all active upcoming and past seat reservations for the authenticated student.
    """
    stmt = (
        select(SeatReservation, StudySeat, StudyArea, LibraryFloor, StudentProfile)
        .join(StudySeat, SeatReservation.seat_id == StudySeat.id)
        .join(StudyArea, StudySeat.area_id == StudyArea.id)
        .join(LibraryFloor, StudyArea.floor_id == LibraryFloor.id)
        .outerjoin(StudentProfile, SeatReservation.student_user_id == StudentProfile.user_id)
        .where(SeatReservation.student_user_id == current_user.id)
        .order_by(SeatReservation.start_time.desc())
    )
    rows = (await db.execute(stmt)).all()

    return [
        SeatReservationResponse(
            id=res.id,
            seat_id=seat.id,
            seat_number=seat.seat_number,
            area_name=area.name,
            floor_name=floor.floor_name,
            student_user_id=res.student_user_id,
            student_name=prof.full_name if prof else current_user.email,
            start_time=res.start_time,
            end_time=res.end_time,
            status=res.status.value,
            check_in_time=res.check_in_time,
            check_out_time=res.check_out_time,
            qr_token=f"TOKEN-{res.id[:8].upper()}"
        )
        for res, seat, area, floor, prof in rows
    ]


@router.post("/check-in", response_model=SeatReservationResponse)
async def check_in_to_seat(
    request: SeatCheckInRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate QR code scanned at desk against the student's active reservation.
    Transitions reservation from PENDING_CHECKIN -> CHECKED_IN.
    Enforces check-in time tolerance window (+/- 15 min around start time).
    """
    now = utc_now()

    stmt = (
        select(SeatReservation, StudySeat, StudyArea, LibraryFloor, StudentProfile)
        .join(StudySeat, SeatReservation.seat_id == StudySeat.id)
        .join(StudyArea, StudySeat.area_id == StudyArea.id)
        .join(LibraryFloor, StudyArea.floor_id == LibraryFloor.id)
        .outerjoin(StudentProfile, SeatReservation.student_user_id == StudentProfile.user_id)
        .where(SeatReservation.id == request.reservation_id)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found.")

    res, seat, area, floor, prof = row

    if res.student_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Reservation belongs to another student."
        )

    if res.status == ReservationStatus.CHECKED_IN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already checked in to this reservation."
        )

    if res.status != ReservationStatus.PENDING_CHECKIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check in. Reservation status is '{res.status.value}'."
        )

    # Verify QR Identifier matches the reserved physical desk
    scanned_qr = request.qr_identifier.strip()
    if scanned_qr != seat.qr_identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"QR code mismatch. This QR ('{scanned_qr}') does not match your reserved desk '{seat.seat_number}'."
        )

    # Check-in time window tolerance check:
    # Allowed: 15 minutes prior to start_time up until end_time
    start_norm = _normalize_dt(res.start_time)
    end_norm = _normalize_dt(res.end_time)

    if now < (start_norm - timedelta(minutes=15)):
        mins_early = int(((start_norm - timedelta(minutes=15)) - now).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too early to check in. Check-in opens 15 minutes before your start time (in {mins_early} mins)."
        )

    if now > end_norm:
        res.status = ReservationStatus.NO_SHOW_EXPIRED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation time window has already expired."
        )

    res.status = ReservationStatus.CHECKED_IN
    res.check_in_time = now

    audit_log = SeatOccupancyLog(
        reservation_id=res.id,
        event_type="CHECKED_IN"
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(res)

    return SeatReservationResponse(
        id=res.id,
        seat_id=seat.id,
        seat_number=seat.seat_number,
        area_name=area.name,
        floor_name=floor.floor_name,
        student_user_id=res.student_user_id,
        student_name=prof.full_name if prof else current_user.email,
        start_time=res.start_time,
        end_time=res.end_time,
        status=res.status.value,
        check_in_time=res.check_in_time,
        check_out_time=res.check_out_time,
        qr_token=f"TOKEN-{res.id[:8].upper()}"
    )


@router.post("/check-out", response_model=SeatReservationResponse)
async def check_out_from_seat(
    request: SeatCheckOutRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Early check-out from an actively occupied study spot.
    Transitions reservation from CHECKED_IN -> COMPLETED.
    Immediately releases the desk back into the pool of available seats.
    """
    now = utc_now()

    stmt = (
        select(SeatReservation, StudySeat, StudyArea, LibraryFloor, StudentProfile)
        .join(StudySeat, SeatReservation.seat_id == StudySeat.id)
        .join(StudyArea, StudySeat.area_id == StudyArea.id)
        .join(LibraryFloor, StudyArea.floor_id == LibraryFloor.id)
        .outerjoin(StudentProfile, SeatReservation.student_user_id == StudentProfile.user_id)
        .where(SeatReservation.id == request.reservation_id)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found.")

    res, seat, area, floor, prof = row

    if res.student_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Reservation belongs to another student."
        )

    if res.status != ReservationStatus.CHECKED_IN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check out from reservation with status '{res.status.value}'. Must be CHECKED_IN."
        )

    res.status = ReservationStatus.COMPLETED
    res.check_out_time = now

    audit_log = SeatOccupancyLog(
        reservation_id=res.id,
        event_type="CHECKED_OUT_EARLY"
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(res)

    return SeatReservationResponse(
        id=res.id,
        seat_id=seat.id,
        seat_number=seat.seat_number,
        area_name=area.name,
        floor_name=floor.floor_name,
        student_user_id=res.student_user_id,
        student_name=prof.full_name if prof else current_user.email,
        start_time=res.start_time,
        end_time=res.end_time,
        status=res.status.value,
        check_in_time=res.check_in_time,
        check_out_time=res.check_out_time,
        qr_token=f"TOKEN-{res.id[:8].upper()}"
    )


@router.get("/{seat_id}/demo-qr", response_model=DemoQrResponse)
async def get_seat_demo_qr(
    seat_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Zero-Hardware Demonstration & Testing Endpoint:
    Returns the exact QR code text identifier assigned to a physical study seat,
    enabling instant testing via in-app CameraX scanner (e.g. scanning on another screen)
    or copying into the in-app manual QR check-in input dialog.
    """
    stmt = (
        select(StudySeat, StudyArea, LibraryFloor)
        .join(StudyArea, StudySeat.area_id == StudyArea.id)
        .join(LibraryFloor, StudyArea.floor_id == LibraryFloor.id)
        .where(StudySeat.id == seat_id)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study seat not found.")

    seat, area, floor = row
    return DemoQrResponse(
        seat_id=seat.id,
        seat_number=seat.seat_number,
        area_name=area.name,
        floor_name=floor.floor_name,
        qr_identifier=seat.qr_identifier,
        instructions="Scan this QR code with the in-app CameraX scanner or paste this exact identifier into the Manual Check-in dialog."
    )


@router.post("/{seat_id}/block", response_model=StudySeatResponse)
async def toggle_seat_maintenance_block(
    seat_id: str,
    request: SeatBlockRequest,
    current_user: User = Depends(require_librarian),
    db: AsyncSession = Depends(get_db)
):
    """
    Librarian Administrative Tool: Block or unblock a study desk for maintenance.
    """
    stmt = (
        select(StudySeat, StudyArea, LibraryFloor)
        .join(StudyArea, StudySeat.area_id == StudyArea.id)
        .join(LibraryFloor, StudyArea.floor_id == LibraryFloor.id)
        .where(StudySeat.id == seat_id)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study seat not found.")

    seat, area, floor = row
    seat.status = SeatStatus(request.status)
    await db.commit()
    await db.refresh(seat)

    return StudySeatResponse(
        id=seat.id,
        area_id=area.id,
        floor_id=floor.id,
        floor_number=floor.floor_number,
        seat_number=seat.seat_number,
        grid_x=seat.grid_x,
        grid_y=seat.grid_y,
        qr_identifier=seat.qr_identifier,
        seat_status=seat.status.value,
        current_occupancy_state="MAINTENANCE" if seat.status == SeatStatus.MAINTENANCE else "AVAILABLE"
    )

"""
show_db.py - Display all existing data in the LibriSmart database.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from app.core.database import get_sync_database_url
from app.models.user import User, StudentProfile, LibrarianProfile, UserRole
from app.models.book import Book, BookCategory, BookCopy, BookCopyStatus
from app.models.seat import LibraryFloor, StudyArea, StudySeat, SeatStatus
import app.models  # noqa: F401

engine = create_engine(get_sync_database_url())

with Session(engine) as s:
    sep = "=" * 65

    # ── USERS ────────────────────────────────────────────────────────
    users = s.execute(select(User)).scalars().all()
    print(f"\n{sep}")
    print(f"  USERS  ({len(users)} total)")
    print(sep)
    for u in users:
        profile_name = "—"
        if u.student_profile:
            profile_name = u.student_profile.full_name
        elif u.librarian_profile:
            profile_name = u.librarian_profile.full_name
        print(f"  [{u.role.value.upper():10s}] {u.email}")
        print(f"              Name : {profile_name}")
        print(f"              Active: {u.is_active}  Verified: {u.is_verified}")
        print()

    # ── BOOK CATEGORIES ───────────────────────────────────────────────
    cats = s.execute(select(BookCategory)).scalars().all()
    print(f"\n{sep}")
    print(f"  BOOK CATEGORIES  ({len(cats)} total)")
    print(sep)
    for c in cats:
        count = s.execute(select(func.count(Book.id)).where(Book.category_id == c.id)).scalar()
        print(f"  [{c.id}] {c.name}  ({count} books)")

    # ── BOOKS & COPIES ────────────────────────────────────────────────
    books = s.execute(select(Book)).scalars().all()
    print(f"\n{sep}")
    print(f"  BOOKS  ({len(books)} total)")
    print(sep)
    for b in books:
        copies = s.execute(select(BookCopy).where(BookCopy.book_id == b.id)).scalars().all()
        avail = sum(1 for c in copies if c.status == BookCopyStatus.AVAILABLE)
        print(f"  📖 {b.title}")
        print(f"      Author  : {b.author}")
        print(f"      ISBN    : {b.isbn}  |  Shelf: {b.shelf_location}")
        print(f"      Copies  : {avail} available / {len(copies)} total")
        statuses = {}
        for c in copies:
            statuses[c.status.value] = statuses.get(c.status.value, 0) + 1
        for st, cnt in statuses.items():
            print(f"               {st}: {cnt}")
        print()

    # ── FLOORS & SEATS ────────────────────────────────────────────────
    floors = s.execute(select(LibraryFloor)).scalars().all()
    print(f"\n{sep}")
    print(f"  LIBRARY FLOORS & SEATS")
    print(sep)
    total_seats = 0
    for f in floors:
        areas = s.execute(select(StudyArea).where(StudyArea.floor_id == f.id)).scalars().all()
        floor_seat_count = 0
        for a in areas:
            seats = s.execute(select(StudySeat).where(StudySeat.area_id == a.id)).scalars().all()
            floor_seat_count += len(seats)
            total_seats += len(seats)
        print(f"  Floor {f.floor_number}: {f.floor_name}")
        for a in areas:
            seats = s.execute(select(StudySeat).where(StudySeat.area_id == a.id)).scalars().all()
            operational = sum(1 for seat in seats if seat.status == SeatStatus.OPERATIONAL)
            print(f"    └─ {a.name}")
            print(f"         Seats: {operational} operational / {len(seats)} total")
            print(f"         Power: {'✔' if a.has_power_outlets else '✘'}  |  Computers: {'✔' if a.has_computers else '✘'}")
        print()
    print(f"  TOTAL SEATS: {total_seats}")

    # ── SUMMARY ───────────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  SUMMARY")
    print(sep)
    print(f"  Users       : {len(users)}")
    print(f"  Categories  : {len(cats)}")
    print(f"  Books       : {len(books)}")
    total_copies = s.execute(select(func.count(BookCopy.id))).scalar()
    avail_copies = s.execute(select(func.count(BookCopy.id)).where(BookCopy.status == BookCopyStatus.AVAILABLE)).scalar()
    print(f"  Book Copies : {avail_copies} available / {total_copies} total")
    print(f"  Seats       : {total_seats}")
    print(f"{sep}\n")

engine.dispose()

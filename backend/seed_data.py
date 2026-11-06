"""
LibriSmart Database Seeder.
Prepopulates essential demo accounts and a rich academic book catalogue.
"""
import sys
import os
from datetime import date

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.core.database import create_all_tables_sync, get_sync_database_url
from app.core.security import get_password_hash
from app.models.user import User, StudentProfile, LibrarianProfile, UserRole
from app.models.book import Book, BookCategory, BookCopy, BookCopyStatus
from app.models.seat import LibraryFloor, StudyArea, StudySeat, SeatStatus
import app.models  # noqa: F401


def seed():
    print("=" * 65, flush=True)
    print("  LibriSmart Database Seeder (Accounts & Academic Catalogue)", flush=True)
    print("=" * 65, flush=True)

    create_all_tables_sync()

    sync_url = get_sync_database_url()
    sync_engine = create_engine(
        sync_url,
        connect_args={"check_same_thread": False} if "sqlite" in sync_url else {}
    )

    with Session(sync_engine) as session:
        # 1. Seed Accounts
        accounts_to_seed = [
            (
                "librarian@librismart.edu",
                "Librarian#2026",
                UserRole.LIBRARIAN,
                False,
                {
                    "staff_id_number": "STAFF-001",
                    "full_name": "Dr. Eleanor Vance",
                    "designation": "Chief Librarian & Campus Archivist"
                }
            ),
            (
                "student@librismart.edu",
                "Student#2026",
                UserRole.STUDENT,
                True,
                {
                    "student_id_number": "STU-2026-001",
                    "full_name": "Alex Rivera",
                    "department": "Computer Science & Engineering",
                    "batch_year": 2026,
                    "phone_number": "+1 555-0199"
                }
            ),
            (
                "reviewer.librarian@librismart-demo.edu",
                "DemoLibrarian#2026",
                UserRole.LIBRARIAN,
                False,
                {
                    "staff_id_number": "REV-LIB-01",
                    "full_name": "Play Reviewer (Librarian)",
                    "designation": "Staff Reviewer"
                }
            ),
            (
                "reviewer.student@librismart-demo.edu",
                "DemoStudent#2026",
                UserRole.STUDENT,
                True,
                {
                    "student_id_number": "REV-STU-01",
                    "full_name": "Play Reviewer (Student)",
                    "department": "Engineering Review",
                    "batch_year": 2026,
                    "phone_number": "+1 555-0100"
                }
            )
        ]

        seeded_users = 0
        for email, password, role, is_student, prof_data in accounts_to_seed:
            existing = session.execute(
                select(User).where(User.email == email)
            ).scalar_one_or_none()

            if not existing:
                user = User(
                    email=email,
                    hashed_password=get_password_hash(password),
                    role=role,
                    is_active=True,
                    is_verified=True
                )
                session.add(user)
                session.flush()

                if is_student:
                    profile = StudentProfile(user_id=user.id, **prof_data)
                    session.add(profile)
                else:
                    profile = LibrarianProfile(user_id=user.id, **prof_data)
                    session.add(profile)

                print(f"[+] Seeded User: {email} ({role.value})", flush=True)
                seeded_users += 1

        # 2. Seed Book Categories
        categories_data = [
            ("Computer Science & Algorithms", "Data structures, algorithmic analysis, computation theory"),
            ("Artificial Intelligence & ML", "Neural networks, deep learning, computer vision, robotics"),
            ("Software Engineering & Architecture", "Clean code, distributed systems, software patterns, microservices"),
            ("Mathematics & Statistics", "Linear algebra, discrete math, probability, calculus"),
            ("Physics & Quantum Computing", "Classical mechanics, quantum information, electromagnetism")
        ]

        category_map = {}
        for cat_name, cat_desc in categories_data:
            existing_cat = session.execute(
                select(BookCategory).where(BookCategory.name == cat_name)
            ).scalar_one_or_none()
            if not existing_cat:
                new_cat = BookCategory(name=cat_name, description=cat_desc)
                session.add(new_cat)
                session.flush()
                category_map[cat_name] = new_cat.id
                print(f"[+] Seeded Category: '{cat_name}'", flush=True)
            else:
                category_map[cat_name] = existing_cat.id

        # 3. Seed Books & Physical Copies
        books_data = [
            {
                "isbn": "978-0262046305",
                "title": "Introduction to Algorithms",
                "author": "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein",
                "publisher": "MIT Press",
                "edition": "4th Edition",
                "publication_year": 2022,
                "category_id": category_map["Computer Science & Algorithms"],
                "language": "English",
                "description": "Comprehensive reference and textbook on algorithms covering sorting, graph algorithms, dynamic programming, and computational complexity.",
                "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780262046305-L.jpg",
                "shelf_location": "Rack A-1, Shelf 03",
                "copies_count": 4
            },
            {
                "isbn": "978-0132350884",
                "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
                "author": "Robert C. Martin",
                "publisher": "Prentice Hall",
                "edition": "1st Edition",
                "publication_year": 2008,
                "category_id": category_map["Software Engineering & Architecture"],
                "language": "English",
                "description": "Practical principles and best practices for writing clean, maintainable, readable, and robust software.",
                "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780132350884-L.jpg",
                "shelf_location": "Rack B-2, Shelf 01",
                "copies_count": 3
            },
            {
                "isbn": "978-0262035613",
                "title": "Deep Learning",
                "author": "Ian Goodfellow, Yoshua Bengio, Aaron Courville",
                "publisher": "MIT Press",
                "edition": "1st Edition",
                "publication_year": 2016,
                "category_id": category_map["Artificial Intelligence & ML"],
                "language": "English",
                "description": "The definitive textbook on deep learning, covering applied math, deep networks, optimization algorithms, and research perspectives.",
                "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780262035613-L.jpg",
                "shelf_location": "Rack C-4, Shelf 02",
                "copies_count": 3
            },
            {
                "isbn": "978-1449373320",
                "title": "Designing Data-Intensive Applications",
                "author": "Martin Kleppmann",
                "publisher": "O'Reilly Media",
                "edition": "1st Edition",
                "publication_year": 2017,
                "category_id": category_map["Software Engineering & Architecture"],
                "language": "English",
                "description": "Key principles and trade-offs of modern data systems: replication, partitioning, transactions, and distributed consensus.",
                "cover_image_url": "https://covers.openlibrary.org/b/isbn/9781449373320-L.jpg",
                "shelf_location": "Rack B-3, Shelf 05",
                "copies_count": 2
            },
            {
                "isbn": "978-0030105678",
                "title": "Linear Algebra and Its Applications",
                "author": "Gilbert Strang",
                "publisher": "Cengage Learning",
                "edition": "4th Edition",
                "publication_year": 2006,
                "category_id": category_map["Mathematics & Statistics"],
                "language": "English",
                "description": "Classic textbook on linear transformations, eigenvalues, singular value decomposition, and computational vector spaces.",
                "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780030105678-L.jpg",
                "shelf_location": "Rack D-1, Shelf 02",
                "copies_count": 3
            },
            {
                "isbn": "978-1119456339",
                "title": "Operating System Concepts",
                "author": "Abraham Silberschatz, Peter B. Galvin, Greg Gagne",
                "publisher": "Wiley",
                "edition": "10th Edition",
                "publication_year": 2018,
                "category_id": category_map["Computer Science & Algorithms"],
                "language": "English",
                "description": "Fundamental concepts of operating systems: process management, concurrency, virtual memory, file systems, and virtualization.",
                "cover_image_url": "https://covers.openlibrary.org/b/isbn/9781119456339-L.jpg",
                "shelf_location": "Rack A-2, Shelf 04",
                "copies_count": 3
            }
        ]

        seeded_books = 0
        total_copies_seeded = 0
        for b_data in books_data:
            existing_book = session.execute(
                select(Book).where(Book.isbn == b_data["isbn"])
            ).scalar_one_or_none()

            if not existing_book:
                copies_cnt = b_data.pop("copies_count")
                clean_isbn = b_data["isbn"].replace("-", "").strip()

                book = Book(
                    **b_data,
                    total_copies_count=copies_cnt,
                    available_copies_count=copies_cnt
                )
                session.add(book)
                session.flush()

                for i in range(1, copies_cnt + 1):
                    barcode = f"BAR-{clean_isbn[-6:]}-C{i:02d}"
                    copy = BookCopy(
                        book_id=book.id,
                        barcode=barcode,
                        copy_number=i,
                        status=BookCopyStatus.AVAILABLE,
                        condition_notes="Excellent - Original Edition",
                        acquired_date=date.today()
                    )
                    session.add(copy)
                    total_copies_seeded += 1

                print(f"[+] Seeded Book: '{book.title}' ({copies_cnt} physical copies)", flush=True)
                seeded_books += 1

        # 4. Seed Campus Library Floors, Study Zones & 2D Seats
        floors_config = [
            {
                "floor_number": 0,
                "floor_name": "Ground Floor - Media & Collaborative Hub",
                "areas": [
                    {
                        "name": "Discussion & Group Study Zone",
                        "noise_policy": "MODERATE_COLLABORATIVE",
                        "has_power_outlets": True,
                        "has_computers": False,
                        "rows": 3,
                        "cols": 4,
                        "prefix": "G"
                    },
                    {
                        "name": "Computer Terminals & Research",
                        "noise_policy": "MODERATE_COLLABORATIVE",
                        "has_power_outlets": True,
                        "has_computers": True,
                        "rows": 2,
                        "cols": 4,
                        "prefix": "C"
                    }
                ]
            },
            {
                "floor_number": 1,
                "floor_name": "First Floor - Silent Study & Individual Research",
                "areas": [
                    {
                        "name": "Silent Reading Hall",
                        "noise_policy": "SILENT",
                        "has_power_outlets": True,
                        "has_computers": False,
                        "rows": 3,
                        "cols": 4,
                        "prefix": "S"
                    },
                    {
                        "name": "Individual Research Pods",
                        "noise_policy": "SILENT",
                        "has_power_outlets": True,
                        "has_computers": False,
                        "rows": 2,
                        "cols": 4,
                        "prefix": "P"
                    }
                ]
            }
        ]

        total_seats_seeded = 0
        for f_data in floors_config:
            existing_floor = session.execute(
                select(LibraryFloor).where(LibraryFloor.floor_number == f_data["floor_number"])
            ).scalar_one_or_none()

            if not existing_floor:
                floor = LibraryFloor(
                    floor_number=f_data["floor_number"],
                    floor_name=f_data["floor_name"],
                    is_active=True
                )
                session.add(floor)
                session.flush()

                for a_data in f_data["areas"]:
                    area = StudyArea(
                        floor_id=floor.id,
                        name=a_data["name"],
                        noise_policy=a_data["noise_policy"],
                        has_power_outlets=a_data["has_power_outlets"],
                        has_computers=a_data["has_computers"]
                    )
                    session.add(area)
                    session.flush()

                    rows = a_data["rows"]
                    cols = a_data["cols"]
                    prefix = a_data["prefix"]
                    seat_num = 1

                    for r in range(rows):
                        for c in range(cols):
                            seat_str = f"{prefix}-{seat_num:02d}"
                            qr_id = f"QR-SEAT-{prefix}{seat_num:02d}-{floor.floor_number}"
                            seat = StudySeat(
                                area_id=area.id,
                                seat_number=seat_str,
                                grid_x=c,
                                grid_y=r,
                                qr_identifier=qr_id,
                                status=SeatStatus.OPERATIONAL
                            )
                            session.add(seat)
                            seat_num += 1
                            total_seats_seeded += 1

                print(f"[+] Seeded Floor {floor.floor_number}: '{floor.floor_name}' with 2 study areas", flush=True)

        session.commit()

    sync_engine.dispose()
    print("\n" + "=" * 65, flush=True)
    print(f"  [SUCCESS] Catalogue seeding complete! ({seeded_books} books, {total_copies_seeded} copies)", flush=True)
    print("=" * 65, flush=True)


if __name__ == "__main__":
    seed()

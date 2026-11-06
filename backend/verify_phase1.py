"""
LibriSmart Phase 1 Verification Script.
Validates database engine connectivity, table creation, and model registration.
"""
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect
from app.core.config import settings
from app.core.database import Base, create_all_tables_sync, get_sync_database_url
import app.models  # Registers all models with Base.metadata


def verify():
    print("=" * 65, flush=True)
    print("  LibriSmart Phase 1: Database Scaffolding Verification", flush=True)
    print("=" * 65, flush=True)

    print(f"[*] App Name:        {settings.APP_NAME}", flush=True)
    print(f"[*] Environment:     {settings.ENVIRONMENT}", flush=True)
    print(f"[*] Async DB URL:    {settings.DATABASE_URL}", flush=True)
    print(f"[*] Sync DB URL:     {get_sync_database_url()}", flush=True)

    print("\n[*] Creating all database tables via SQLAlchemy metadata...", flush=True)
    create_all_tables_sync()
    print("[+] Table creation completed successfully.", flush=True)

    # Inspect tables in the database
    sync_url = get_sync_database_url()
    sync_engine = create_engine(
        sync_url,
        connect_args={"check_same_thread": False} if "sqlite" in sync_url else {}
    )
    inspector = inspect(sync_engine)
    discovered_tables = inspector.get_table_names()
    sync_engine.dispose()

    print(f"\n[+] Total tables discovered in database: {len(discovered_tables)}", flush=True)
    for idx, table_name in enumerate(sorted(discovered_tables), start=1):
        print(f"    {idx:2d}. {table_name}", flush=True)

    expected_tables = {
        "users",
        "student_profiles",
        "librarian_profiles",
        "book_categories",
        "books",
        "book_copies",
        "book_loans",
        "fine_records",
        "fine_payments",
        "book_waitlists",
        "library_floors",
        "study_areas",
        "study_seats",
        "seat_reservations",
        "seat_occupancy_logs",
        "notifications",
        "wishlists",
        "book_reports",
        "library_settings"
    }

    missing_tables = expected_tables - set(discovered_tables)
    if missing_tables:
        print(f"\n[-] ERROR: Missing expected tables: {missing_tables}", flush=True)
        sys.exit(1)

    print("\n" + "=" * 65, flush=True)
    print("  [SUCCESS] All 19 LibriSmart Phase 1 tables verified & operational!", flush=True)
    print("=" * 65, flush=True)


if __name__ == "__main__":
    verify()

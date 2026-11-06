"""
cleanup_users.py - Remove all users from Supabase except the primary librarian.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session
from app.core.database import get_sync_database_url
from app.models.user import User, StudentProfile, LibrarianProfile, UserRole
import app.models  # noqa: F401

KEEP_EMAIL = "librarian@librismart.edu"

engine = create_engine(get_sync_database_url())

with Session(engine) as s:
    # Find the librarian to keep
    librarian = s.execute(select(User).where(User.email == KEEP_EMAIL)).scalar_one_or_none()
    if not librarian:
        print(f"[!] ERROR: '{KEEP_EMAIL}' not found! Aborting.")
        sys.exit(1)

    print(f"[✔] Keeping: {librarian.email} (ID: {librarian.id})")

    # Find all users to delete
    to_delete = s.execute(select(User).where(User.email != KEEP_EMAIL)).scalars().all()
    print(f"\n[*] Removing {len(to_delete)} user(s):")
    for u in to_delete:
        print(f"    - {u.email} ({u.role.value})")

    # Delete student & librarian profiles for those users
    ids_to_delete = [u.id for u in to_delete]
    for uid in ids_to_delete:
        sp = s.execute(select(StudentProfile).where(StudentProfile.user_id == uid)).scalar_one_or_none()
        if sp:
            s.delete(sp)
        lp = s.execute(select(LibrarianProfile).where(LibrarianProfile.user_id == uid)).scalar_one_or_none()
        if lp:
            s.delete(lp)

    s.flush()

    # Delete the users
    for u in to_delete:
        s.delete(u)

    s.commit()
    print(f"\n[✔] Done! Only '{KEEP_EMAIL}' remains in the database.")

engine.dispose()

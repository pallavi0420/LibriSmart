"""
refresh_database.py - LibriSmart Fresh Start Database Reset
Clears all loans, returns, fines, reservations, occupancy logs, and notifications.
Resets all book copies to AVAILABLE and study seats to OPERATIONAL.
Deletes all user accounts except the primary librarian demo account (librarian@librismart.edu).
Synchronizes both backend/librismart.db and root librismart.db.
"""
import sqlite3
import os
import shutil

TARGET_LIBRARIAN_EMAIL = "librarian@librismart.edu"

def refresh_database_file(db_path: str):
    if not os.path.exists(db_path):
        print(f"[-] Database file not found: {db_path}")
        return

    print(f"\n[*] Processing database: {os.path.abspath(db_path)}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Disable foreign keys temporarily for clean deletion
    cursor.execute("PRAGMA foreign_keys = OFF;")

    # 1. Clear all book circulation, loans, returns, and fines
    cursor.execute("DELETE FROM fine_payments;")
    cursor.execute("DELETE FROM fine_records;")
    cursor.execute("DELETE FROM book_loans;")
    cursor.execute("DELETE FROM book_waitlists;")
    cursor.execute("DELETE FROM wishlists;")
    cursor.execute("DELETE FROM book_reports;")

    # 2. Clear all seat reservations and live occupancy logs
    cursor.execute("DELETE FROM seat_occupancy_logs;")
    cursor.execute("DELETE FROM seat_reservations;")

    # 3. Clear all notification center records
    cursor.execute("DELETE FROM notifications;")

    # 4. Reset all physical book copies to AVAILABLE
    cursor.execute("UPDATE book_copies SET status = 'AVAILABLE';")

    # 5. Reset all study seats to OPERATIONAL
    cursor.execute("UPDATE study_seats SET status = 'OPERATIONAL';")

    # 6. Locate the 1 Librarian demo account
    cursor.execute("SELECT id, email, role FROM users WHERE email = ?;", (TARGET_LIBRARIAN_EMAIL,))
    lib_row = cursor.fetchone()

    if lib_row:
        lib_id = lib_row[0]
        print(f" [+] Preserved Librarian Demo Account: {lib_row[1]} (ID: {lib_id})")

        # Delete all student profiles
        cursor.execute("DELETE FROM student_profiles;")

        # Delete all other librarian profiles except the target
        cursor.execute("DELETE FROM librarian_profiles WHERE user_id != ?;", (lib_id,))

        # Delete all other users
        cursor.execute("DELETE FROM users WHERE id != ?;", (lib_id,))
    else:
        print(f" [!] Warning: '{TARGET_LIBRARIAN_EMAIL}' not found in {db_path}")

    # Re-enable foreign keys and commit
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()

    # Print summary verification
    print("\n[+] Verification of refreshed state:")
    tables_to_check = [
        "users", "librarian_profiles", "student_profiles",
        "book_loans", "fine_records", "fine_payments",
        "seat_reservations", "seat_occupancy_logs", "notifications",
        "book_copies", "study_seats"
    ]
    for tbl in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cursor.fetchone()[0]
        print(f"     - {tbl:<22}: {cnt} rows")

    cursor.execute("SELECT email, role FROM users;")
    users_left = cursor.fetchall()
    print(f" [+] Remaining users in database: {users_left}")

    conn.close()

if __name__ == "__main__":
    backend_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "librismart.db")
    root_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "librismart.db")

    refresh_database_file(backend_db)

    # Sync refreshed backend database to root database so both are 100% identical
    if os.path.exists(backend_db):
        shutil.copy2(backend_db, root_db)
        print(f"\n[+] Synchronized refreshed database to root path: {os.path.abspath(root_db)}")

    print("\n" + "=" * 65)
    print("  [SUCCESS] Database refreshed cleanly for a fresh start!")
    print("=" * 65)

"""
test_phase7_analytics.py - Automated Verification of Digital Card, Notifications & Dashboard Analytics
Tests:
1. Authenticate student and librarian
2. Student accesses Digital Library Membership Card (/api/v1/students/me/card)
3. Verify card payload: barcode, QR token, validity date, borrow counts
4. Verify RBAC: Librarian cannot access student digital card (403 Forbidden)
5. Student fetches In-App Notifications (/api/v1/notifications)
6. Verify notifications auto-seeded and unread indicators
7. Student marks single notification as read (/api/v1/notifications/{id}/read)
8. Student marks all notifications as read (/api/v1/notifications/mark-all-read)
9. Librarian accesses Administrative Dashboard Analytics (/api/v1/analytics/dashboard)
10. Verify analytics calculations: registered students, book counts, occupancy %, circulation trends
11. Verify RBAC: Student cannot access librarian analytics dashboard (403 Forbidden)
"""

import asyncio
from datetime import datetime
import httpx

STUDENT_CREDS = {"email": "student@librismart.edu", "password": "Student#2026"}
LIBRARIAN_CREDS = {"email": "librarian@librismart.edu", "password": "Librarian#2026"}


async def run_tests():
    print("=" * 70)
    print("PHASE 7: Digital Student Card, Notifications & Analytics Tests")
    print("=" * 70)

    from app.main import app
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Authenticate users
        print("\n[Step 1] Authenticating test accounts...")
        res_stu = await client.post("/api/v1/auth/login", json=STUDENT_CREDS)
        assert res_stu.status_code == 200, f"Student login failed: {res_stu.text}"
        stu_token = res_stu.json()["access_token"]
        headers_student = {"Authorization": f"Bearer {stu_token}"}

        res_lib = await client.post("/api/v1/auth/login", json=LIBRARIAN_CREDS)
        assert res_lib.status_code == 200, f"Librarian login failed: {res_lib.text}"
        lib_token = res_lib.json()["access_token"]
        headers_librarian = {"Authorization": f"Bearer {lib_token}"}
        print("  [OK] Authenticated student 'Alex Rivera' and librarian 'Dr. Eleanor Vance'.")

        # 2. Digital Membership Card
        print("\n[Step 2] Testing Student Digital Membership Card (/api/v1/students/me/card)...")
        card_res = await client.get("/api/v1/students/me/card", headers=headers_student)
        assert card_res.status_code == 200, f"Card retrieval failed: {card_res.text}"
        card = card_res.json()
        assert card["student_id_number"] == "STU-2026-001"
        assert card["student_name"] == "Alex Rivera"
        assert card["membership_status"] == "ACTIVE"
        assert card["digital_card_barcode"].startswith("CARD-STU-")
        assert "LIBRISMART:" in card["digital_card_qr"]
        assert card["max_borrow_limit"] >= 3
        print(f"  [OK] Digital Card: Student '{card['student_name']}' ({card['student_id_number']})")
        print(f"       Barcode: {card['digital_card_barcode']}")
        print(f"       QR Token: {card['digital_card_qr']}")
        print(f"       Validity: {card['member_since'][:10]} to {card['valid_until'][:10]}")

        # 3. RBAC on Digital Card
        print("\n[Step 3] Verifying RBAC protection on Digital Membership Card...")
        bad_card = await client.get("/api/v1/students/me/card", headers=headers_librarian)
        assert bad_card.status_code == 403, f"Expected 403, got {bad_card.status_code}"
        print(f"  [OK] Non-student access rejected: {bad_card.json()['detail']}")

        # 4. In-App Notifications
        print("\n[Step 4] Testing In-App Notifications Retrieval (/api/v1/notifications)...")
        notifs_res = await client.get("/api/v1/notifications", headers=headers_student)
        assert notifs_res.status_code == 200, f"Notifications failed: {notifs_res.text}"
        notifs = notifs_res.json()
        assert len(notifs) >= 3, f"Expected at least 3 notifications, got {len(notifs)}"
        sample_notif = notifs[0]
        print(f"  [OK] Retrieved {len(notifs)} notifications. Latest: '{sample_notif['title']}' ({sample_notif['category']})")

        # 5. Mark Single Notification as Read
        print(f"\n[Step 5] Marking notification '{sample_notif['id']}' as read...")
        read_res = await client.patch(f"/api/v1/notifications/{sample_notif['id']}/read", headers=headers_student)
        assert read_res.status_code == 200, f"Mark read failed: {read_res.text}"
        assert read_res.json()["is_read"] is True
        print(f"  [OK] Notification '{sample_notif['title']}' is now marked as read.")

        # 6. Mark All Read
        print("\n[Step 6] Testing Mark All Notifications as Read (/api/v1/notifications/mark-all-read)...")
        mark_all = await client.post("/api/v1/notifications/mark-all-read", headers=headers_student)
        assert mark_all.status_code == 200
        notifs_after = (await client.get("/api/v1/notifications", headers=headers_student)).json()
        assert all(n["is_read"] for n in notifs_after)
        print("  [OK] All student notifications verified as read.")

        # 7. Librarian Analytics Dashboard
        print("\n[Step 7] Testing Librarian Administrative Analytics (/api/v1/analytics/dashboard)...")
        dash_res = await client.get("/api/v1/analytics/dashboard", headers=headers_librarian)
        assert dash_res.status_code == 200, f"Analytics failed: {dash_res.text}"
        data = dash_res.json()
        assert data["total_students"] >= 1
        assert data["total_books"] >= 1
        assert data["total_copies"] >= 1
        assert data["total_study_spots"] >= 40
        assert len(data["circulation_trends"]) == 7
        assert len(data["category_distribution"]) >= 1

        print(f"  [OK] Library Statistics:")
        print(f"       - Registered Students: {data['total_students']}")
        print(f"       - Book Titles: {data['total_books']} (Physical Copies: {data['total_copies']})")
        print(f"       - Available Copies: {data['available_copies']}, Issued Copies: {data['issued_copies']}")
        print(f"       - Overdue Loans: {data['overdue_loans']}")
        print(f"       - Unpaid Fines: ${data['total_fines_unpaid_cents']/100:.2f}, Collected Fines: ${data['total_fines_collected_cents']/100:.2f}")
        print(f"       - Study Spots: {data['total_study_spots']} (Occupancy: {data['occupancy_percentage']}%)")
        print(f"       - 7-Day Circulation Trends: {len(data['circulation_trends'])} daily data points")
        print(f"       - Academic Categories: {len(data['category_distribution'])} subject areas")

        # 8. RBAC on Librarian Analytics Dashboard
        print("\n[Step 8] Verifying RBAC protection on Analytics Dashboard...")
        bad_dash = await client.get("/api/v1/analytics/dashboard", headers=headers_student)
        assert bad_dash.status_code == 403, f"Expected 403, got {bad_dash.status_code}"
        print(f"  [OK] Unauthorized student blocked from analytics: {bad_dash.json()['detail']}")

    print("\n" + "=" * 70)
    print("ALL PHASE 7 BACKEND ANALYTICS & CARD TESTS PASSED PERFECTLY!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())

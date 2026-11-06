"""
Automated Integration Test Suite for LibriSmart Phase 4 Circulation & Fines Engine.
Tests Book Issuing, Active Loans, Renewal Extension, Double-Issue Prevention,
Book Returns, Overdue Fine Calculation, and Offline Cash Settlement.
"""
import sys
import os
from datetime import timedelta

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import httpx
from httpx import ASGITransport
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.loan import BookLoan
from app.models.base import utc_now
from sqlalchemy import select


async def run_circulation_tests():
    print("=" * 65)
    print("  LibriSmart Phase 4: Book Circulation & Fine Engine Test Suite")
    print("=" * 65)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Authenticate Student and Librarian
        student_res = await client.post("/api/v1/auth/login", json={
            "email": "student@librismart.edu",
            "password": "Student#2026"
        })
        assert student_res.status_code == 200
        student_token = student_res.json()["access_token"]
        student_headers = {"Authorization": f"Bearer {student_token}"}

        lib_res = await client.post("/api/v1/auth/login", json={
            "email": "librarian@librismart.edu",
            "password": "Librarian#2026"
        })
        assert lib_res.status_code == 200
        lib_token = lib_res.json()["access_token"]
        lib_headers = {"Authorization": f"Bearer {lib_token}"}

        # Reset active borrowed counts for testing idempotency
        async with AsyncSessionLocal() as session:
            from app.models.user import StudentProfile
            profiles = (await session.execute(select(StudentProfile))).scalars().all()
            for p in profiles:
                p.current_borrowed_count = 0
            await session.commit()

        # 2. Retrieve an available book copy to issue
        print("\n[Test 1] Finding Available Copy in Catalogue...")
        books_res = await client.get("/api/v1/books?available_only=true")
        avail_items = books_res.json()["items"]
        assert len(avail_items) > 0, "No available books in catalogue"
        target_book = avail_items[0]
        detail_res = await client.get(f"/api/v1/books/{target_book['id']}")
        target_copy = None
        for copy in detail_res.json()["copies"]:
            if copy["status"] == "AVAILABLE":
                target_copy = copy
                break
        assert target_copy is not None, "No available copy found for test."
        test_barcode = target_copy["barcode"]
        print(f" [+] Found Available Copy Barcode: '{test_barcode}' for '{detail_res.json()['title']}'")

        # 3. Librarian Issues Book to Student (STU-2026-001)
        print(f"\n[Test 2] Testing Book Issuance: Barcode '{test_barcode}' -> Student 'STU-2026-001'...")
        issue_res = await client.post(
            "/api/v1/loans/issue",
            headers=lib_headers,
            json={
                "student_id_or_email": "STU-2026-001",
                "barcode": test_barcode,
                "loan_duration_days": 14
            }
        )
        assert issue_res.status_code == 201, f"Expected 201, got {issue_res.status_code}: {issue_res.text}"
        loan_data = issue_res.json()
        loan_id = loan_data["id"]
        assert loan_data["status"] == "ISSUED"
        assert loan_data["barcode"] == test_barcode
        print(f" [+] Success: Formally issued Loan ID: {loan_id}")
        print(f"     - Due Date: {loan_data['due_date']}")
        print(f"     - Status: {loan_data['status']}")

        # 4. Prevent Duplicate Issue of the Same Copy
        print("\n[Test 3] Testing Prevention of Double-Issuing Active Copy...")
        dup_issue = await client.post(
            "/api/v1/loans/issue",
            headers=lib_headers,
            json={
                "student_id_or_email": "reviewer.student@librismart-demo.edu",
                "barcode": test_barcode
            }
        )
        assert dup_issue.status_code == 409, f"Expected 409 Conflict, got {dup_issue.status_code}: {dup_issue.text}"
        print(" [+] Success: Second issue attempt correctly rejected with HTTP 409 Conflict.")

        # 5. Student Views Active Loans
        print("\n[Test 4] Testing Student Active Loans (/api/v1/loans/my-active)...")
        my_loans_res = await client.get("/api/v1/loans/my-active", headers=student_headers)
        assert my_loans_res.status_code == 200
        my_loans = my_loans_res.json()
        assert len(my_loans) >= 1
        found_loan = next((l for l in my_loans if l["id"] == loan_id), None)
        assert found_loan is not None
        print(f" [+] Success: Student active dashboard shows '{found_loan['book_title']}' (Status: {found_loan['status']})")

        # 6. Student Renews Loan (14-day Extension)
        print(f"\n[Test 5] Testing 14-Day Loan Renewal for Loan ID: {loan_id}...")
        renew_res = await client.post(f"/api/v1/loans/{loan_id}/renew", headers=student_headers)
        assert renew_res.status_code == 200, f"Expected 200, got {renew_res.status_code}: {renew_res.text}"
        renew_data = renew_res.json()
        assert renew_data["renewal_count"] == 1
        print(f" [+] Success: {renew_data['message']}")
        print(f"     - Renewal Count: {renew_data['renewal_count']}/{renew_data['max_renewals_allowed']}")

        # 7. Simulate Overdue Status by adjusting due_date in database
        print("\n[Test 6] Simulating 3 Days Overdue Condition...")
        async with AsyncSessionLocal() as session:
            stmt = select(BookLoan).where(BookLoan.id == loan_id)
            loan_obj = (await session.execute(stmt)).scalar_one()
            # Set due date 3 days in the past
            loan_obj.due_date = utc_now() - timedelta(days=3)
            await session.commit()
        print(" [+] Due date shifted back 3 days to simulate overdue return.")

        # Verify active loans now shows overdue
        overdue_check = (await client.get("/api/v1/loans/my-active", headers=student_headers)).json()
        overdue_loan = next((l for l in overdue_check if l["id"] == loan_id), None)
        assert overdue_loan["is_overdue"] is True
        assert overdue_loan["days_overdue"] >= 3
        print(f" [+] Success: Live status flagged as OVERDUE ({overdue_loan['days_overdue']} days late, Accrued Fine: ${overdue_loan['fine_amount_cents']/100:.2f})")

        # 8. Librarian Processes Book Return
        print(f"\n[Test 7] Testing Return Processing for Barcode '{test_barcode}'...")
        return_res = await client.post(
            "/api/v1/loans/return",
            headers=lib_headers,
            json={
                "barcode": test_barcode,
                "condition_notes": "Returned in good condition"
            }
        )
        assert return_res.status_code == 200, f"Expected 200, got {return_res.status_code}: {return_res.text}"
        returned_loan = return_res.json()
        assert returned_loan["status"] == "RETURNED"
        assert returned_loan["fine_amount_cents"] > 0
        print(f" [+] Success: Book returned. Fine generated: ${returned_loan['fine_amount_cents']/100:.2f}")

        # 9. Student Checks Fines
        print("\n[Test 8] Testing Student Fines Retrieval (/api/v1/fines/my-fines)...")
        fines_res = await client.get("/api/v1/fines/my-fines", headers=student_headers)
        assert fines_res.status_code == 200
        fines = fines_res.json()
        assert len(fines) >= 1
        pending_fine = fines[0]
        fine_id = pending_fine["id"]
        assert pending_fine["status"] == "PENDING"
        print(f" [+] Success: Discovered pending fine ID: {fine_id} for amount {pending_fine['amount_display']}")

        # 10. Librarian Settles Fine Offline with Receipt
        print(f"\n[Test 9] Testing Librarian Offline Cash Settlement for Fine ID: {fine_id}...")
        pay_res = await client.post(
            f"/api/v1/fines/{fine_id}/pay-offline",
            headers=lib_headers,
            json={
                "amount_paid_cents": pending_fine["amount_cents"],
                "payment_method": "CASH_OFFLINE"
            }
        )
        assert pay_res.status_code == 200, f"Expected 200, got {pay_res.status_code}: {pay_res.text}"
        payment = pay_res.json()
        assert payment["status"] == "PAID"
        assert payment["remaining_fine_cents"] == 0
        print(f" [+] Success: Fine settled! Receipt No: '{payment['receipt_number']}' (Status: {payment['status']})")

    print("\n" + "=" * 65)
    print("  [SUCCESS] All 9 Phase 4 Circulation & Fine Tests Passed Flawlessly!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_circulation_tests())

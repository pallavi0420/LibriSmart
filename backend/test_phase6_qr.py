"""
test_phase6_qr.py - Automated Verification of CameraX / QR Code Check-In & Check-Out Workflow
Tests:
1. Fetch demo QR identifier for a seat
2. Reserve a seat for immediate time slot
3. Attempt check-in with invalid/mismatched QR code (400 Bad Request)
4. Attempt check-in by unauthorized student (403 Forbidden)
5. Valid check-in: QR matched, within check-in window (200 OK -> CHECKED_IN)
6. Verify duplicate check-in rejected (400 Bad Request)
7. Verify seat map reflects OCCUPIED status for checked-in desk
8. Early check-out via POST /api/v1/seats/check-out (200 OK -> COMPLETED)
9. Verify seat map returns to AVAILABLE status immediately
10. Verify duplicate checkout rejected (400 Bad Request)
"""

import asyncio
from datetime import datetime, timedelta, timezone
import httpx

BASE_URL = "http://127.0.0.1:8000"
STUDENT_CREDS = {"email": "student@librismart.edu", "password": "Student#2026"}
OTHER_STUDENT_CREDS = {"email": "reviewer.student@librismart-demo.edu", "password": "DemoStudent#2026"}


async def run_tests():
    print("=" * 70)
    print("PHASE 6: CameraX & QR Code Check-In / Check-Out Workflow Tests")
    print("=" * 70)

    # Note: Use ASGITransport to test FastAPI app directly in-process with aiosqlite
    from app.main import app
    from app.core.database import AsyncSessionLocal
    from app.models.seat import SeatReservation
    from sqlalchemy import delete

    # Clean up prior test reservations
    async with AsyncSessionLocal() as session:
        await session.execute(delete(SeatReservation))
        await session.commit()

    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Authenticate student accounts
        print("\n[Step 1] Authenticating test students...")
        res = await client.post("/api/v1/auth/login", json=STUDENT_CREDS)
        assert res.status_code == 200, f"Student login failed: {res.text}"
        student_token = res.json()["access_token"]
        headers_student = {"Authorization": f"Bearer {student_token}"}

        res_other = await client.post("/api/v1/auth/login", json=OTHER_STUDENT_CREDS)
        assert res_other.status_code == 200, f"Other student login failed: {res_other.text}"
        other_token = res_other.json()["access_token"]
        headers_other = {"Authorization": f"Bearer {other_token}"}
        print("  [OK] Authenticated primary student and secondary student.")

        # 2. Query available seats to pick a test seat
        print("\n[Step 2] Finding an available seat...")
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(minutes=2)
        end_time = start_time + timedelta(hours=2)

        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        map_res = await client.get(f"/api/v1/seats/map?start_time={start_str}&end_time={end_str}")
        assert map_res.status_code == 200, f"Map query failed: {map_res.text}"
        seats = map_res.json()
        avail_seats = [s for s in seats if s["current_occupancy_state"] == "AVAILABLE"]
        assert len(avail_seats) > 0, "No available seats found in map!"
        test_seat = avail_seats[0]
        seat_id = test_seat["id"]
        seat_number = test_seat["seat_number"]
        actual_qr = test_seat["qr_identifier"]
        print(f"  [OK] Selected seat {seat_number} (ID: {seat_id}, QR: {actual_qr})")

        # 3. Test GET /{seat_id}/demo-qr
        print("\n[Step 3] Testing GET /api/v1/seats/{seat_id}/demo-qr endpoint...")
        demo_qr_res = await client.get(f"/api/v1/seats/{seat_id}/demo-qr")
        assert demo_qr_res.status_code == 200, f"Demo QR retrieval failed: {demo_qr_res.text}"
        demo_data = demo_qr_res.json()
        assert demo_data["qr_identifier"] == actual_qr
        assert demo_data["seat_number"] == seat_number
        assert "instructions" in demo_data
        print(f"  [OK] Demo QR retrieved successfully: {demo_data['qr_identifier']}")

        # 4. Create advance reservation for primary student
        print("\n[Step 4] Reserving seat for primary student...")
        reserve_payload = {
            "seat_id": seat_id,
            "start_time": start_str,
            "end_time": end_str
        }
        res_book = await client.post("/api/v1/seats/reserve", json=reserve_payload, headers=headers_student)
        assert res_book.status_code == 201, f"Reservation failed: {res_book.text}"
        reservation = res_book.json()
        reservation_id = reservation["id"]
        assert reservation["status"] == "PENDING_CHECKIN"
        print(f"  [OK] Reserved seat. Reservation ID: {reservation_id}, Status: {reservation['status']}")

        # 5. Check-in attempt with WRONG QR code (mismatch test)
        print("\n[Step 5] Testing check-in with invalid/mismatched QR code...")
        bad_checkin = await client.post(
            "/api/v1/seats/check-in",
            json={"reservation_id": reservation_id, "qr_identifier": "QR-WRONG-DESK-999"},
            headers=headers_student
        )
        assert bad_checkin.status_code == 400, f"Expected 400, got {bad_checkin.status_code}: {bad_checkin.text}"
        print(f"  [OK] Mismatched QR code correctly rejected: {bad_checkin.json()['detail']}")

        # 6. Check-in attempt by ANOTHER student (authorization test)
        print("\n[Step 6] Testing check-in attempt by different student...")
        fraud_checkin = await client.post(
            "/api/v1/seats/check-in",
            json={"reservation_id": reservation_id, "qr_identifier": actual_qr},
            headers=headers_other
        )
        assert fraud_checkin.status_code == 403, f"Expected 403, got {fraud_checkin.status_code}: {fraud_checkin.text}"
        print(f"  [OK] Unauthorized check-in blocked: {fraud_checkin.json()['detail']}")

        # 7. Valid Check-in with correct QR code
        print("\n[Step 7] Testing valid QR check-in...")
        valid_checkin = await client.post(
            "/api/v1/seats/check-in",
            json={"reservation_id": reservation_id, "qr_identifier": actual_qr},
            headers=headers_student
        )
        assert valid_checkin.status_code == 200, f"Valid check-in failed: {valid_checkin.text}"
        checked_in_data = valid_checkin.json()
        assert checked_in_data["status"] == "CHECKED_IN"
        assert checked_in_data["check_in_time"] is not None
        print(f"  [OK] Check-in successful! Status: {checked_in_data['status']}, Time: {checked_in_data['check_in_time']}")

        # 8. Duplicate check-in attempt
        print("\n[Step 8] Testing duplicate check-in rejection...")
        dup_checkin = await client.post(
            "/api/v1/seats/check-in",
            json={"reservation_id": reservation_id, "qr_identifier": actual_qr},
            headers=headers_student
        )
        assert dup_checkin.status_code == 400, f"Expected 400, got {dup_checkin.status_code}: {dup_checkin.text}"
        print(f"  [OK] Duplicate check-in rejected: {dup_checkin.json()['detail']}")

        # 9. Verify seat map displays OCCUPIED (Red)
        print("\n[Step 9] Verifying live seat map status reflects OCCUPIED...")
        map_res2 = await client.get(f"/api/v1/seats/map?start_time={start_str}&end_time={end_str}")
        assert map_res2.status_code == 200
        seats2 = map_res2.json()
        updated_seat = next(s for s in seats2 if s["id"] == seat_id)
        assert updated_seat["current_occupancy_state"] == "OCCUPIED", f"Expected OCCUPIED, got {updated_seat['current_occupancy_state']}"
        print(f"  [OK] Desk {seat_number} occupancy state is now OCCUPIED [Red]")

        # 10. Early Checkout via POST /api/v1/seats/check-out
        print("\n[Step 10] Testing early check-out...")
        checkout_res = await client.post(
            "/api/v1/seats/check-out",
            json={"reservation_id": reservation_id},
            headers=headers_student
        )
        assert checkout_res.status_code == 200, f"Check-out failed: {checkout_res.text}"
        checkout_data = checkout_res.json()
        assert checkout_data["status"] == "COMPLETED"
        assert checkout_data["check_out_time"] is not None
        print(f"  [OK] Check-out successful! Status: {checkout_data['status']}, Checkout Time: {checkout_data['check_out_time']}")

        # 11. Verify seat map reflects AVAILABLE (Green) after checkout
        print("\n[Step 11] Verifying seat map reflects AVAILABLE after early checkout...")
        map_res3 = await client.get(f"/api/v1/seats/map?start_time={start_str}&end_time={end_str}")
        assert map_res3.status_code == 200
        seats3 = map_res3.json()
        released_seat = next(s for s in seats3 if s["id"] == seat_id)
        assert released_seat["current_occupancy_state"] == "AVAILABLE", f"Expected AVAILABLE, got {released_seat['current_occupancy_state']}"
        print(f"  [OK] Desk {seat_number} occupancy state reverted to AVAILABLE [Green]")

        # 12. Duplicate checkout attempt
        print("\n[Step 12] Testing duplicate check-out rejection...")
        dup_checkout = await client.post(
            "/api/v1/seats/check-out",
            json={"reservation_id": reservation_id},
            headers=headers_student
        )
        assert dup_checkout.status_code == 400, f"Expected 400, got {dup_checkout.status_code}: {dup_checkout.text}"
        print(f"  [OK] Duplicate check-out rejected: {dup_checkout.json()['detail']}")

    print("\n" + "=" * 70)
    print("ALL 12 PHASE 6 QR CHECK-IN / CHECK-OUT TESTS PASSED PERFECTLY!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())

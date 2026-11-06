"""
Automated Integration Test Suite for LibriSmart Phase 5 Smart Space Reservation Engine.
Tests Occupancy Analytics, Floor/Zone Layout, 2D Seat Map, Double-Booking Prevention,
Overlapping Time-Slot Collision, Cancellation, and Maintenance Blocking.
"""
import sys
import os
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import httpx
from httpx import ASGITransport
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.seat import SeatReservation, ReservationStatus
from sqlalchemy import select, delete


async def run_seat_tests():
    print("=" * 65)
    print("  LibriSmart Phase 5: Space Reservation & Seat Map Test Suite")
    print("=" * 65)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Authenticate Students and Librarian
        student_res = await client.post("/api/v1/auth/login", json={
            "email": "student@librismart.edu",
            "password": "Student#2026"
        })
        student_token = student_res.json()["access_token"]
        student_headers = {"Authorization": f"Bearer {student_token}"}

        student2_res = await client.post("/api/v1/auth/login", json={
            "email": "reviewer.student@librismart-demo.edu",
            "password": "DemoStudent#2026"
        })
        student2_token = student2_res.json()["access_token"]
        student2_headers = {"Authorization": f"Bearer {student2_token}"}

        lib_res = await client.post("/api/v1/auth/login", json={
            "email": "librarian@librismart.edu",
            "password": "Librarian#2026"
        })
        lib_token = lib_res.json()["access_token"]
        lib_headers = {"Authorization": f"Bearer {lib_token}"}

        # Clear prior test reservations for clean testing
        async with AsyncSessionLocal() as session:
            await session.execute(delete(SeatReservation))
            await session.commit()

        # Test 1: Real-time Occupancy Metrics
        print("\n[Test 1] Testing Real-Time Occupancy Metrics (/api/v1/seats/occupancy)...")
        occ_res = await client.get("/api/v1/seats/occupancy")
        assert occ_res.status_code == 200
        occ_data = occ_res.json()
        assert occ_data["total_spots"] >= 40
        print(f" [+] Success: Library study capacity = {occ_data['total_spots']} spots.")
        print(f"     - Available: {occ_data['available_spots']}")
        print(f"     - Occupied: {occ_data['occupied_spots']}")
        print(f"     - Reserved: {occ_data['reserved_spots']}")
        print(f"     - Occupancy Rate: {occ_data['occupancy_percentage']}%")

        # Test 2: Floor & Study Area Hierarchy
        print("\n[Test 2] Testing Floor & Zone Listing (/api/v1/seats/floors)...")
        floors_res = await client.get("/api/v1/seats/floors")
        assert floors_res.status_code == 200
        floors = floors_res.json()
        assert len(floors) >= 2
        print(f" [+] Success: Retrieved {len(floors)} active library floors:")
        for f in floors:
            print(f"     - Floor {f['floor_number']}: '{f['floor_name']}' ({len(f['areas'])} study zones)")
        floor0_id = floors[0]["id"]
        area0_id = floors[0]["areas"][0]["id"]

        # Test 3: Interactive 2D Seat Map Layout
        print(f"\n[Test 3] Testing 2D Visual Seat Map for Floor 0 Area '{floors[0]['areas'][0]['name']}'...")
        map_res = await client.get(f"/api/v1/seats/map?area_id={area0_id}")
        assert map_res.status_code == 200
        seats = map_res.json()
        assert len(seats) >= 12
        first_seat = seats[0]
        seat_id = first_seat["id"]
        seat_num = first_seat["seat_number"]
        print(f" [+] Success: Discovered {len(seats)} seats arranged in 2D coordinates.")
        print(f"     - Sample Seat: ID='{seat_num}', Grid=({first_seat['grid_x']}, {first_seat['grid_y']}), State={first_seat['current_occupancy_state']}")

        # Test 4: Advance Seat Reservation (Tomorrow 10:00 - 12:00)
        print(f"\n[Test 4] Testing Advance Seat Booking for Seat '{seat_num}'...")
        tomorrow_10am = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        tomorrow_12pm = tomorrow_10am + timedelta(hours=2)
        t10_str = tomorrow_10am.strftime("%Y-%m-%dT%H:%M:%SZ")
        t12_str = tomorrow_12pm.strftime("%Y-%m-%dT%H:%M:%SZ")

        reserve_res = await client.post(
            "/api/v1/seats/reserve",
            headers=student_headers,
            json={
                "seat_id": seat_id,
                "start_time": tomorrow_10am.isoformat(),
                "end_time": tomorrow_12pm.isoformat()
            }
        )
        assert reserve_res.status_code == 201, f"Expected 201, got {reserve_res.status_code}: {reserve_res.text}"
        res_data = reserve_res.json()
        reservation_id = res_data["id"]
        assert res_data["seat_number"] == seat_num
        assert res_data["status"] == "PENDING_CHECKIN"
        print(f" [+] Success: Created advance reservation ID: {reservation_id}")
        print(f"     - Time Window: {res_data['start_time']} to {res_data['end_time']}")
        print(f"     - QR Check-in Token: {res_data['qr_token']}")

        # Test 5: Seat Map Reflects RESERVED Status for Booked Slot
        print(f"\n[Test 5] Verifying 2D Seat Map Status During Booked Window...")
        slot_map_res = await client.get(
            f"/api/v1/seats/map?area_id={area0_id}&start_time={t10_str}&end_time={t12_str}"
        )
        assert slot_map_res.status_code == 200, f"Expected 200, got {slot_map_res.status_code}: {slot_map_res.text}"
        slot_seats = slot_map_res.json()
        booked_seat_state = next(s for s in slot_seats if s["id"] == seat_id)
        assert booked_seat_state["current_occupancy_state"] == "RESERVED"
        print(f" [+] Success: Desk '{seat_num}' dynamically colored as 'RESERVED' (Blue) for time slot.")

        # Test 6: Double-Booking Prevention: Another student books overlapping slot (Tomorrow 11:00 - 13:00)
        print("\n[Test 6] Testing Concurrency Defense: Blocking Overlapping Slot (11:00 to 13:00)...")
        overlap_start = tomorrow_10am + timedelta(hours=1)
        overlap_end = overlap_start + timedelta(hours=2)

        collision_res = await client.post(
            "/api/v1/seats/reserve",
            headers=student2_headers,
            json={
                "seat_id": seat_id,
                "start_time": overlap_start.isoformat(),
                "end_time": overlap_end.isoformat()
            }
        )
        assert collision_res.status_code == 409, f"Expected 409 Conflict, got {collision_res.status_code}: {collision_res.text}"
        print(f" [+] Success: Overlapping double-booking rejected with HTTP 409 Conflict.")
        print(f"     - Error Response: {collision_res.json()['detail']}")

        # Test 7: Single Active Booking Limit per Student
        print("\n[Test 7] Testing Policy Limit: Student cannot book two spots at the same time...")
        second_seat_id = seats[1]["id"]
        dup_student_res = await client.post(
            "/api/v1/seats/reserve",
            headers=student_headers,
            json={
                "seat_id": second_seat_id,
                "start_time": tomorrow_10am.isoformat(),
                "end_time": tomorrow_12pm.isoformat()
            }
        )
        assert dup_student_res.status_code == 409, f"Expected 409 Conflict, got {dup_student_res.status_code}"
        print(" [+] Success: Simultaneous multi-desk booking blocked with HTTP 409 Conflict.")

        # Test 8: Student My Reservations List
        print("\n[Test 8] Testing Student My Reservations (/api/v1/seats/my-reservations)...")
        my_res = await client.get("/api/v1/seats/my-reservations", headers=student_headers)
        assert my_res.status_code == 200
        my_list = my_res.json()
        assert len(my_list) >= 1
        assert my_list[0]["id"] == reservation_id
        print(f" [+] Success: Student dashboard shows upcoming reservation for '{my_list[0]['seat_number']}' in '{my_list[0]['area_name']}'.")

        # Test 9: Cancellation & Spot Release
        print(f"\n[Test 9] Testing Reservation Cancellation for ID: {reservation_id}...")
        cancel_res = await client.post(f"/api/v1/seats/{reservation_id}/cancel", headers=student_headers)
        assert cancel_res.status_code == 200
        print(" [+] Success: Reservation cancelled.")

        # Verify seat map immediately updates back to AVAILABLE
        released_map_res = await client.get(
            f"/api/v1/seats/map?area_id={area0_id}&start_time={t10_str}&end_time={t12_str}"
        )
        released_seat = next(s for s in released_map_res.json() if s["id"] == seat_id)
        assert released_seat["current_occupancy_state"] == "AVAILABLE"
        print(f" [+] Success: Desk '{seat_num}' immediately restored to 'AVAILABLE' (Green).")

        # Test 10: Librarian Maintenance Block
        print(f"\n[Test 10] Testing Librarian Maintenance Block on Seat '{seat_num}'...")
        block_res = await client.post(
            f"/api/v1/seats/{seat_id}/block",
            headers=lib_headers,
            json={
                "status": "MAINTENANCE",
                "reason": "Power outlet repair"
            }
        )
        assert block_res.status_code == 200
        blocked_data = block_res.json()
        assert blocked_data["seat_status"] == "MAINTENANCE"
        assert blocked_data["current_occupancy_state"] == "MAINTENANCE"
        print(f" [+] Success: Seat status changed to 'MAINTENANCE' (Grey).")

        # Unblock for cleanliness
        await client.post(f"/api/v1/seats/{seat_id}/block", headers=lib_headers, json={"status": "OPERATIONAL"})

    print("\n" + "=" * 65)
    print("  [SUCCESS] All 10 Phase 5 Space Reservation Tests Passed Flawlessly!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_seat_tests())

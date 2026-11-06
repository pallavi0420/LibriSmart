"""
Automated Integration Test Suite for LibriSmart Phase 2 Authentication.
Tests Registration, Dual-Role Login, Token Refresh, Role Verification, and Account Deletion.
"""
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import httpx
from httpx import ASGITransport
from app.main import app


async def run_auth_tests():
    print("=" * 65)
    print("  LibriSmart Phase 2: Dual-Role Authentication Test Suite")
    print("=" * 65)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Test 1: Student Login with Seeded Account
        print("\n[Test 1] Testing Student Login (student@librismart.edu)...")
        res = await client.post("/api/v1/auth/login", json={
            "email": "student@librismart.edu",
            "password": "Student#2026"
        })
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        student_data = res.json()
        assert student_data["role"] == "STUDENT"
        assert "access_token" in student_data
        assert "refresh_token" in student_data
        student_access_token = student_data["access_token"]
        student_refresh_token = student_data["refresh_token"]
        print(f" [+] Success: Logged in as Student '{student_data['full_name']}' (Role: {student_data['role']})")

        # Test 2: Librarian Login with Seeded Account
        print("\n[Test 2] Testing Librarian Login (librarian@librismart.edu)...")
        res = await client.post("/api/v1/auth/login", json={
            "email": "librarian@librismart.edu",
            "password": "Librarian#2026"
        })
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        lib_data = res.json()
        assert lib_data["role"] == "LIBRARIAN"
        print(f" [+] Success: Logged in as Librarian '{lib_data['full_name']}' (Role: {lib_data['role']})")

        # Test 3: Invalid Password Rejection
        print("\n[Test 3] Testing Invalid Password Rejection...")
        res = await client.post("/api/v1/auth/login", json={
            "email": "student@librismart.edu",
            "password": "WrongPassword123"
        })
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"
        print(" [+] Success: Invalid credentials correctly rejected with HTTP 401 Unauthorized.")

        # Test 4: Token-Protected Profile Access (/api/v1/auth/me)
        print("\n[Test 4] Testing Bearer Token Authentication (/api/v1/auth/me)...")
        res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_access_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        profile = res.json()
        assert profile["email"] == "student@librismart.edu"
        assert profile["student_profile"]["student_id_number"] == "STU-2026-001"
        print(f" [+] Success: Retrieved profile for Student ID: {profile['student_profile']['student_id_number']}")

        # Test 5: Refresh Token Flow
        print("\n[Test 5] Testing JWT Refresh Token Rotation (/api/v1/auth/refresh)...")
        res = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": student_refresh_token
        })
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        refreshed = res.json()
        assert "access_token" in refreshed
        assert refreshed["access_token"] != student_access_token
        print(" [+] Success: Issued fresh access token via valid refresh token.")

        # Test 6: New Student Self-Registration
        test_email = "new.student@librismart.edu"
        print(f"\n[Test 6] Testing New Student Self-Registration ({test_email})...")
        reg_payload = {
            "email": test_email,
            "password": "SecurePassword#2026",
            "student_id_number": "STU-2026-999",
            "full_name": "Jordan Lee",
            "department": "Biomedical Engineering",
            "batch_year": 2026,
            "phone_number": "+1 555-0987"
        }
        res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
        reg_data = res.json()
        new_student_token = reg_data["access_token"]
        print(f" [+] Success: Created student account '{reg_data['full_name']}' with ID 'STU-2026-999'")

        # Test 7: Duplicate Registration Prevention
        print("\n[Test 7] Testing Duplicate Registration Prevention...")
        res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code == 409, f"Expected 409, got {res.status_code}"
        print(" [+] Success: Duplicate email/student ID rejected with HTTP 409 Conflict.")

        # Test 8: Google Play Mandatory In-App Account Deletion
        print("\n[Test 8] Testing Google Play Mandatory Account Deletion (/api/v1/auth/account)...")
        res = await client.delete(
            "/api/v1/auth/account",
            headers={"Authorization": f"Bearer {new_student_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print(f" [+] Success: {res.json()['message']}")

        # Confirm account was actually deleted
        res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_student_token}"}
        )
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"
        print(" [+] Success: Deleted account can no longer authenticate.")

    print("\n" + "=" * 65)
    print("  [SUCCESS] All 8 Phase 2 Authentication Tests Passed Flawlessly!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_auth_tests())

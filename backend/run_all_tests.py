"""
run_all_tests.py - LibriSmart Full Regression Test Suite
Runs all test modules across Phases 2 through 7 in sequence.
"""

import asyncio
import sys

from test_phase2_auth import run_auth_tests
from test_phase3_books import run_book_tests
from test_phase4_loans import run_circulation_tests
from test_phase5_seats import run_seat_tests
from test_phase6_qr import run_tests as run_qr_tests
from test_phase7_analytics import run_tests as run_analytics_tests


async def main():
    print("*" * 75)
    print("         LIBRISMART COMPREHENSIVE ARCHITECTURAL TEST SUITE")
    print("*" * 75)

    suites = [
        ("Phase 2: Dual-Role Authentication & Google Play Deletion", run_auth_tests),
        ("Phase 3: Book Catalogue, Barcode Minting & Inventory", run_book_tests),
        ("Phase 4: Book Circulation Desk, 14-Day Renewals & Fines", run_circulation_tests),
        ("Phase 5: Study-Spot Reservation Engine & Interactive 2D Seat Map", run_seat_tests),
        ("Phase 6: CameraX & QR Code Attendance Check-In / Check-Out", run_qr_tests),
        ("Phase 7: Digital Student Card, Notifications & Dashboard Analytics", run_analytics_tests),
    ]

    passed = 0
    failed = 0

    for name, test_func in suites:
        print("\n" + "=" * 75)
        print(f"RUNNING: {name}")
        print("=" * 75)
        try:
            await test_func()
            passed += 1
            print(f"\n>>> [PASSED] {name}")
        except Exception as e:
            failed += 1
            print(f"\n>>> [FAILED] {name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "*" * 75)
    print(f"FINAL RESULTS: {passed}/{len(suites)} TEST SUITES PASSED ({failed} FAILED)")
    print("*" * 75)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

"""
Automated Integration Test Suite for LibriSmart Phase 3 Book Catalogue & Inventory.
Tests Search, Category Filtering, Detail Retrieval, Librarian Creation, RBAC, and Physical Copy Barcodes.
"""
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import httpx
from httpx import ASGITransport
from app.main import app


async def run_book_tests():
    print("=" * 65)
    print("  LibriSmart Phase 3: Book Catalogue & Inventory Test Suite")
    print("=" * 65)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Obtain Student and Librarian JWT tokens
        student_res = await client.post("/api/v1/auth/login", json={
            "email": "student@librismart.edu",
            "password": "Student#2026"
        })
        student_token = student_res.json()["access_token"]

        lib_res = await client.post("/api/v1/auth/login", json={
            "email": "librarian@librismart.edu",
            "password": "Librarian#2026"
        })
        lib_token = lib_res.json()["access_token"]

        # Test 1: List Categories
        print("\n[Test 1] Testing Category Listing (/api/v1/books/categories)...")
        cat_res = await client.get("/api/v1/books/categories")
        assert cat_res.status_code == 200, f"Expected 200, got {cat_res.status_code}"
        categories = cat_res.json()
        assert len(categories) >= 5
        print(f" [+] Success: Found {len(categories)} academic categories (e.g. '{categories[0]['name']}')")
        first_cat_id = categories[0]["id"]

        # Test 2: List All Books
        print("\n[Test 2] Testing Browse Catalogue (/api/v1/books)...")
        books_res = await client.get("/api/v1/books")
        assert books_res.status_code == 200
        book_list = books_res.json()
        assert book_list["total"] >= 6
        print(f" [+] Success: Catalogue contains {book_list['total']} titles.")

        # Test 3: Search by Keyword in Title
        print("\n[Test 3] Testing Search Keyword 'Clean Code'...")
        search_res = await client.get("/api/v1/books?q=Clean+Code")
        assert search_res.status_code == 200
        results = search_res.json()["items"]
        assert len(results) >= 1
        assert "Clean Code" in results[0]["title"]
        print(f" [+] Success: Found title '{results[0]['title']}' by author '{results[0]['author']}'")
        sample_book_id = results[0]["id"]

        # Test 4: Search by Author Name
        print("\n[Test 4] Testing Search by Author 'Cormen'...")
        author_res = await client.get("/api/v1/books?q=Cormen")
        assert author_res.status_code == 200
        author_results = author_res.json()["items"]
        assert len(author_results) >= 1
        assert "Algorithms" in author_results[0]["title"]
        print(f" [+] Success: Found algorithms book: '{author_results[0]['title']}'")

        # Test 5: Search by ISBN Number
        print("\n[Test 5] Testing Search by ISBN '1449373320'...")
        isbn_res = await client.get("/api/v1/books?q=1449373320")
        assert isbn_res.status_code == 200
        isbn_results = isbn_res.json()["items"]
        assert len(isbn_results) >= 1
        assert "Data-Intensive" in isbn_results[0]["title"]
        print(f" [+] Success: Found '{isbn_results[0]['title']}' by ISBN")

        # Test 6: Book Details & Physical Barcode Copies
        print(f"\n[Test 6] Testing Book Details & Physical Copies for ID: {sample_book_id}...")
        detail_res = await client.get(f"/api/v1/books/{sample_book_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert "copies" in detail
        assert len(detail["copies"]) >= 1
        assert detail["copies"][0]["barcode"].startswith("BAR-")
        print(f" [+] Success: Book '{detail['title']}' has {len(detail['copies'])} physical copies:")
        for copy in detail["copies"]:
            print(f"     - Copy #{copy['copy_number']}: Barcode={copy['barcode']} (Status={copy['status']})")

        # Test 7: Student Forbidden from Creating Books (RBAC)
        print("\n[Test 7] Testing RBAC Security: Student cannot add books...")
        student_post = await client.post(
            "/api/v1/books",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "isbn": "978-0000000001",
                "title": "Hacker's Handbook",
                "author": "Anonymous",
                "initial_copies_count": 1
            }
        )
        assert student_post.status_code == 403, f"Expected 403, got {student_post.status_code}"
        print(" [+] Success: Student correctly blocked with HTTP 403 Forbidden.")

        # Test 8: Librarian Adds a New Book with Auto Barcodes
        print("\n[Test 8] Testing Librarian Adds New Acquisition...")
        lib_post = await client.post(
            "/api/v1/books",
            headers={"Authorization": f"Bearer {lib_token}"},
            json={
                "isbn": "978-1593279288",
                "title": "Python Crash Course (3rd Edition)",
                "author": "Eric Matthes",
                "publisher": "No Starch Press",
                "edition": "3rd Edition",
                "publication_year": 2023,
                "category_id": first_cat_id,
                "language": "English",
                "description": "A hands-on, project-based introduction to programming with Python.",
                "shelf_location": "Rack A-3, Shelf 01",
                "initial_copies_count": 2
            }
        )
        assert lib_post.status_code == 201, f"Expected 201, got {lib_post.status_code}: {lib_post.text}"
        new_book = lib_post.json()
        new_book_id = new_book["id"]
        assert new_book["total_copies_count"] == 2
        assert len(new_book["copies"]) == 2
        print(f" [+] Success: Created book '{new_book['title']}' with {len(new_book['copies'])} auto-generated barcodes:")
        for copy in new_book["copies"]:
            print(f"     - Copy #{copy['copy_number']}: Barcode={copy['barcode']}")

        # Test 9: Librarian Adds Additional Physical Copy
        print(f"\n[Test 9] Testing Adding Extra Physical Copy to '{new_book['title']}'...")
        add_copy_res = await client.post(
            f"/api/v1/books/{new_book_id}/copies",
            headers={"Authorization": f"Bearer {lib_token}"},
            json={
                "condition_notes": "Donated by Alumni"
            }
        )
        assert add_copy_res.status_code == 201, f"Expected 201, got {add_copy_res.status_code}"
        added_copy = add_copy_res.json()
        assert added_copy["copy_number"] == 3
        print(f" [+] Success: Added copy #{added_copy['copy_number']} with Barcode '{added_copy['barcode']}'")

        # Verify updated counts on book
        updated_detail = (await client.get(f"/api/v1/books/{new_book_id}")).json()
        assert updated_detail["total_copies_count"] == 3
        assert updated_detail["available_copies_count"] == 3
        print(f" [+] Success: Book counts updated to {updated_detail['available_copies_count']}/{updated_detail['total_copies_count']} Available.")

    print("\n" + "=" * 65)
    print("  [SUCCESS] All 9 Phase 3 Book Catalogue Tests Passed Flawlessly!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_book_tests())

import uuid
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import require_librarian
from app.models.book import Book, BookCategory, BookCopy, BookCopyStatus
from app.models.loan import BookLoan, LoanStatus
from app.schemas.book import (
    BookCopyCreate,
    BookCopyResponse,
    BookCreateRequest,
    BookListResponse,
    BookResponse,
    BookUpdateRequest,
    CategoryCreate,
    CategoryResponse
)

router = APIRouter(prefix="/books", tags=["Books & Catalogue"])


@router.get("/categories", response_model=List[CategoryResponse], summary="List all book categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """
    Returns all categories along with the total count of books in each category.
    """
    stmt = (
        select(
            BookCategory.id,
            BookCategory.name,
            BookCategory.description,
            func.count(Book.id).label("book_count")
        )
        .outerjoin(Book, Book.category_id == BookCategory.id)
        .group_by(BookCategory.id)
        .order_by(BookCategory.name.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        CategoryResponse(
            id=row.id,
            name=row.name,
            description=row.description,
            book_count=row.book_count
        )
        for row in rows
    ]


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book category (Librarian only)"
)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _librarian = Depends(require_librarian)
):
    """
    Creates a new book category. Requires Librarian privileges.
    """
    existing_stmt = select(BookCategory).where(
        func.lower(BookCategory.name) == payload.name.strip().lower()
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{payload.name}' already exists."
        )

    category = BookCategory(
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)

    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        book_count=0
    )


@router.get("", response_model=BookListResponse, summary="Search and browse books catalogue")
async def search_books(
    q: Optional[str] = Query(None, description="Search keyword matching title, author, or ISBN"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    available_only: bool = Query(False, description="Filter only books with available copies"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search and filter the book collection with pagination.
    """
    base_query = (
        select(Book)
        .options(
            selectinload(Book.category),
            selectinload(Book.copies)
        )
    )

    count_query = select(func.count(Book.id))

    # Apply keyword search
    if q and q.strip():
        search_term = f"%{q.strip().lower()}%"
        filter_cond = or_(
            func.lower(Book.title).like(search_term),
            func.lower(Book.author).like(search_term),
            func.lower(Book.isbn).like(search_term)
        )
        base_query = base_query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    # Apply category filter
    if category_id is not None:
        base_query = base_query.where(Book.category_id == category_id)
        count_query = count_query.where(Book.category_id == category_id)

    # Apply availability filter
    if available_only:
        base_query = base_query.where(Book.available_copies_count > 0)
        count_query = count_query.where(Book.available_copies_count > 0)

    # Total count
    total = (await db.execute(count_query)).scalar_one()

    # Pagination
    offset = (page - 1) * size
    stmt = base_query.order_by(Book.title.asc()).offset(offset).limit(size)
    books = (await db.execute(stmt)).scalars().all()

    items = []
    for book in books:
        copies_dto = [
            BookCopyResponse(
                id=c.id,
                book_id=c.book_id,
                barcode=c.barcode,
                copy_number=c.copy_number,
                status=c.status.value,
                condition_notes=c.condition_notes,
                acquired_date=str(c.acquired_date) if c.acquired_date else None
            )
            for c in book.copies
        ]
        items.append(
            BookResponse(
                id=book.id,
                isbn=book.isbn,
                title=book.title,
                author=book.author,
                publisher=book.publisher,
                edition=book.edition,
                publication_year=book.publication_year,
                category_id=book.category_id,
                category_name=book.category.name if book.category else None,
                language=book.language,
                description=book.description,
                cover_image_url=book.cover_image_url,
                shelf_location=book.shelf_location,
                total_copies_count=book.total_copies_count,
                available_copies_count=book.available_copies_count,
                copies=copies_dto
            )
        )

    return BookListResponse(
        items=items,
        total=total,
        page=page,
        size=size
    )


@router.get("/{book_id}", response_model=BookResponse, summary="Get book details and physical copies")
async def get_book_details(
    book_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves full details for a book, including its individual barcode-tracked physical copies.
    """
    stmt = (
        select(Book)
        .where(Book.id == book_id)
        .options(
            selectinload(Book.category),
            selectinload(Book.copies)
        )
    )
    book = (await db.execute(stmt)).scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID '{book_id}' not found."
        )

    copies_dto = [
        BookCopyResponse(
            id=c.id,
            book_id=c.book_id,
            barcode=c.barcode,
            copy_number=c.copy_number,
            status=c.status.value,
            condition_notes=c.condition_notes,
            acquired_date=str(c.acquired_date) if c.acquired_date else None
        )
        for c in sorted(book.copies, key=lambda x: x.copy_number)
    ]

    return BookResponse(
        id=book.id,
        isbn=book.isbn,
        title=book.title,
        author=book.author,
        publisher=book.publisher,
        edition=book.edition,
        publication_year=book.publication_year,
        category_id=book.category_id,
        category_name=book.category.name if book.category else None,
        language=book.language,
        description=book.description,
        cover_image_url=book.cover_image_url,
        shelf_location=book.shelf_location,
        total_copies_count=book.total_copies_count,
        available_copies_count=book.available_copies_count,
        copies=copies_dto
    )


@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new book title and generate physical copy barcodes (Librarian only)"
)
async def create_book(
    payload: BookCreateRequest,
    db: AsyncSession = Depends(get_db),
    _librarian = Depends(require_librarian)
):
    """
    Creates a new book catalogue record and automatically generates
    initial physical copies with unique barcodes.
    """
    # 1. Verify category exists if provided
    category_name = None
    if payload.category_id:
        cat_stmt = select(BookCategory).where(BookCategory.id == payload.category_id)
        cat = (await db.execute(cat_stmt)).scalar_one_or_none()
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {payload.category_id} does not exist."
            )
        category_name = cat.name

    # 2. Create Book record
    clean_isbn = payload.isbn.replace("-", "").strip()
    book = Book(
        isbn=payload.isbn.strip(),
        title=payload.title.strip(),
        author=payload.author.strip(),
        publisher=payload.publisher.strip() if payload.publisher else None,
        edition=payload.edition.strip() if payload.edition else None,
        publication_year=payload.publication_year,
        category_id=payload.category_id,
        language=payload.language.strip(),
        description=payload.description.strip() if payload.description else None,
        cover_image_url=payload.cover_image_url.strip() if payload.cover_image_url else None,
        shelf_location=payload.shelf_location.strip() if payload.shelf_location else None,
        total_copies_count=payload.initial_copies_count,
        available_copies_count=payload.initial_copies_count
    )
    db.add(book)
    await db.flush()  # Generates book.id

    # 3. Generate initial physical copy records with unique barcodes
    copies_created = []
    for i in range(1, payload.initial_copies_count + 1):
        unique_suffix = uuid.uuid4().hex[:6].upper()
        barcode = f"LS-{clean_isbn[-6:]}-C{i:02d}-{unique_suffix}"

        copy = BookCopy(
            book_id=book.id,
            barcode=barcode,
            copy_number=i,
            status=BookCopyStatus.AVAILABLE,
            condition_notes="New Acquisition",
            acquired_date=date.today()
        )
        db.add(copy)
        copies_created.append(copy)

    await db.commit()

    copies_dto = [
        BookCopyResponse(
            id=c.id,
            book_id=c.book_id,
            barcode=c.barcode,
            copy_number=c.copy_number,
            status=c.status.value,
            condition_notes=c.condition_notes,
            acquired_date=str(c.acquired_date)
        )
        for c in copies_created
    ]

    return BookResponse(
        id=book.id,
        isbn=book.isbn,
        title=book.title,
        author=book.author,
        publisher=book.publisher,
        edition=book.edition,
        publication_year=book.publication_year,
        category_id=book.category_id,
        category_name=category_name,
        language=book.language,
        description=book.description,
        cover_image_url=book.cover_image_url,
        shelf_location=book.shelf_location,
        total_copies_count=book.total_copies_count,
        available_copies_count=book.available_copies_count,
        copies=copies_dto
    )


@router.put(
    "/{book_id}",
    response_model=BookResponse,
    summary="Update book catalogue details (Librarian only)"
)
async def update_book(
    book_id: str,
    payload: BookUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _librarian = Depends(require_librarian)
):
    """
    Updates book title, description, shelf location, or category.
    """
    stmt = (
        select(Book)
        .where(Book.id == book_id)
        .options(
            selectinload(Book.category),
            selectinload(Book.copies)
        )
    )
    book = (await db.execute(stmt)).scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID '{book_id}' not found."
        )

    if payload.title is not None:
        book.title = payload.title.strip()
    if payload.author is not None:
        book.author = payload.author.strip()
    if payload.publisher is not None:
        book.publisher = payload.publisher.strip()
    if payload.edition is not None:
        book.edition = payload.edition.strip()
    if payload.publication_year is not None:
        book.publication_year = payload.publication_year
    if payload.category_id is not None:
        book.category_id = payload.category_id
    if payload.language is not None:
        book.language = payload.language.strip()
    if payload.description is not None:
        book.description = payload.description.strip()
    if payload.cover_image_url is not None:
        book.cover_image_url = payload.cover_image_url.strip()
    if payload.shelf_location is not None:
        book.shelf_location = payload.shelf_location.strip()

    await db.commit()
    await db.refresh(book)

    copies_dto = [
        BookCopyResponse(
            id=c.id,
            book_id=c.book_id,
            barcode=c.barcode,
            copy_number=c.copy_number,
            status=c.status.value,
            condition_notes=c.condition_notes,
            acquired_date=str(c.acquired_date) if c.acquired_date else None
        )
        for c in book.copies
    ]

    return BookResponse(
        id=book.id,
        isbn=book.isbn,
        title=book.title,
        author=book.author,
        publisher=book.publisher,
        edition=book.edition,
        publication_year=book.publication_year,
        category_id=book.category_id,
        category_name=book.category.name if book.category else None,
        language=book.language,
        description=book.description,
        cover_image_url=book.cover_image_url,
        shelf_location=book.shelf_location,
        total_copies_count=book.total_copies_count,
        available_copies_count=book.available_copies_count,
        copies=copies_dto
    )


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a book catalogue entry (Librarian only)"
)
async def delete_book(
    book_id: str,
    db: AsyncSession = Depends(get_db),
    _librarian = Depends(require_librarian)
):
    """
    Deletes a book from the catalogue. Fails if any copy is currently issued out to a student.
    """
    # Check if any copy is currently issued
    loan_stmt = (
        select(BookLoan)
        .join(BookCopy, BookCopy.id == BookLoan.book_copy_id)
        .where(
            BookCopy.book_id == book_id,
            BookLoan.status.in_([LoanStatus.ISSUED, LoanStatus.OVERDUE])
        )
    )
    active_loans = (await db.execute(loan_stmt)).scalars().all()
    if active_loans:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete book: {len(active_loans)} copies are currently issued to students."
        )

    stmt = select(Book).where(Book.id == book_id)
    book = (await db.execute(stmt)).scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID '{book_id}' not found."
        )

    await db.delete(book)
    await db.commit()

    return {"message": f"Book '{book.title}' and all associated copies deleted successfully."}


@router.post(
    "/{book_id}/copies",
    response_model=BookCopyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an additional physical copy to an existing book (Librarian only)"
)
async def add_book_copy(
    book_id: str,
    payload: BookCopyCreate,
    db: AsyncSession = Depends(get_db),
    _librarian = Depends(require_librarian)
):
    """
    Adds a new physical copy (with a unique barcode) to a book and increments the availability counter.
    """
    stmt = (
        select(Book)
        .where(Book.id == book_id)
        .options(selectinload(Book.copies))
    )
    book = (await db.execute(stmt)).scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID '{book_id}' not found."
        )

    # Determine copy number
    next_number = len(book.copies) + 1 if not payload.copy_number else payload.copy_number

    # Generate or validate barcode
    clean_isbn = book.isbn.replace("-", "").strip()
    if payload.barcode and payload.barcode.strip():
        barcode = payload.barcode.strip()
    else:
        unique_suffix = uuid.uuid4().hex[:6].upper()
        barcode = f"LS-{clean_isbn[-6:]}-C{next_number:02d}-{unique_suffix}"

    # Check for duplicate barcode
    dup_stmt = select(BookCopy).where(BookCopy.barcode == barcode)
    dup = (await db.execute(dup_stmt)).scalar_one_or_none()
    if dup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Barcode '{barcode}' is already assigned to another physical copy."
        )

    copy = BookCopy(
        book_id=book.id,
        barcode=barcode,
        copy_number=next_number,
        status=BookCopyStatus.AVAILABLE,
        condition_notes=payload.condition_notes.strip() if payload.condition_notes else "Added to inventory",
        acquired_date=date.today()
    )
    db.add(copy)

    # Increment book counters
    book.total_copies_count += 1
    book.available_copies_count += 1

    await db.commit()
    await db.refresh(copy)

    return BookCopyResponse(
        id=copy.id,
        book_id=copy.book_id,
        barcode=copy.barcode,
        copy_number=copy.copy_number,
        status=copy.status.value,
        condition_notes=copy.condition_notes,
        acquired_date=str(copy.acquired_date)
    )

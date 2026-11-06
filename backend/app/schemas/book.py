from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    book_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class BookCopyResponse(BaseModel):
    id: str
    book_id: str
    barcode: str
    copy_number: int
    status: str
    condition_notes: Optional[str] = None
    acquired_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BookCopyCreate(BaseModel):
    barcode: Optional[str] = None
    copy_number: Optional[int] = None
    condition_notes: Optional[str] = None


class BookResponse(BaseModel):
    id: str
    isbn: str
    title: str
    author: str
    publisher: Optional[str] = None
    edition: Optional[str] = None
    publication_year: Optional[int] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    language: str = "English"
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    shelf_location: Optional[str] = None
    total_copies_count: int = 0
    available_copies_count: int = 0
    copies: List[BookCopyResponse] = []

    model_config = ConfigDict(from_attributes=True)


class BookCreateRequest(BaseModel):
    isbn: str = Field(..., min_length=5, max_length=20)
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    publisher: Optional[str] = Field(None, max_length=150)
    edition: Optional[str] = Field(None, max_length=50)
    publication_year: Optional[int] = Field(None, ge=1800, le=2100)
    category_id: Optional[int] = None
    language: str = Field("English", max_length=50)
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    shelf_location: Optional[str] = Field(None, max_length=100)
    initial_copies_count: int = Field(1, ge=1, le=20, description="Initial physical copies to generate barcodes for")


class BookUpdateRequest(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    publication_year: Optional[int] = None
    category_id: Optional[int] = None
    language: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    shelf_location: Optional[str] = None


class BookListResponse(BaseModel):
    items: List[BookResponse]
    total: int
    page: int
    size: int

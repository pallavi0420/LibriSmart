import enum
from typing import List, Optional
from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class BookCopyStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ISSUED = "ISSUED"
    RESERVED = "RESERVED"
    DAMAGED = "DAMAGED"
    LOST = "LOST"
    MAINTENANCE = "MAINTENANCE"


class BookCategory(Base, TimestampMixin):
    __tablename__ = "book_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    books: Mapped[List["Book"]] = relationship("Book", back_populates="category")


class Book(Base, TimestampMixin):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    isbn: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    author: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    publisher: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    edition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("book_categories.id", ondelete="SET NULL"),
        nullable=True
    )
    language: Mapped[str] = mapped_column(String(50), default="English", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    shelf_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Denormalized counters for instant catalogue queries
    total_copies_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_copies_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    category: Mapped[Optional["BookCategory"]] = relationship("BookCategory", back_populates="books")
    copies: Mapped[List["BookCopy"]] = relationship(
        "BookCopy",
        back_populates="book",
        cascade="all, delete-orphan"
    )


class BookCopy(Base, TimestampMixin):
    """Represents an individual physical barcode-tracked copy of a book."""
    __tablename__ = "book_copies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    book_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    barcode: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    copy_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[BookCopyStatus] = mapped_column(
        Enum(BookCopyStatus, name="book_copy_status_enum", native_enum=False),
        default=BookCopyStatus.AVAILABLE,
        nullable=False,
        index=True
    )
    condition_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    acquired_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)

    book: Mapped["Book"] = relationship("Book", back_populates="copies")

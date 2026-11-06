import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def generate_uuid() -> str:
    """Generate a clean RFC 4122 UUID v4 string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Returns current datetime with UTC timezone."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Reusable mixin providing created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

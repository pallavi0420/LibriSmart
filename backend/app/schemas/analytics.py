from datetime import datetime
from typing import List
from pydantic import BaseModel


class DailyCirculationPoint(BaseModel):
    date_str: str  # e.g. "Nov 01"
    issues_count: int
    returns_count: int


class CategorySharePoint(BaseModel):
    category_name: str
    books_count: int


class DashboardAnalyticsResponse(BaseModel):
    total_students: int
    total_books: int
    total_copies: int
    available_copies: int
    issued_copies: int
    overdue_loans: int
    total_fines_unpaid_cents: int
    total_fines_collected_cents: int
    total_study_spots: int
    occupied_study_spots: int
    reserved_study_spots: int
    occupancy_percentage: float
    circulation_trends: List[DailyCirculationPoint]
    category_distribution: List[CategorySharePoint]
    generated_at: datetime

    class Config:
        from_attributes = True

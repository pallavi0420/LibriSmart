from fastapi import APIRouter
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.books import router as books_router
from app.api.v1.loans import router as loans_router, fines_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.seats import router as seats_router
from app.api.v1.students import router as students_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(books_router)
api_v1_router.include_router(loans_router)
api_v1_router.include_router(fines_router)
api_v1_router.include_router(seats_router)
api_v1_router.include_router(students_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(analytics_router)

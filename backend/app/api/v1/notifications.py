from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.system import Notification
from app.models.user import User
from app.schemas.notification import NotificationMarkReadResponse, NotificationResponse

router = APIRouter(prefix="/notifications", tags=["In-App Notifications"])


@router.get("", response_model=List[NotificationResponse])
async def get_my_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all in-app notifications for the authenticated user ordered newest first.
    Auto-populates helpful academic onboarding alerts if the inbox is empty.
    """
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    result = await db.execute(stmt)
    notifications = result.scalars().all()

    # Seed initial academic notifications if brand new account
    if not notifications:
        starter_alerts = [
            Notification(
                user_id=current_user.id,
                title="Welcome to LibriSmart Campus Library",
                body="Explore thousands of textbooks, reserve study spots with live seat occupancy, and manage your loans digitally.",
                category="ANNOUNCEMENT",
                is_read=False
            ),
            Notification(
                user_id=current_user.id,
                title="Extended Finals Quiet Study Hours",
                body="Floor 1 Silent Study Zone is open 24/7 during midterm and final examination weeks. Please adhere to the campus noise policy.",
                category="ANNOUNCEMENT",
                is_read=False
            ),
            Notification(
                user_id=current_user.id,
                title="Circulation Guidelines Reminder",
                body="Standard textbook loan duration is 14 days. Eligible books can be renewed once if no other students are on the hold waitlist.",
                category="CIRCULATION",
                is_read=False
            )
        ]
        for alert in starter_alerts:
            db.add(alert)
        await db.commit()

        # Re-fetch
        stmt = (
            select(Notification)
            .where(Notification.user_id == current_user.id)
            .order_by(Notification.created_at.desc())
        )
        notifications = (await db.execute(stmt)).scalars().all()

    return notifications


@router.patch("/{notification_id}/read", response_model=NotificationMarkReadResponse)
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark an individual notification as read.
    """
    stmt = select(Notification).where(Notification.id == notification_id)
    notification = (await db.execute(stmt)).scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )

    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Notification belongs to another user."
        )

    notification.is_read = True
    await db.commit()

    return NotificationMarkReadResponse(
        id=notification.id,
        is_read=True,
        message="Notification marked as read."
    )


@router.post("/mark-all-read")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark all unread notifications as read for the authenticated user.
    """
    stmt = (
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.execute(stmt)
    await db.commit()

    return {"message": "All notifications marked as read."}

from typing import List, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validates Bearer token and returns the authenticated User with profiles loaded.
    Raises HTTP 401 if token is invalid, expired, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    token_type: str = payload.get("type", "")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Access token required."
        )

    user_id: str = payload.get("sub", "")
    if not user_id:
        raise credentials_exception

    # Query user with eager-loaded student and librarian profiles
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.student_profile),
            selectinload(User.librarian_profile)
        )
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Contact library administration."
        )

    return user


def require_role(allowed_roles: Union[UserRole, List[UserRole]]):
    """
    Factory dependency for role-based access control (RBAC).
    Guarantees students cannot invoke librarian endpoints and vice-versa.
    """
    if isinstance(allowed_roles, UserRole):
        roles_list = [allowed_roles]
    else:
        roles_list = allowed_roles

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles_list:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of the following roles: {[r.value for r in roles_list]}"
            )
        return current_user

    return role_checker


# Convenient role-specific dependencies
require_student = require_role([UserRole.STUDENT])
require_librarian = require_role([UserRole.LIBRARIAN, UserRole.ADMIN])

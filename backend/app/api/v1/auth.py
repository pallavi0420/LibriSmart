from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import LibrarianProfile, StudentProfile, User, UserRole
from app.models.loan import BookLoan, FineRecord, FineStatus, LoanStatus
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    StudentProfileData,
    LibrarianProfileData,
    StudentRegisterRequest,
    TokenResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account"
)
async def register_student(
    payload: StudentRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new student, creates their library membership profile,
    and returns initial access & refresh JWT tokens.
    """
    normalized_email = payload.email.lower().strip()

    # 1. Check for duplicate email
    email_stmt = select(User).where(User.email == normalized_email)
    existing_user = (await db.execute(email_stmt)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )

    # 2. Check for duplicate student ID number
    id_stmt = select(StudentProfile).where(StudentProfile.student_id_number == payload.student_id_number.strip())
    existing_id = (await db.execute(id_stmt)).scalar_one_or_none()
    if existing_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student profile with this Student ID Number is already registered."
        )

    # 3. Create User record
    hashed_password = get_password_hash(payload.password)
    user = User(
        email=normalized_email,
        hashed_password=hashed_password,
        role=UserRole.STUDENT,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    await db.flush()  # Populates user.id

    # 4. Create StudentProfile record
    profile = StudentProfile(
        user_id=user.id,
        student_id_number=payload.student_id_number.strip(),
        full_name=payload.full_name.strip(),
        department=payload.department.strip(),
        batch_year=payload.batch_year,
        phone_number=payload.phone_number.strip() if payload.phone_number else None,
        max_borrow_limit=3,
        current_borrowed_count=0,
        is_suspended=False
    )
    db.add(profile)
    await db.commit()

    # 5. Generate JWT tokens
    access_token = create_access_token(subject=user.id, role=user.role.value, email=user.email)
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role.value,
        user_id=user.id,
        email=user.email,
        full_name=payload.full_name.strip()
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain JWT tokens"
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates both Students and Librarians using their institutional email and password.
    """
    normalized_email = payload.email.lower().strip()

    stmt = (
        select(User)
        .where(User.email == normalized_email)
        .options(
            selectinload(User.student_profile),
            selectinload(User.librarian_profile)
        )
    )
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact the library administrator."
        )

    # Determine full name based on role profile
    full_name = "Library User"
    if user.student_profile:
        full_name = user.student_profile.full_name
    elif user.librarian_profile:
        full_name = user.librarian_profile.full_name

    access_token = create_access_token(subject=user.id, role=user.role.value, email=user.email)
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role.value,
        user_id=user.id,
        email=user.email,
        full_name=full_name
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token using a valid refresh token"
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Exchanges a valid refresh token for a fresh short-lived access token.
    """
    token_payload = decode_token(payload.refresh_token)
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    if token_payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected refresh token."
        )

    user_id = token_payload.get("sub")
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.student_profile),
            selectinload(User.librarian_profile)
        )
    )
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active or exists."
        )

    full_name = "Library User"
    if user.student_profile:
        full_name = user.student_profile.full_name
    elif user.librarian_profile:
        full_name = user.librarian_profile.full_name

    new_access_token = create_access_token(subject=user.id, role=user.role.value, email=user.email)
    new_refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        role=user.role.value,
        user_id=user.id,
        email=user.email,
        full_name=full_name
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile and role details"
)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Returns the currently logged-in user profile with role-specific information.
    """
    full_name = "Library User"
    student_data = None
    librarian_data = None

    if current_user.student_profile:
        full_name = current_user.student_profile.full_name
        student_data = StudentProfileData.model_validate(current_user.student_profile)
    elif current_user.librarian_profile:
        full_name = current_user.librarian_profile.full_name
        librarian_data = LibrarianProfileData.model_validate(current_user.librarian_profile)

    return UserProfileResponse(
        user_id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        full_name=full_name,
        student_profile=student_data,
        librarian_profile=librarian_data
    )


@router.delete(
    "/account",
    response_model=MessageResponse,
    summary="Google Play Mandatory: Delete user account and PII"
)
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Google Play Developer Policy requirement:
    Allows students to delete their account directly within the app.
    Validates that no active loans or pending unpaid fines exist before proceeding.
    """
    # 1. Verify user has no active borrowed books
    loan_stmt = select(BookLoan).where(
        BookLoan.student_user_id == current_user.id,
        BookLoan.status.in_([LoanStatus.ISSUED, LoanStatus.REQUESTED, LoanStatus.OVERDUE])
    )
    active_loans = (await db.execute(loan_stmt)).scalars().all()
    if active_loans:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete account: You have {len(active_loans)} active book loan(s) that must be returned first."
        )

    # 2. Verify user has no pending fines
    fine_stmt = select(FineRecord).where(
        FineRecord.student_user_id == current_user.id,
        FineRecord.status == FineStatus.PENDING
    )
    pending_fines = (await db.execute(fine_stmt)).scalars().all()
    if pending_fines:
        total_cents = sum(f.amount_cents for f in pending_fines)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete account: You have outstanding fines amounting to ${total_cents / 100:.2f}."
        )

    # 3. Anonymize/Delete User and cascading profiles
    await db.delete(current_user)
    await db.commit()

    return MessageResponse(message="Your LibriSmart account and associated data have been permanently deleted.")

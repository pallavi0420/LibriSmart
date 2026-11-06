from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    student_id_number: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=150)
    department: str = Field(..., min_length=2, max_length=100)
    batch_year: int = Field(..., ge=2000, le=2100)
    phone_number: Optional[str] = Field(None, max_length=20)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    email: str
    full_name: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class StudentProfileData(BaseModel):
    student_id_number: str
    full_name: str
    department: str
    batch_year: int
    phone_number: Optional[str]
    max_borrow_limit: int
    current_borrowed_count: int
    is_suspended: bool

    model_config = ConfigDict(from_attributes=True)


class LibrarianProfileData(BaseModel):
    staff_id_number: str
    full_name: str
    designation: str

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    role: str
    is_active: bool
    full_name: str
    student_profile: Optional[StudentProfileData] = None
    librarian_profile: Optional[LibrarianProfileData] = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str

package com.librismart.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class LoginRequestDto(
    @SerialName("email") val email: String,
    @SerialName("password") val password: String
)

@Serializable
data class StudentRegisterRequestDto(
    @SerialName("email") val email: String,
    @SerialName("password") val password: String,
    @SerialName("student_id_number") val studentIdNumber: String,
    @SerialName("full_name") val fullName: String,
    @SerialName("department") val department: String,
    @SerialName("batch_year") val batchYear: Int = 2026,
    @SerialName("phone_number") val phoneNumber: String? = null
)

@Serializable
data class TokenResponseDto(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("token_type") val tokenType: String = "bearer",
    @SerialName("role") val role: String,
    @SerialName("user_id") val userId: String,
    @SerialName("email") val email: String,
    @SerialName("full_name") val fullName: String
)

@Serializable
data class RefreshTokenRequestDto(
    @SerialName("refresh_token") val refreshToken: String
)

@Serializable
data class StudentProfileDto(
    @SerialName("student_id_number") val studentIdNumber: String,
    @SerialName("full_name") val fullName: String,
    @SerialName("department") val department: String,
    @SerialName("batch_year") val batchYear: Int,
    @SerialName("phone_number") val phoneNumber: String? = null,
    @SerialName("max_borrow_limit") val maxBorrowLimit: Int = 3,
    @SerialName("current_borrowed_count") val currentBorrowedCount: Int = 0,
    @SerialName("is_suspended") val isSuspended: Boolean = false
)

@Serializable
data class LibrarianProfileDto(
    @SerialName("staff_id_number") val staffIdNumber: String,
    @SerialName("full_name") val fullName: String,
    @SerialName("designation") val designation: String
)

@Serializable
data class UserProfileResponseDto(
    @SerialName("user_id") val userId: String,
    @SerialName("email") val email: String,
    @SerialName("role") val role: String,
    @SerialName("is_active") val isActive: Boolean,
    @SerialName("full_name") val fullName: String,
    @SerialName("student_profile") val studentProfile: StudentProfileDto? = null,
    @SerialName("librarian_profile") val librarianProfile: LibrarianProfileDto? = null
)

@Serializable
data class MessageResponseDto(
    @SerialName("message") val message: String
)

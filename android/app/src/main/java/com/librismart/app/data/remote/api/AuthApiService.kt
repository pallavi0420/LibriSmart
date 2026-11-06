package com.librismart.app.data.remote.api

import com.librismart.app.data.remote.dto.LoginRequestDto
import com.librismart.app.data.remote.dto.MessageResponseDto
import com.librismart.app.data.remote.dto.RefreshTokenRequestDto
import com.librismart.app.data.remote.dto.StudentRegisterRequestDto
import com.librismart.app.data.remote.dto.TokenResponseDto
import com.librismart.app.data.remote.dto.UserProfileResponseDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST

interface AuthApiService {

    @POST("api/v1/auth/login")
    suspend fun login(
        @Body request: LoginRequestDto
    ): Response<TokenResponseDto>

    @POST("api/v1/auth/register")
    suspend fun register(
        @Body request: StudentRegisterRequestDto
    ): Response<TokenResponseDto>

    @POST("api/v1/auth/refresh")
    suspend fun refreshToken(
        @Body request: RefreshTokenRequestDto
    ): Response<TokenResponseDto>

    @GET("api/v1/auth/me")
    suspend fun getProfile(): Response<UserProfileResponseDto>

    @DELETE("api/v1/auth/account")
    suspend fun deleteAccount(): Response<MessageResponseDto>
}

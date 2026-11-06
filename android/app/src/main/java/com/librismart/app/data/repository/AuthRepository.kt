package com.librismart.app.data.repository

import com.librismart.app.core.datastore.UserPreferencesManager
import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.api.AuthApiService
import com.librismart.app.data.remote.dto.LoginRequestDto
import com.librismart.app.data.remote.dto.MessageResponseDto
import com.librismart.app.data.remote.dto.StudentRegisterRequestDto
import com.librismart.app.data.remote.dto.TokenResponseDto
import com.librismart.app.data.remote.dto.UserProfileResponseDto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import org.json.JSONObject

class AuthRepository(
    private val authApiService: AuthApiService,
    private val preferencesManager: UserPreferencesManager
) {

    val userRoleFlow: Flow<String?> = preferencesManager.userRoleFlow
    val fullNameFlow: Flow<String?> = preferencesManager.fullNameFlow
    val isLoggedInFlow: Flow<Boolean> = preferencesManager.isLoggedInFlow

    suspend fun login(email: String, password: String): NetworkResult<TokenResponseDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = authApiService.login(LoginRequestDto(email = email.trim(), password = password))
                if (response.isSuccessful && response.body() != null) {
                    val tokenData = response.body()!!
                    preferencesManager.saveAuthSession(
                        accessToken = tokenData.accessToken,
                        refreshToken = tokenData.refreshToken,
                        role = tokenData.role,
                        userId = tokenData.userId,
                        email = tokenData.email,
                        fullName = tokenData.fullName
                    )
                    NetworkResult.Success(tokenData)
                } else {
                    val errorMsg = parseErrorMessage(response.errorBody()?.string())
                    NetworkResult.Error(errorMsg, response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Unable to connect to LibriSmart server"}")
            }
        }
    }

    suspend fun registerStudent(request: StudentRegisterRequestDto): NetworkResult<TokenResponseDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = authApiService.register(request)
                if (response.isSuccessful && response.body() != null) {
                    val tokenData = response.body()!!
                    preferencesManager.saveAuthSession(
                        accessToken = tokenData.accessToken,
                        refreshToken = tokenData.refreshToken,
                        role = tokenData.role,
                        userId = tokenData.userId,
                        email = tokenData.email,
                        fullName = tokenData.fullName
                    )
                    NetworkResult.Success(tokenData)
                } else {
                    val errorMsg = parseErrorMessage(response.errorBody()?.string())
                    NetworkResult.Error(errorMsg, response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Registration failed"}")
            }
        }
    }

    suspend fun getProfile(): NetworkResult<UserProfileResponseDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = authApiService.getProfile()
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    val errorMsg = parseErrorMessage(response.errorBody()?.string())
                    NetworkResult.Error(errorMsg, response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Failed to fetch profile: ${e.localizedMessage}")
            }
        }
    }

    suspend fun deleteAccount(): NetworkResult<MessageResponseDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = authApiService.deleteAccount()
                if (response.isSuccessful && response.body() != null) {
                    preferencesManager.clearSession()
                    NetworkResult.Success(response.body()!!)
                } else {
                    val errorMsg = parseErrorMessage(response.errorBody()?.string())
                    NetworkResult.Error(errorMsg, response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Account deletion failed: ${e.localizedMessage}")
            }
        }
    }

    suspend fun logout() {
        preferencesManager.clearSession()
    }

    private fun parseErrorMessage(errorBody: String?): String {
        return try {
            if (!errorBody.isNullOrBlank()) {
                val json = JSONObject(errorBody)
                json.optString("detail", "Operation failed. Please try again.")
            } else {
                "An unexpected server error occurred."
            }
        } catch (_: Exception) {
            "An unexpected server error occurred."
        }
    }
}

package com.librismart.app.data.repository

import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.api.NotificationApiService
import com.librismart.app.data.remote.dto.MessageResponseDto
import com.librismart.app.data.remote.dto.NotificationDto
import com.librismart.app.data.remote.dto.NotificationMarkReadDto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

class NotificationRepository(
    private val notificationApiService: NotificationApiService
) {

    suspend fun getNotifications(): NetworkResult<List<NotificationDto>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = notificationApiService.getNotifications()
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to load notifications"}")
            }
        }
    }

    suspend fun markAsRead(notificationId: String): NetworkResult<NotificationMarkReadDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = notificationApiService.markAsRead(notificationId)
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to update notification"}")
            }
        }
    }

    suspend fun markAllAsRead(): NetworkResult<MessageResponseDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = notificationApiService.markAllAsRead()
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to mark all as read"}")
            }
        }
    }

    private fun parseErrorMessage(errorJson: String?): String {
        if (errorJson.isNullOrBlank()) return "Notification action failed."
        return try {
            val json = JSONObject(errorJson)
            json.optString("detail", "Notification action failed.")
        } catch (_: Exception) {
            errorJson
        }
    }
}

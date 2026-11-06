package com.librismart.app.data.repository

import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.api.AnalyticsApiService
import com.librismart.app.data.remote.dto.DashboardAnalyticsDto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

class AnalyticsRepository(
    private val analyticsApiService: AnalyticsApiService
) {

    suspend fun getDashboardAnalytics(): NetworkResult<DashboardAnalyticsDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = analyticsApiService.getDashboardAnalytics()
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to load dashboard analytics"}")
            }
        }
    }

    private fun parseErrorMessage(errorJson: String?): String {
        if (errorJson.isNullOrBlank()) return "Failed to retrieve library analytics."
        return try {
            val json = JSONObject(errorJson)
            json.optString("detail", "Failed to retrieve library analytics.")
        } catch (_: Exception) {
            errorJson
        }
    }
}

package com.librismart.app.data.repository

import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.api.StudentApiService
import com.librismart.app.data.remote.dto.DigitalStudentCardDto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

class StudentCardRepository(
    private val studentApiService: StudentApiService
) {

    suspend fun getMyDigitalCard(): NetworkResult<DigitalStudentCardDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = studentApiService.getMyDigitalCard()
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to load digital student card"}")
            }
        }
    }

    private fun parseErrorMessage(errorJson: String?): String {
        if (errorJson.isNullOrBlank()) return "Failed to retrieve student membership card."
        return try {
            val json = JSONObject(errorJson)
            json.optString("detail", "Failed to retrieve student membership card.")
        } catch (_: Exception) {
            errorJson
        }
    }
}

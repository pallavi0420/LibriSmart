package com.librismart.app.data.repository

import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.api.SeatApiService
import com.librismart.app.data.remote.dto.DemoQrDto
import com.librismart.app.data.remote.dto.FloorDto
import com.librismart.app.data.remote.dto.MessageResponseDto
import com.librismart.app.data.remote.dto.OccupancyDto
import com.librismart.app.data.remote.dto.SeatCheckInRequestDto
import com.librismart.app.data.remote.dto.SeatCheckOutRequestDto
import com.librismart.app.data.remote.dto.SeatReservationDto
import com.librismart.app.data.remote.dto.SeatReserveRequestDto
import com.librismart.app.data.remote.dto.StudySeatDto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

class SeatReservationRepository(
    private val seatApiService: SeatApiService
) {

    suspend fun getOccupancy(): NetworkResult<OccupancyDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = seatApiService.getOccupancy()
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to load library occupancy"}")
            }
        }
    }

    suspend fun getFloors(): NetworkResult<List<FloorDto>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = seatApiService.getFloors()
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to load library floors"}")
            }
        }
    }

    suspend fun getSeatMap(
        floorId: Int? = null,
        areaId: Int? = null,
        startTime: String? = null,
        endTime: String? = null
    ): NetworkResult<List<StudySeatDto>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = seatApiService.getSeatMap(floorId, areaId, startTime, endTime)
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to load seat layout map"}")
            }
        }
    }

    suspend fun reserveSeat(
        seatId: String,
        startTimeIso: String,
        endTimeIso: String
    ): NetworkResult<SeatReservationDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = seatApiService.reserveSeat(
                    SeatReserveRequestDto(seatId = seatId, startTime = startTimeIso, endTime = endTimeIso)
                )
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to reserve study desk"}")
            }
        }
    }

    suspend fun cancelReservation(reservationId: String): NetworkResult<MessageResponseDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = seatApiService.cancelReservation(reservationId)
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to cancel reservation"}")
            }
        }
    }

    suspend fun getMyReservations(): NetworkResult<List<SeatReservationDto>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = seatApiService.getMyReservations()
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to load reservations"}")
            }
        }
    }

    suspend fun checkIn(reservationId: String, qrIdentifier: String): NetworkResult<SeatReservationDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = seatApiService.checkIn(
                    SeatCheckInRequestDto(reservationId = reservationId, qrIdentifier = qrIdentifier)
                )
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "QR Check-in failed"}")
            }
        }
    }

    suspend fun checkOut(reservationId: String): NetworkResult<SeatReservationDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = seatApiService.checkOut(
                    SeatCheckOutRequestDto(reservationId = reservationId)
                )
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Desk check-out failed"}")
            }
        }
    }

    suspend fun getDemoQr(seatId: String): NetworkResult<DemoQrDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = seatApiService.getDemoQr(seatId)
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to fetch demo QR"}")
            }
        }
    }

    private fun parseErrorMessage(errorJson: String?): String {
        if (errorJson.isNullOrBlank()) return "Space reservation failed. Please try again."
        return try {
            val json = JSONObject(errorJson)
            json.optString("detail", "Space reservation failed.")
        } catch (_: Exception) {
            errorJson
        }
    }
}

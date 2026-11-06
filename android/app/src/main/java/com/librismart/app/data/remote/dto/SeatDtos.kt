package com.librismart.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class OccupancyDto(
    @SerialName("total_spots") val totalSpots: Int,
    @SerialName("occupied_spots") val occupiedSpots: Int,
    @SerialName("reserved_spots") val reservedSpots: Int,
    @SerialName("available_spots") val availableSpots: Int,
    @SerialName("maintenance_spots") val maintenanceSpots: Int,
    @SerialName("occupancy_percentage") val occupancyPercentage: Double,
    @SerialName("updated_at") val updatedAt: String
)

@Serializable
data class StudySeatDto(
    @SerialName("id") val id: String,
    @SerialName("area_id") val areaId: Int,
    @SerialName("floor_id") val floorId: Int,
    @SerialName("floor_number") val floorNumber: Int,
    @SerialName("seat_number") val seatNumber: String,
    @SerialName("grid_x") val gridX: Int,
    @SerialName("grid_y") val gridY: Int,
    @SerialName("qr_identifier") val qrIdentifier: String,
    @SerialName("seat_status") val seatStatus: String,
    @SerialName("current_occupancy_state") val currentOccupancyState: String, // "AVAILABLE", "OCCUPIED", "RESERVED", "MAINTENANCE"
    @SerialName("active_reservation_id") val activeReservationId: String? = null
)

@Serializable
data class StudyAreaDto(
    @SerialName("id") val id: Int,
    @SerialName("floor_id") val floorId: Int,
    @SerialName("name") val name: String,
    @SerialName("noise_policy") val noisePolicy: String,
    @SerialName("has_power_outlets") val hasPowerOutlets: Boolean,
    @SerialName("has_computers") val hasComputers: Boolean,
    @SerialName("total_seats_count") val totalSeatsCount: Int = 0,
    @SerialName("available_seats_count") val availableSeatsCount: Int = 0
)

@Serializable
data class FloorDto(
    @SerialName("id") val id: Int,
    @SerialName("floor_number") val floorNumber: Int,
    @SerialName("floor_name") val floorName: String,
    @SerialName("is_active") val isActive: Boolean,
    @SerialName("areas") val areas: List<StudyAreaDto> = emptyList()
)

@Serializable
data class SeatReserveRequestDto(
    @SerialName("seat_id") val seatId: String,
    @SerialName("start_time") val startTime: String,
    @SerialName("end_time") val endTime: String
)

@Serializable
data class SeatReservationDto(
    @SerialName("id") val id: String,
    @SerialName("seat_id") val seatId: String,
    @SerialName("seat_number") val seatNumber: String,
    @SerialName("area_name") val areaName: String,
    @SerialName("floor_name") val floorName: String,
    @SerialName("student_user_id") val studentUserId: String,
    @SerialName("student_name") val studentName: String? = null,
    @SerialName("start_time") val startTime: String,
    @SerialName("end_time") val endTime: String,
    @SerialName("status") val status: String,
    @SerialName("check_in_time") val checkInTime: String? = null,
    @SerialName("check_out_time") val checkOutTime: String? = null,
    @SerialName("qr_token") val qrToken: String
)

@Serializable
data class SeatCheckInRequestDto(
    @SerialName("reservation_id") val reservationId: String,
    @SerialName("qr_identifier") val qrIdentifier: String
)

@Serializable
data class SeatCheckOutRequestDto(
    @SerialName("reservation_id") val reservationId: String
)

@Serializable
data class DemoQrDto(
    @SerialName("seat_id") val seatId: String,
    @SerialName("seat_number") val seatNumber: String,
    @SerialName("area_name") val areaName: String,
    @SerialName("floor_name") val floorName: String,
    @SerialName("qr_identifier") val qrIdentifier: String,
    @SerialName("instructions") val instructions: String
)

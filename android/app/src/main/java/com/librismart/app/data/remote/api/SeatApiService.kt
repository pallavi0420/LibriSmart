package com.librismart.app.data.remote.api

import com.librismart.app.data.remote.dto.DemoQrDto
import com.librismart.app.data.remote.dto.FloorDto
import com.librismart.app.data.remote.dto.MessageResponseDto
import com.librismart.app.data.remote.dto.OccupancyDto
import com.librismart.app.data.remote.dto.SeatCheckInRequestDto
import com.librismart.app.data.remote.dto.SeatCheckOutRequestDto
import com.librismart.app.data.remote.dto.SeatReservationDto
import com.librismart.app.data.remote.dto.SeatReserveRequestDto
import com.librismart.app.data.remote.dto.StudySeatDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface SeatApiService {

    @GET("api/v1/seats/occupancy")
    suspend fun getOccupancy(): Response<OccupancyDto>

    @GET("api/v1/seats/floors")
    suspend fun getFloors(): Response<List<FloorDto>>

    @GET("api/v1/seats/map")
    suspend fun getSeatMap(
        @Query("floor_id") floorId: Int? = null,
        @Query("area_id") areaId: Int? = null,
        @Query("start_time") startTime: String? = null,
        @Query("end_time") endTime: String? = null
    ): Response<List<StudySeatDto>>

    @POST("api/v1/seats/reserve")
    suspend fun reserveSeat(
        @Body request: SeatReserveRequestDto
    ): Response<SeatReservationDto>

    @POST("api/v1/seats/{reservation_id}/cancel")
    suspend fun cancelReservation(
        @Path("reservation_id") reservationId: String
    ): Response<MessageResponseDto>

    @GET("api/v1/seats/my-reservations")
    suspend fun getMyReservations(): Response<List<SeatReservationDto>>

    @POST("api/v1/seats/check-in")
    suspend fun checkIn(
        @Body request: SeatCheckInRequestDto
    ): Response<SeatReservationDto>

    @POST("api/v1/seats/check-out")
    suspend fun checkOut(
        @Body request: SeatCheckOutRequestDto
    ): Response<SeatReservationDto>

    @GET("api/v1/seats/{seat_id}/demo-qr")
    suspend fun getDemoQr(
        @Path("seat_id") seatId: String
    ): Response<DemoQrDto>
}

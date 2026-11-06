package com.librismart.app.data.remote.api

import com.librismart.app.data.remote.dto.MessageResponseDto
import com.librismart.app.data.remote.dto.NotificationDto
import com.librismart.app.data.remote.dto.NotificationMarkReadDto
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path

interface NotificationApiService {

    @GET("api/v1/notifications")
    suspend fun getNotifications(): Response<List<NotificationDto>>

    @PATCH("api/v1/notifications/{notification_id}/read")
    suspend fun markAsRead(
        @Path("notification_id") notificationId: String
    ): Response<NotificationMarkReadDto>

    @POST("api/v1/notifications/mark-all-read")
    suspend fun markAllAsRead(): Response<MessageResponseDto>
}

package com.librismart.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class NotificationDto(
    @SerialName("id") val id: String,
    @SerialName("user_id") val userId: String,
    @SerialName("title") val title: String,
    @SerialName("body") val body: String,
    @SerialName("category") val category: String,
    @SerialName("is_read") val isRead: Boolean,
    @SerialName("created_at") val createdAt: String
)

@Serializable
data class NotificationMarkReadDto(
    @SerialName("id") val id: String,
    @SerialName("is_read") val isRead: Boolean,
    @SerialName("message") val message: String
)

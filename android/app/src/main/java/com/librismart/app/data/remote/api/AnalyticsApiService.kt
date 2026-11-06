package com.librismart.app.data.remote.api

import com.librismart.app.data.remote.dto.DashboardAnalyticsDto
import retrofit2.Response
import retrofit2.http.GET

interface AnalyticsApiService {

    @GET("api/v1/analytics/dashboard")
    suspend fun getDashboardAnalytics(): Response<DashboardAnalyticsDto>
}

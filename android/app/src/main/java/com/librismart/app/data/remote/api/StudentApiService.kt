package com.librismart.app.data.remote.api

import com.librismart.app.data.remote.dto.DigitalStudentCardDto
import retrofit2.Response
import retrofit2.http.GET

interface StudentApiService {

    @GET("api/v1/students/me/card")
    suspend fun getMyDigitalCard(): Response<DigitalStudentCardDto>
}

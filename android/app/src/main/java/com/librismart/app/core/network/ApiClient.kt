package com.librismart.app.core.network

import android.content.Context
import com.librismart.app.core.datastore.UserPreferencesManager
import com.librismart.app.data.remote.api.AuthApiService
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {

    /**
     * Base URL for the LibriSmart Backend API.
     * - Local development (Android Emulator): "http://10.0.2.2:8000/"
     * - Production (Play Store): Replace with your live 24/7 cloud URL (e.g. "https://librismart.onrender.com/")
     */
    private const val BASE_URL = "https://librismart-uajm.onrender.com/"

    private val json = Json {
        ignoreUnknownKeys = true
        coerceInputValues = true
        isLenient = true
        encodeDefaults = true
    }

    private var retrofitInstance: Retrofit? = null

    private fun getRetrofit(context: Context): Retrofit {
        if (retrofitInstance == null) {
            val preferencesManager = UserPreferencesManager(context.applicationContext)
            val authInterceptor = AuthInterceptor(preferencesManager)

            val loggingInterceptor = HttpLoggingInterceptor().apply {
                level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BODY else HttpLoggingInterceptor.Level.NONE
            }

            val okHttpClient = OkHttpClient.Builder()
                .addInterceptor(authInterceptor)
                .addInterceptor(loggingInterceptor)
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(15, TimeUnit.SECONDS)
                .writeTimeout(15, TimeUnit.SECONDS)
                .build()

            val contentType = "application/json".toMediaType()

            retrofitInstance = Retrofit.Builder()
                .baseUrl(BASE_URL)
                .client(okHttpClient)
                .addConverterFactory(json.asConverterFactory(contentType))
                .build()
        }
        return retrofitInstance!!
    }

    fun getAuthApiService(context: Context): AuthApiService {
        return getRetrofit(context).create(AuthApiService::class.java)
    }

    fun getBookApiService(context: Context): com.librismart.app.data.remote.api.BookApiService {
        return getRetrofit(context).create(com.librismart.app.data.remote.api.BookApiService::class.java)
    }

    fun getLoanApiService(context: Context): com.librismart.app.data.remote.api.LoanApiService {
        return getRetrofit(context).create(com.librismart.app.data.remote.api.LoanApiService::class.java)
    }

    fun getSeatApiService(context: Context): com.librismart.app.data.remote.api.SeatApiService {
        return getRetrofit(context).create(com.librismart.app.data.remote.api.SeatApiService::class.java)
    }

    fun getStudentApiService(context: Context): com.librismart.app.data.remote.api.StudentApiService {
        return getRetrofit(context).create(com.librismart.app.data.remote.api.StudentApiService::class.java)
    }

    fun getNotificationApiService(context: Context): com.librismart.app.data.remote.api.NotificationApiService {
        return getRetrofit(context).create(com.librismart.app.data.remote.api.NotificationApiService::class.java)
    }

    fun getAnalyticsApiService(context: Context): com.librismart.app.data.remote.api.AnalyticsApiService {
        return getRetrofit(context).create(com.librismart.app.data.remote.api.AnalyticsApiService::class.java)
    }
}

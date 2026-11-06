package com.librismart.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class DailyCirculationPointDto(
    @SerialName("date_str") val dateStr: String,
    @SerialName("issues_count") val issuesCount: Int,
    @SerialName("returns_count") val returnsCount: Int
)

@Serializable
data class CategorySharePointDto(
    @SerialName("category_name") val categoryName: String,
    @SerialName("books_count") val booksCount: Int
)

@Serializable
data class DashboardAnalyticsDto(
    @SerialName("total_students") val totalStudents: Int,
    @SerialName("total_books") val totalBooks: Int,
    @SerialName("total_copies") val totalCopies: Int,
    @SerialName("available_copies") val availableCopies: Int,
    @SerialName("issued_copies") val issuedCopies: Int,
    @SerialName("overdue_loans") val overdueLoans: Int,
    @SerialName("total_fines_unpaid_cents") val totalFinesUnpaidCents: Int,
    @SerialName("total_fines_collected_cents") val totalFinesCollectedCents: Int,
    @SerialName("total_study_spots") val totalStudySpots: Int,
    @SerialName("occupied_study_spots") val occupiedStudySpots: Int,
    @SerialName("reserved_study_spots") val reservedStudySpots: Int,
    @SerialName("occupancy_percentage") val occupancyPercentage: Double,
    @SerialName("circulation_trends") val circulationTrends: List<DailyCirculationPointDto> = emptyList(),
    @SerialName("category_distribution") val categoryDistribution: List<CategorySharePointDto> = emptyList(),
    @SerialName("generated_at") val generatedAt: String
)

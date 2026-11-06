package com.librismart.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class CategoryDto(
    @SerialName("id") val id: Int,
    @SerialName("name") val name: String,
    @SerialName("description") val description: String? = null,
    @SerialName("book_count") val bookCount: Int = 0
)

@Serializable
data class BookCopyDto(
    @SerialName("id") val id: String,
    @SerialName("book_id") val bookId: String,
    @SerialName("barcode") val barcode: String,
    @SerialName("copy_number") val copyNumber: Int,
    @SerialName("status") val status: String,
    @SerialName("condition_notes") val conditionNotes: String? = null,
    @SerialName("acquired_date") val acquiredDate: String? = null
)

@Serializable
data class BookDto(
    @SerialName("id") val id: String,
    @SerialName("isbn") val isbn: String,
    @SerialName("title") val title: String,
    @SerialName("author") val author: String,
    @SerialName("publisher") val publisher: String? = null,
    @SerialName("edition") val edition: String? = null,
    @SerialName("publication_year") val publicationYear: Int? = null,
    @SerialName("category_id") val categoryId: Int? = null,
    @SerialName("category_name") val categoryName: String? = null,
    @SerialName("language") val language: String = "English",
    @SerialName("description") val description: String? = null,
    @SerialName("cover_image_url") val coverImageUrl: String? = null,
    @SerialName("shelf_location") val shelfLocation: String? = null,
    @SerialName("total_copies_count") val totalCopiesCount: Int = 0,
    @SerialName("available_copies_count") val availableCopiesCount: Int = 0,
    @SerialName("copies") val copies: List<BookCopyDto> = emptyList()
)

@Serializable
data class BookListResponseDto(
    @SerialName("items") val items: List<BookDto>,
    @SerialName("total") val total: Int,
    @SerialName("page") val page: Int,
    @SerialName("size") val size: Int
)

@Serializable
data class BookCreateRequestDto(
    @SerialName("isbn") val isbn: String,
    @SerialName("title") val title: String,
    @SerialName("author") val author: String,
    @SerialName("publisher") val publisher: String? = null,
    @SerialName("edition") val edition: String? = null,
    @SerialName("publication_year") val publicationYear: Int? = null,
    @SerialName("category_id") val categoryId: Int? = null,
    @SerialName("language") val language: String = "English",
    @SerialName("description") val description: String? = null,
    @SerialName("cover_image_url") val coverImageUrl: String? = null,
    @SerialName("shelf_location") val shelfLocation: String? = null,
    @SerialName("initial_copies_count") val initialCopiesCount: Int = 1
)

@Serializable
data class BookCopyCreateDto(
    @SerialName("barcode") val barcode: String? = null,
    @SerialName("copy_number") val copyNumber: Int? = null,
    @SerialName("condition_notes") val conditionNotes: String? = null
)

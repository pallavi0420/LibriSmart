package com.librismart.app.data.remote.api

import com.librismart.app.data.remote.dto.BookCopyCreateDto
import com.librismart.app.data.remote.dto.BookCopyDto
import com.librismart.app.data.remote.dto.BookCreateRequestDto
import com.librismart.app.data.remote.dto.BookDto
import com.librismart.app.data.remote.dto.BookListResponseDto
import com.librismart.app.data.remote.dto.CategoryDto
import com.librismart.app.data.remote.dto.MessageResponseDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface BookApiService {

    @GET("api/v1/books")
    suspend fun getBooks(
        @Query("q") query: String? = null,
        @Query("category_id") categoryId: Int? = null,
        @Query("available_only") availableOnly: Boolean = false,
        @Query("page") page: Int = 1,
        @Query("size") size: Int = 30
    ): Response<BookListResponseDto>

    @GET("api/v1/books/categories")
    suspend fun getCategories(): Response<List<CategoryDto>>

    @GET("api/v1/books/{book_id}")
    suspend fun getBookDetails(
        @Path("book_id") bookId: String
    ): Response<BookDto>

    @POST("api/v1/books")
    suspend fun createBook(
        @Body request: BookCreateRequestDto
    ): Response<BookDto>

    @POST("api/v1/books/{book_id}/copies")
    suspend fun addCopy(
        @Path("book_id") bookId: String,
        @Body request: BookCopyCreateDto
    ): Response<BookCopyDto>

    @DELETE("api/v1/books/{book_id}")
    suspend fun deleteBook(
        @Path("book_id") bookId: String
    ): Response<MessageResponseDto>
}

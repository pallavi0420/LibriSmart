package com.librismart.app.data.repository

import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.api.BookApiService
import com.librismart.app.data.remote.dto.BookCopyCreateDto
import com.librismart.app.data.remote.dto.BookCopyDto
import com.librismart.app.data.remote.dto.BookCreateRequestDto
import com.librismart.app.data.remote.dto.BookDto
import com.librismart.app.data.remote.dto.BookListResponseDto
import com.librismart.app.data.remote.dto.CategoryDto
import com.librismart.app.data.remote.dto.MessageResponseDto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

class BookRepository(
    private val bookApiService: BookApiService
) {

    suspend fun getBooks(
        query: String? = null,
        categoryId: Int? = null,
        availableOnly: Boolean = false,
        page: Int = 1,
        size: Int = 30
    ): NetworkResult<BookListResponseDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = bookApiService.getBooks(
                    query = query?.ifBlank { null },
                    categoryId = categoryId,
                    availableOnly = availableOnly,
                    page = page,
                    size = size
                )
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to fetch book catalogue"}")
            }
        }
    }

    suspend fun getCategories(): NetworkResult<List<CategoryDto>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = bookApiService.getCategories()
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to fetch categories"}")
            }
        }
    }

    suspend fun getBookDetails(bookId: String): NetworkResult<BookDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = bookApiService.getBookDetails(bookId)
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to load book details"}")
            }
        }
    }

    suspend fun createBook(request: BookCreateRequestDto): NetworkResult<BookDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = bookApiService.createBook(request)
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to add book"}")
            }
        }
    }

    suspend fun addCopy(bookId: String, barcode: String? = null, condition: String? = null): NetworkResult<BookCopyDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = bookApiService.addCopy(
                    bookId = bookId,
                    request = BookCopyCreateDto(barcode = barcode, conditionNotes = condition)
                )
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to add copy"}")
            }
        }
    }

    suspend fun deleteBook(bookId: String): NetworkResult<MessageResponseDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = bookApiService.deleteBook(bookId)
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to delete book"}")
            }
        }
    }

    private fun parseErrorMessage(errorBody: String?): String {
        return try {
            if (!errorBody.isNullOrBlank()) {
                val json = JSONObject(errorBody)
                json.optString("detail", "Operation failed.")
            } else {
                "An unexpected server error occurred."
            }
        } catch (_: Exception) {
            "An unexpected server error occurred."
        }
    }
}

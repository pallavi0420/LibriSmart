package com.librismart.app.data.repository

import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.api.LoanApiService
import com.librismart.app.data.remote.dto.BookLoanDto
import com.librismart.app.data.remote.dto.FinePaymentRequestDto
import com.librismart.app.data.remote.dto.FinePaymentResponseDto
import com.librismart.app.data.remote.dto.FineRecordDto
import com.librismart.app.data.remote.dto.LoanIssueRequestDto
import com.librismart.app.data.remote.dto.LoanRenewalResponseDto
import com.librismart.app.data.remote.dto.LoanReturnRequestDto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

class LoanRepository(
    private val loanApiService: LoanApiService
) {

    suspend fun getMyActiveLoans(): NetworkResult<List<BookLoanDto>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = loanApiService.getMyActiveLoans()
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to fetch active loans"}")
            }
        }
    }

    suspend fun getMyHistory(): NetworkResult<List<BookLoanDto>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = loanApiService.getMyHistory()
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to fetch borrowing history"}")
            }
        }
    }

    suspend fun renewLoan(loanId: String): NetworkResult<LoanRenewalResponseDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = loanApiService.renewLoan(loanId)
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to renew loan"}")
            }
        }
    }

    suspend fun listAllActiveLoans(
        studentIdNumber: String? = null,
        barcode: String? = null,
        overdueOnly: Boolean = false
    ): NetworkResult<List<BookLoanDto>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = loanApiService.listAllActiveLoans(
                    studentIdNumber = studentIdNumber?.ifBlank { null },
                    barcode = barcode?.ifBlank { null },
                    overdueOnly = overdueOnly
                )
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to fetch active circulation loans"}")
            }
        }
    }

    suspend fun issueBook(
        studentIdOrEmail: String,
        barcode: String,
        durationDays: Int = 14
    ): NetworkResult<BookLoanDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = loanApiService.issueBook(
                    LoanIssueRequestDto(
                        studentIdOrEmail = studentIdOrEmail.trim(),
                        barcode = barcode.trim(),
                        loanDurationDays = durationDays
                    )
                )
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to issue book"}")
            }
        }
    }

    suspend fun returnBook(
        barcode: String,
        conditionNotes: String? = null,
        markAsDamaged: Boolean = false
    ): NetworkResult<BookLoanDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = loanApiService.returnBook(
                    LoanReturnRequestDto(
                        barcode = barcode.trim(),
                        conditionNotes = conditionNotes?.trim()?.ifBlank { null },
                        markAsDamaged = markAsDamaged
                    )
                )
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to return book"}")
            }
        }
    }

    suspend fun getMyFines(): NetworkResult<List<FineRecordDto>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = loanApiService.getMyFines()
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to fetch student fines"}")
            }
        }
    }

    suspend fun settleFineOffline(
        fineId: String,
        amountCents: Int,
        paymentMethod: String = "CASH_OFFLINE"
    ): NetworkResult<FinePaymentResponseDto> {
        return withContext(Dispatchers.IO) {
            try {
                val response = loanApiService.settleFineOffline(
                    fineId = fineId,
                    request = FinePaymentRequestDto(amountPaidCents = amountCents, paymentMethod = paymentMethod)
                )
                if (response.isSuccessful && response.body() != null) {
                    NetworkResult.Success(response.body()!!)
                } else {
                    NetworkResult.Error(parseErrorMessage(response.errorBody()?.string()), response.code())
                }
            } catch (e: Exception) {
                NetworkResult.Error("Network error: ${e.localizedMessage ?: "Failed to record payment"}")
            }
        }
    }

    private fun parseErrorMessage(errorJson: String?): String {
        if (errorJson.isNullOrBlank()) return "Circulation operation failed. Please try again."
        return try {
            val json = JSONObject(errorJson)
            json.optString("detail", "Circulation operation failed.")
        } catch (_: Exception) {
            errorJson
        }
    }
}

package com.librismart.app.data.remote.api

import com.librismart.app.data.remote.dto.BookLoanDto
import com.librismart.app.data.remote.dto.FinePaymentRequestDto
import com.librismart.app.data.remote.dto.FinePaymentResponseDto
import com.librismart.app.data.remote.dto.FineRecordDto
import com.librismart.app.data.remote.dto.LoanIssueRequestDto
import com.librismart.app.data.remote.dto.LoanRenewalResponseDto
import com.librismart.app.data.remote.dto.LoanReturnRequestDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface LoanApiService {

    @GET("api/v1/loans/my-active")
    suspend fun getMyActiveLoans(): Response<List<BookLoanDto>>

    @GET("api/v1/loans/my-history")
    suspend fun getMyHistory(): Response<List<BookLoanDto>>

    @POST("api/v1/loans/{loan_id}/renew")
    suspend fun renewLoan(
        @Path("loan_id") loanId: String
    ): Response<LoanRenewalResponseDto>

    @GET("api/v1/loans/active")
    suspend fun listAllActiveLoans(
        @Query("student_id_number") studentIdNumber: String? = null,
        @Query("barcode") barcode: String? = null,
        @Query("overdue_only") overdueOnly: Boolean = false
    ): Response<List<BookLoanDto>>

    @POST("api/v1/loans/issue")
    suspend fun issueBook(
        @Body request: LoanIssueRequestDto
    ): Response<BookLoanDto>

    @POST("api/v1/loans/return")
    suspend fun returnBook(
        @Body request: LoanReturnRequestDto
    ): Response<BookLoanDto>

    @GET("api/v1/fines/my-fines")
    suspend fun getMyFines(): Response<List<FineRecordDto>>

    @POST("api/v1/fines/{fine_id}/pay-offline")
    suspend fun settleFineOffline(
        @Path("fine_id") fineId: String,
        @Body request: FinePaymentRequestDto
    ): Response<FinePaymentResponseDto>
}

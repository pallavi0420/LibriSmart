package com.librismart.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class BookLoanDto(
    @SerialName("id") val id: String,
    @SerialName("book_copy_id") val bookCopyId: String,
    @SerialName("barcode") val barcode: String,
    @SerialName("book_id") val bookId: String,
    @SerialName("book_title") val bookTitle: String,
    @SerialName("book_author") val bookAuthor: String,
    @SerialName("cover_image_url") val coverImageUrl: String? = null,
    @SerialName("shelf_location") val shelfLocation: String? = null,
    @SerialName("student_user_id") val studentUserId: String,
    @SerialName("student_name") val studentName: String? = null,
    @SerialName("student_id_number") val studentIdNumber: String? = null,
    @SerialName("issue_date") val issueDate: String,
    @SerialName("due_date") val dueDate: String,
    @SerialName("return_date") val returnDate: String? = null,
    @SerialName("status") val status: String,
    @SerialName("renewal_count") val renewalCount: Int = 0,
    @SerialName("max_renewals_allowed") val maxRenewalsAllowed: Int = 2,
    @SerialName("is_overdue") val isOverdue: Boolean = false,
    @SerialName("days_overdue") val daysOverdue: Int = 0,
    @SerialName("fine_amount_cents") val fineAmountCents: Int = 0
)

@Serializable
data class LoanIssueRequestDto(
    @SerialName("student_id_or_email") val studentIdOrEmail: String,
    @SerialName("barcode") val barcode: String,
    @SerialName("loan_duration_days") val loanDurationDays: Int = 14
)

@Serializable
data class LoanReturnRequestDto(
    @SerialName("barcode") val barcode: String,
    @SerialName("condition_notes") val conditionNotes: String? = null,
    @SerialName("mark_as_damaged") val markAsDamaged: Boolean = false
)

@Serializable
data class LoanRenewalResponseDto(
    @SerialName("loan_id") val loanId: String,
    @SerialName("new_due_date") val newDueDate: String,
    @SerialName("renewal_count") val renewalCount: Int,
    @SerialName("max_renewals_allowed") val maxRenewalsAllowed: Int,
    @SerialName("message") val message: String
)

@Serializable
data class FineRecordDto(
    @SerialName("id") val id: String,
    @SerialName("loan_id") val loanId: String,
    @SerialName("book_title") val bookTitle: String,
    @SerialName("amount_cents") val amountCents: Int,
    @SerialName("amount_display") val amountDisplay: String,
    @SerialName("days_overdue") val daysOverdue: Int,
    @SerialName("status") val status: String,
    @SerialName("waiver_reason") val waiverReason: String? = null,
    @SerialName("created_at") val createdAt: String
)

@Serializable
data class FinePaymentRequestDto(
    @SerialName("amount_paid_cents") val amountPaidCents: Int,
    @SerialName("payment_method") val paymentMethod: String = "CASH_OFFLINE",
    @SerialName("receipt_number") val receiptNumber: String? = null
)

@Serializable
data class FinePaymentResponseDto(
    @SerialName("id") val id: String,
    @SerialName("fine_record_id") val fineRecordId: String,
    @SerialName("amount_paid_cents") val amountPaidCents: Int,
    @SerialName("receipt_number") val receiptNumber: String,
    @SerialName("payment_date") val paymentDate: String,
    @SerialName("remaining_fine_cents") val remainingFineCents: Int,
    @SerialName("status") val status: String
)

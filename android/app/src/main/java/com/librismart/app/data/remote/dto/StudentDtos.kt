package com.librismart.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class DigitalStudentCardDto(
    @SerialName("student_user_id") val studentUserId: String,
    @SerialName("student_name") val studentName: String,
    @SerialName("student_id_number") val studentIdNumber: String,
    @SerialName("email") val email: String,
    @SerialName("department") val department: String,
    @SerialName("batch_year") val batchYear: Int,
    @SerialName("membership_status") val membershipStatus: String,
    @SerialName("digital_card_barcode") val digitalCardBarcode: String,
    @SerialName("digital_card_qr") val digitalCardQr: String,
    @SerialName("member_since") val memberSince: String,
    @SerialName("valid_until") val validUntil: String,
    @SerialName("active_loans_count") val activeLoansCount: Int,
    @SerialName("max_borrow_limit") val maxBorrowLimit: Int,
    @SerialName("unpaid_fines_cents") val unpaidFinesCents: Int
)

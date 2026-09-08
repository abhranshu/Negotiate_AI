package com.negotiateai.app.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class LoginRequest(
    val username: String,
    val password: String,
)

@Serializable
data class RegisterRequest(
    val email: String,
    val password: String,
    @SerialName("full_name") val fullName: String,
    @SerialName("role") val role: UserRole = UserRole.CLAIMANT,
    @SerialName("company_name") val companyName: String? = null,
    @SerialName("udyam_number") val udyamNumber: String? = null,
    val gstin: String? = null,
    val phone: String? = null,
)

@Serializable
data class AuthTokenResponse(
    @SerialName("access_token") val accessToken: String,
    @SerialName("token_type") val tokenType: String = "bearer",
)

@Serializable
enum class UserRole {
    @SerialName("claimant") CLAIMANT,
    @SerialName("respondent") RESPONDENT,
}

@Serializable
data class UserDto(
    val id: String,
    val email: String,
    @SerialName("full_name") val fullName: String,
    val role: UserRole,
    @SerialName("company_name") val companyName: String? = null,
    @SerialName("udyam_number") val udyamNumber: String? = null,
    val gstin: String? = null,
)

@Serializable
enum class CaseStatus {
    @SerialName("draft") DRAFT,
    @SerialName("submitted") SUBMITTED,
    @SerialName("in_progress") IN_PROGRESS,
    @SerialName("agreement") AGREEMENT,
    @SerialName("closed") CLOSED,
    @SerialName("escalated") ESCALATED,
}

@Serializable
enum class DisputeType {
    @SerialName("delayed_payment") DELAYED_PAYMENT,
    @SerialName("non_payment") NON_PAYMENT,
    @SerialName("short_payment") SHORT_PAYMENT,
    @SerialName("quality_dispute") QUALITY_DISPUTE,
    @SerialName("quantity_dispute") QUANTITY_DISPUTE,
    @SerialName("contract_breach") CONTRACT_BREACH,
}

@Serializable
data class CreateCaseRequest(
    @SerialName("dispute_type") val disputeType: DisputeType? = null,
    @SerialName("claim_amount") val claimAmount: Double? = null,
    @SerialName("overdue_days") val overdueDays: Int? = null,
    val description: String? = null,
    val state: String? = null,
    val industry: String? = null,
    @SerialName("respondent_email") val respondentEmail: String? = null,
)

@Serializable
data class CaseListItem(
    val id: String,
    @SerialName("case_number") val caseNumber: String? = null,
    val status: CaseStatus,
    @SerialName("dispute_type") val disputeType: DisputeType? = null,
    @SerialName("claim_amount") val claimAmount: Double? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class CaseDto(
    val id: String,
    @SerialName("case_number") val caseNumber: String? = null,
    val status: CaseStatus,
    @SerialName("dispute_type") val disputeType: DisputeType? = null,
    @SerialName("claim_amount") val claimAmount: Double? = null,
    @SerialName("overdue_days") val overdueDays: Int? = null,
    val description: String? = null,
    val state: String? = null,
    val industry: String? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("case_strength") val caseStrength: String? = null,
    @SerialName("settlement_probability") val settlementProbability: Double? = null,
    @SerialName("settlement_range_low") val settlementRangeLow: Double? = null,
    @SerialName("settlement_range_high") val settlementRangeHigh: Double? = null,
    @SerialName("adjudication_days") val adjudicationDays: Int? = null,
    @SerialName("prediction_recommendation") val predictionRecommendation: String? = null,
    @SerialName("agreement_amount") val agreementAmount: Double? = null,
)

@Serializable
data class CaseDescriptionUpdate(
    val description: String,
)

@Serializable
data class DocumentDto(
    val id: String,
    val filename: String,
    @SerialName("doc_type") val docType: String? = null,
    val confidence: Double? = null,
    @SerialName("is_valid") val isValid: Boolean = false,
    val issues: List<String> = emptyList(),
    @SerialName("key_fields") val keyFields: Map<String, String> = emptyMap(),
    @SerialName("uploaded_at") val uploadedAt: String,
)

@Serializable
data class NegotiationRequest(
    val text: String,
    val offer: Double? = null,
)

@Serializable
data class NegotiationResponse(
    @SerialName("mediator_response") val mediatorResponse: String,
    @SerialName("sentiment_detected") val sentimentDetected: String,
    val phase: String,
    val round: Int,
    @SerialName("agreement_reached") val agreementReached: Boolean,
    @SerialName("agreement_amount") val agreementAmount: Double? = null,
    @SerialName("strategy_hints") val strategyHints: Map<String, String> = emptyMap(),
)

@Serializable
data class NegotiationMessageDto(
    val id: String? = null,
    val party: String,
    val text: String,
    val offer: Double? = null,
    val sentiment: String? = null,
    val phase: String? = null,
    @SerialName("timestamp") val timestamp: String? = null,
)

@Serializable
data class KeyFactor(
    val factor: String = "",
    val impact: Double = 0.0,
    val direction: String = "",
)

@Serializable
data class PredictionDto(
    @SerialName("settlement_probability") val settlementProbability: Double = 0.0,
    @SerialName("settlement_range_low") val settlementRangeLow: Double = 0.0,
    @SerialName("settlement_range_high") val settlementRangeHigh: Double = 0.0,
    @SerialName("adjudication_days") val adjudicationDays: Int = 0,
    @SerialName("confidence_band") val confidenceBand: String = "",
    @SerialName("key_factors") val keyFactors: List<KeyFactor> = emptyList(),
    val recommendation: String = "",
)

@Serializable
data class SettlementDto(
    @SerialName("agreement_id") val agreementId: String = "",
    val date: String = "",
    @SerialName("dispute_type") val disputeType: String? = null,
    @SerialName("original_claim") val originalClaim: Double = 0.0,
    @SerialName("agreed_amount") val agreedAmount: Double = 0.0,
    @SerialName("agreement_text") val agreementText: String = "",
    @SerialName("is_valid") val isValid: Boolean = false,
    @SerialName("validation_notes") val validationNotes: List<String> = emptyList(),
)

@Serializable
data class WsFrame(
    val type: String = "",
    val sender: String? = null,
    val text: String? = null,
    val offer: Double? = null,
    val sentiment: String? = null,
    val phase: String? = null,
    val round: Int? = null,
    @SerialName("agreement_reached") val agreementReached: Boolean? = null,
    @SerialName("agreement_amount") val agreementAmount: Double? = null,
    val hint: String? = null,
)
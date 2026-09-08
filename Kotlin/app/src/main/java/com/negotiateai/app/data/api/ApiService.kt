package com.negotiateai.app.data.api

import com.negotiateai.app.data.model.AuthTokenResponse
import com.negotiateai.app.data.model.CaseDescriptionUpdate
import com.negotiateai.app.data.model.CaseDto
import com.negotiateai.app.data.model.CaseListItem
import com.negotiateai.app.data.model.CreateCaseRequest
import com.negotiateai.app.data.model.DocumentDto
import com.negotiateai.app.data.model.LoginRequest
import com.negotiateai.app.data.model.NegotiationMessageDto
import com.negotiateai.app.data.model.NegotiationRequest
import com.negotiateai.app.data.model.NegotiationResponse
import com.negotiateai.app.data.model.PredictionDto
import com.negotiateai.app.data.model.RegisterRequest
import com.negotiateai.app.data.model.SettlementDto
import com.negotiateai.app.data.model.UserDto
import okhttp3.MultipartBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path

interface ApiService {
    @FormUrlEncoded
    @POST("api/auth/login")
    suspend fun login(
        @Field("username") username: String,
        @Field("password") password: String,
    ): Response<AuthTokenResponse>

    @POST("api/auth/register")
    suspend fun register(@Body request: RegisterRequest): Response<UserDto>

    @GET("api/auth/me")
    suspend fun getCurrentUser(): Response<UserDto>

    @GET("api/cases")
    suspend fun getCases(): Response<List<CaseListItem>>

    @POST("api/cases")
    suspend fun createCase(@Body request: CreateCaseRequest): Response<CaseDto>

    @GET("api/cases/{case_id}")
    suspend fun getCase(@Path("case_id") caseId: String): Response<CaseDto>

    @PATCH("api/cases/{case_id}/description")
    suspend fun updateDescription(
        @Path("case_id") caseId: String,
        @Body body: CaseDescriptionUpdate,
    ): Response<CaseDto>

    @Multipart
    @POST("api/cases/{case_id}/voice")
    suspend fun uploadVoice(
        @Path("case_id") caseId: String,
        @Part file: MultipartBody.Part,
    ): Response<CaseDto>

    @Multipart
    @POST("api/cases/{case_id}/documents")
    suspend fun uploadDocuments(
        @Path("case_id") caseId: String,
        @Part files: List<MultipartBody.Part>,
    ): Response<List<DocumentDto>>

    @GET("api/cases/{case_id}/documents")
    suspend fun getDocuments(@Path("case_id") caseId: String): Response<List<DocumentDto>>

    @GET("api/cases/{case_id}/messages")
    suspend fun getMessages(@Path("case_id") caseId: String): Response<List<NegotiationMessageDto>>

    @POST("api/cases/{case_id}/negotiate")
    suspend fun negotiate(
        @Path("case_id") caseId: String,
        @Body request: NegotiationRequest,
    ): Response<NegotiationResponse>

    @POST("api/cases/{case_id}/predict")
    suspend fun runPrediction(@Path("case_id") caseId: String): Response<PredictionDto>

    @POST("api/cases/{case_id}/settlement")
    suspend fun generateSettlement(@Path("case_id") caseId: String): Response<SettlementDto>

    @GET("api/cases/{case_id}/settlement")
    suspend fun getSettlement(@Path("case_id") caseId: String): Response<SettlementDto>
}
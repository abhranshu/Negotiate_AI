package com.negotiateai.app.data.repository

import android.content.Context
import com.negotiateai.app.data.model.CaseDescriptionUpdate
import com.negotiateai.app.data.model.CaseDto
import com.negotiateai.app.data.model.CaseListItem
import com.negotiateai.app.data.model.CreateCaseRequest
import com.negotiateai.app.data.model.DocumentDto
import com.negotiateai.app.data.model.NegotiationMessageDto
import com.negotiateai.app.data.model.PredictionDto
import com.negotiateai.app.data.model.SettlementDto
import com.negotiateai.app.data.api.ApiService
import com.negotiateai.app.core.network.ApiClient
import com.negotiateai.app.core.network.NetworkResult
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File

class CaseRepository(context: Context) {
	private val api = ApiClient.getService(context)

	suspend fun listCases(): NetworkResult<List<CaseListItem>> = try {
		val response = api.getCases()
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Failed to load cases" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}

	suspend fun getCase(caseId: String): NetworkResult<CaseDto> = try {
		val response = api.getCase(caseId)
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Case not found" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}

	suspend fun createCase(request: CreateCaseRequest): NetworkResult<CaseDto> = try {
		val response = api.createCase(request)
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Failed to create case" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}

	suspend fun updateDescription(caseId: String, description: String): NetworkResult<CaseDto> = try {
		val response = api.updateDescription(caseId, CaseDescriptionUpdate(description))
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Failed to update description" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}

	suspend fun getDocuments(caseId: String): NetworkResult<List<DocumentDto>> = try {
		val response = api.getDocuments(caseId)
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Failed to load documents" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}

	suspend fun getMessages(caseId: String): NetworkResult<List<NegotiationMessageDto>> = try {
		val response = api.getMessages(caseId)
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Failed to load messages" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}

	suspend fun runPrediction(caseId: String): NetworkResult<PredictionDto> = try {
		val response = api.runPrediction(caseId)
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Prediction failed" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}

	suspend fun generateSettlement(caseId: String): NetworkResult<SettlementDto> = try {
		val response = api.generateSettlement(caseId)
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Settlement generation failed" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}

	suspend fun getSettlement(caseId: String): NetworkResult<SettlementDto> = try {
		val response = api.getSettlement(caseId)
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "No settlement found" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}

	suspend fun uploadVoice(caseId: String, audioFile: File, mimeType: String = "audio/m4a"): NetworkResult<CaseDto> = try {
		val part = MultipartBody.Part.createFormData(
			"file",
			audioFile.name,
			audioFile.asRequestBody(mimeType.toMediaType()),
		)
		val response = api.uploadVoice(caseId, part)
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Voice upload failed" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}

	suspend fun uploadDocuments(caseId: String, files: List<File>): NetworkResult<List<DocumentDto>> = try {
		val parts = files.map { file ->
			MultipartBody.Part.createFormData(
				"files",
				file.name,
				file.asRequestBody("application/octet-stream".toMediaType()),
			)
		}
		val response = api.uploadDocuments(caseId, parts)
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Document upload failed" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}
}

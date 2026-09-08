package com.negotiateai.app.data.repository

import android.content.Context
import com.negotiateai.app.data.model.NegotiationRequest
import com.negotiateai.app.data.model.NegotiationResponse
import com.negotiateai.app.core.network.ApiClient
import com.negotiateai.app.core.network.NetworkResult

class NegotiationRepository(context: Context) {
	private val api = ApiClient.getService(context)

	suspend fun negotiate(caseId: String, text: String, offer: Double? = null): NetworkResult<NegotiationResponse> = try {
		val response = api.negotiate(caseId, NegotiationRequest(text, offer))
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Negotiation failed" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}
}

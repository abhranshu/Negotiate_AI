package com.negotiateai.app.feature.negotiation

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.negotiateai.app.data.model.NegotiationMessageDto
import com.negotiateai.app.data.repository.CaseRepository
import com.negotiateai.app.data.repository.NegotiationRepository
import com.negotiateai.app.core.network.NetworkResult
import kotlinx.coroutines.launch

class NegotiationViewModel(context: Context) : ViewModel() {
    private val caseRepository = CaseRepository(context)
    private val negotiationRepository = NegotiationRepository(context)

    var messages by mutableStateOf<List<NegotiationMessageDto>>(emptyList())
        private set
    var input by mutableStateOf("")
    var offer by mutableStateOf("")
    var isLoading by mutableStateOf(false)
    var error by mutableStateOf<String?>(null)

    fun loadMessages(caseId: String) {
        viewModelScope.launch {
            when (val result = caseRepository.getMessages(caseId)) {
                is NetworkResult.Success -> messages = result.data ?: emptyList()
                is NetworkResult.Error -> error = result.message
                is NetworkResult.Loading -> Unit
            }
        }
    }

    fun sendMessage(caseId: String) {
        isLoading = true
        viewModelScope.launch {
            val offerValue = offer.toDoubleOrNull()
            when (negotiationRepository.negotiate(caseId, input, offerValue)) {
                is NetworkResult.Success -> {
                    input = ""
                    offer = ""
                    loadMessages(caseId)
                }
                is NetworkResult.Error -> error = "Failed to send message"
                else -> Unit
            }
            isLoading = false
        }
    }
}
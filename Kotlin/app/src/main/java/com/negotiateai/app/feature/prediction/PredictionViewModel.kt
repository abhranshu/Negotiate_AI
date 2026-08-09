package com.negotiateai.app.feature.prediction

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.negotiateai.app.data.model.CaseDto
import com.negotiateai.app.data.repository.CaseRepository
import com.negotiateai.app.core.network.NetworkResult
import kotlinx.coroutines.launch

class PredictionViewModel(context: Context) : ViewModel() {
    private val repository = CaseRepository(context)

    var case by mutableStateOf<CaseDto?>(null)
        private set
    var isLoading by mutableStateOf(true)
        private set
    var error by mutableStateOf<String?>(null)

    fun loadCase(caseId: String) {
        isLoading = true
        error = null
        viewModelScope.launch {
            when (val result = repository.getCase(caseId)) {
                is NetworkResult.Success -> case = result.data
                is NetworkResult.Error -> error = result.message
                is NetworkResult.Loading -> Unit
            }
            isLoading = false
        }
    }
}
package com.negotiateai.app.feature.dashboard

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.negotiateai.app.data.model.CaseListItem
import com.negotiateai.app.data.repository.CaseRepository
import com.negotiateai.app.core.network.NetworkResult
import kotlinx.coroutines.launch

class DashboardViewModel(context: Context) : ViewModel() {
    private val repository = CaseRepository(context)

    var cases by mutableStateOf<List<CaseListItem>>(emptyList())
        private set
    var isLoading by mutableStateOf(true)
        private set
    var error by mutableStateOf<String?>(null)
        private set

    fun loadCases() {
        isLoading = true
        error = null
        viewModelScope.launch {
            when (val result = repository.listCases()) {
                is NetworkResult.Success -> cases = result.data ?: emptyList()
                is NetworkResult.Error -> error = result.message
                is NetworkResult.Loading -> Unit
            }
            isLoading = false
        }
    }

    fun refresh() = loadCases()
}
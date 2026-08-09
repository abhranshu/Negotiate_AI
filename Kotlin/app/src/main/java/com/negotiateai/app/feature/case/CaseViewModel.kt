package com.negotiateai.app.feature.`case`

import androidx.lifecycle.ViewModel
import com.negotiateai.app.data.model.CaseDto
import com.negotiateai.app.data.model.CaseListItem
import com.negotiateai.app.data.model.DocumentDto
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class CaseDetailUiState(
    val isLoading: Boolean = false,
    val caseData: CaseDto? = null,
    val error: String? = null,
    val documents: List<DocumentDto> = emptyList(),
)

data class CreateCaseUiState(
    val isLoading: Boolean = false,
    val createdCaseId: String? = null,
    val error: String? = null,
)

class CaseViewModel : ViewModel() {
    private val _detailState = MutableStateFlow(CaseDetailUiState())
    val detailState: StateFlow<CaseDetailUiState> = _detailState.asStateFlow()

    private val _createState = MutableStateFlow(CreateCaseUiState())
    val createState: StateFlow<CreateCaseUiState> = _createState.asStateFlow()

    fun resetCreateState() {
        _createState.value = CreateCaseUiState()
    }
}
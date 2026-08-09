package com.negotiateai.app.feature.auth

import androidx.lifecycle.ViewModel
import com.negotiateai.app.data.model.UserDto
import com.negotiateai.app.core.network.NetworkResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class AuthUiState(
    val isLoading: Boolean = false,
    val isAuthenticated: Boolean = false,
    val user: UserDto? = null,
    val error: String? = null,
)

sealed class AuthEvent {
    object Submit : AuthEvent()
}

class AuthViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    fun onEvent(event: AuthEvent) {
        _uiState.value = AuthUiState()
    }
}
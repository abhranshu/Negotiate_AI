package com.negotiateai.app.data.repository

import android.content.Context
import com.negotiateai.app.data.SessionManager
import com.negotiateai.app.data.model.LoginRequest
import com.negotiateai.app.data.model.RegisterRequest
import com.negotiateai.app.data.model.UserDto
import com.negotiateai.app.data.api.ApiService
import com.negotiateai.app.core.network.ApiClient
import com.negotiateai.app.core.network.NetworkResult

class AuthRepository(private val context: Context) {
	private val api = ApiClient.getService(context)
	private val sessionManager = SessionManager(context)

	suspend fun login(email: String, password: String): NetworkResult<String> = try {
		val response = api.login(email, password)
		if (response.isSuccessful && response.body() != null) {
			val token = response.body()!!.accessToken
			sessionManager.saveAuthToken(token)
			// Persist the user id + role so the app knows who is logged in.
			fetchAndSaveCurrentUser()
			NetworkResult.Success(token)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Login failed" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}

	/** Fetch /me and store the user's id and role (non-fatal if it fails). */
	private suspend fun fetchAndSaveCurrentUser() {
		try {
			val me = api.getCurrentUser()
			if (me.isSuccessful && me.body() != null) {
				val user = me.body()!!
				sessionManager.saveUserId(user.id)
				sessionManager.saveUserRole(user.role.name.lowercase())
			}
		} catch (e: Exception) {
			// Non-fatal: auth still succeeded; role features degrade gracefully.
		}
	}

	suspend fun register(request: RegisterRequest): NetworkResult<UserDto> = try {
		val response = api.register(request)
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Registration failed" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}

	suspend fun currentUser(): NetworkResult<UserDto> = try {
		val response = api.getCurrentUser()
		if (response.isSuccessful && response.body() != null) {
			NetworkResult.Success(response.body()!!)
		} else {
			NetworkResult.Error(response.message().ifBlank { "Failed to load profile" })
		}
	} catch (e: Exception) {
		NetworkResult.Error(e.message ?: "Network failure")
	}
}

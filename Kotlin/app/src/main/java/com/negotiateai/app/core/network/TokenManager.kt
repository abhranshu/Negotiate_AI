package com.negotiateai.app.core.network

import android.content.Context
import com.negotiateai.app.data.SessionManager

class TokenManager(context: Context) {
	private val sessionManager = SessionManager(context)

	suspend fun saveToken(token: String) = sessionManager.saveAuthToken(token)
	suspend fun clearToken() = sessionManager.clearAuthToken()
}

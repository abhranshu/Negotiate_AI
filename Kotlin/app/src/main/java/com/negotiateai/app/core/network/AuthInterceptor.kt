package com.negotiateai.app.core.network

import com.negotiateai.app.data.SessionManager
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response

class AuthInterceptor(
	private val sessionManager: SessionManager,
) : Interceptor {
	override fun intercept(chain: Interceptor.Chain): Response {
		val request = chain.request()
		val path = request.url.encodedPath

		if (path.contains("/api/auth/login") || path.contains("/api/auth/register")) {
			return chain.proceed(request)
		}

		val token = runBlocking { sessionManager.authToken.first() }
		val authRequest = if (!token.isNullOrBlank()) {
			request.newBuilder().header("Authorization", "Bearer $token").build()
		} else request

		return chain.proceed(authRequest)
	}
}

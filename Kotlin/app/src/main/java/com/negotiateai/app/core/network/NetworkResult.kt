package com.negotiateai.app.core.network

sealed class NetworkResult<T>(
    val data: T? = null,
    val message: String? = null
) {
    class Success<T>(data: T) : NetworkResult<T>(data)
    class Error<T>(message: String, data: T? = null) : NetworkResult<T>(data, message)
    class Loading<T> : NetworkResult<T>()
}

suspend fun <T> safeApiCall(
    dispatcher: kotlinx.coroutines.CoroutineDispatcher = kotlinx.coroutines.Dispatchers.IO,
    apiCall: suspend () -> retrofit2.Response<T>
): NetworkResult<T> = kotlinx.coroutines.withContext(dispatcher) {
    try {
        val response = apiCall()
        if (response.isSuccessful && response.body() != null) {
            NetworkResult.Success(response.body()!!)
        } else {
            NetworkResult.Error(response.message() ?: "Unknown error")
        }
    } catch (e: Exception) {
        NetworkResult.Error(e.message ?: "Network failure")
    }
}

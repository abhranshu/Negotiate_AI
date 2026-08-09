package com.negotiateai.app.core.network

import com.negotiateai.app.data.model.NegotiationMessageDto
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.WebSocket
import okhttp3.WebSocketListener

class NegotiationWebSocket(private val caseId: String) {
    private var webSocket: WebSocket? = null
    private val json = Json { ignoreUnknownKeys = true }

    private val _messages = MutableSharedFlow<NegotiationMessageDto>(extraBufferCapacity = 10)
    val messages: SharedFlow<NegotiationMessageDto> = _messages

    fun connect() {
        val client = OkHttpClient()
        val request = Request.Builder()
            .url("ws://10.0.2.2:8000/ws/negotiate/$caseId")
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val message = json.decodeFromString<NegotiationMessageDto>(text)
                    _messages.tryEmit(message)
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        })
    }

    fun sendMessage(content: String, type: String = "text") {
        val json = """{"content":"$content","type":"$type"}"""
        webSocket?.send(json)
    }

    fun disconnect() {
        webSocket?.close(1000, "Closing")
        webSocket = null
    }
}
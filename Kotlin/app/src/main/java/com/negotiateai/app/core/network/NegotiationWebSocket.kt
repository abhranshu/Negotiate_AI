package com.negotiateai.app.core.network

import com.negotiateai.app.data.model.NegotiationMessageDto
import com.negotiateai.app.data.model.WsFrame
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.WebSocket
import okhttp3.WebSocketListener

/**
 * Real-time negotiation WebSocket client.
 *
 * Backend contract (api/routes/negotiate.py):
 *   URL:  ws://<host>/api/cases/ws/{case_id}?party=claimant
 *   Send: {"text": "...", "offer": 1234.5}
 *   Recv: {"type": "user_message" | "mediator_started" | "mediator_token" |
 *          "mediator_response", "sender": "...", "text": "...",
 *          "sentiment": "...", "phase": "...", "round": 1,
 *          "agreement_reached": false, "agreement_amount": null}
 *
 * Streaming: a mediator reply arrives as mediator_started (metadata only),
 * then zero or more mediator_token frames (text chunks), then a final
 * mediator_response frame with the full authoritative text.
 *
 * "presence_update" / "private_hint" frames are ignored here.
 */

/** Live-stream events for an in-progress mediator reply. */
sealed class WsStreamEvent {
    data class Started(val phase: String?, val round: Int?) : WsStreamEvent()
    data class Chunk(val text: String) : WsStreamEvent()
}

class NegotiationWebSocket(private val caseId: String) {
    private var webSocket: WebSocket? = null
    private val json = Json { ignoreUnknownKeys = true }

    private val _messages = MutableSharedFlow<NegotiationMessageDto>(extraBufferCapacity = 10)
    val messages: SharedFlow<NegotiationMessageDto> = _messages

    private val _stream = MutableSharedFlow<WsStreamEvent>(extraBufferCapacity = 50)
    val stream: SharedFlow<WsStreamEvent> = _stream

    private val _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected.asStateFlow()

    fun connect(party: String = "claimant") {
        if (webSocket != null) return
        val client = OkHttpClient()
        val request = Request.Builder()
            .url("ws://10.0.2.2:8000/api/cases/ws/$caseId?party=$party")
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: okhttp3.Response) {
                _isConnected.value = true
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val frame = json.decodeFromString<WsFrame>(text)
                    val message = when (frame.type) {
                        "user_message" -> NegotiationMessageDto(
                            party = frame.sender ?: "party",
                            text = frame.text ?: "",
                            offer = frame.offer,
                        )
                        "mediator_response" -> NegotiationMessageDto(
                            party = "mediator",
                            text = frame.text ?: "",
                            sentiment = frame.sentiment,
                            phase = frame.phase,
                        )
                        else -> null   // presence_update / private_hint — not chat messages
                    }
                    // Streaming frames are not chat messages — emit separately.
                    when (frame.type) {
                        "mediator_started" -> _stream.tryEmit(WsStreamEvent.Started(frame.phase, frame.round))
                        "mediator_token" -> _stream.tryEmit(WsStreamEvent.Chunk(frame.text ?: ""))
                        else -> Unit
                    }
                    if (message != null) _messages.tryEmit(message)
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: okhttp3.Response?) {
                _isConnected.value = false
                webSocket.close(1001, "Connection failed")
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                _isConnected.value = false
            }
        })
    }

    fun sendMessage(text: String, offer: Double?) {
        val payload = json.encodeToString(
            WsFrame(type = "chat", text = text, offer = offer)
        )
        webSocket?.send(payload)
    }

    fun disconnect() {
        webSocket?.close(1000, "Closing")
        webSocket = null
        _isConnected.value = false
    }
}

package com.negotiateai.app.feature.negotiation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.negotiateai.app.data.SessionManager
import com.negotiateai.app.data.model.NegotiationMessageDto
import com.negotiateai.app.data.repository.CaseRepository
import com.negotiateai.app.data.repository.NegotiationRepository
import com.negotiateai.app.core.network.NegotiationWebSocket
import com.negotiateai.app.core.network.NetworkResult
import com.negotiateai.app.core.network.WsStreamEvent
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

@Composable
fun NegotiationChatScreen(caseId: String, onBack: () -> Unit) {
    val context = LocalContext.current
    val caseRepo = remember(context) { CaseRepository(context) }
    val negotiationRepo = remember(context) { NegotiationRepository(context) }
    val sessionManager = remember(context) { SessionManager(context) }
    val scope = rememberCoroutineScope()

    // Real-time socket — fixed URL, payload and frame parsing.
    val webSocket = remember(caseId) { NegotiationWebSocket(caseId) }
    val wsConnected by webSocket.isConnected.collectAsState()

    var messages by remember { mutableStateOf<List<NegotiationMessageDto>>(emptyList()) }
    var input by remember { mutableStateOf("") }
    var offer by remember { mutableStateOf("") }
    var connectionNote by remember { mutableStateOf("") }

    // Live-streamed mediator reply (accumulates mediator_token frames).
    var streamingText by remember { mutableStateOf("") }
    var streamingPhase by remember { mutableStateOf<String?>(null) }

    fun refresh() {
        scope.launch {
            when (val result = caseRepo.getMessages(caseId)) {
                is NetworkResult.Success -> messages = result.data ?: emptyList()
                else -> Unit
            }
        }
    }

    LaunchedEffect(caseId) {
        refresh()
        // Join the room as the logged-in user's role (claimant/respondent),
        // falling back to claimant when the role isn't persisted yet.
        val role = sessionManager.userRole.first()
        webSocket.connect(party = role ?: "claimant")
    }

    // Live chat frames arrive on the socket — append them as they come.
    // A complete mediator_response commits the bubble and clears the stream.
    LaunchedEffect(webSocket) {
        webSocket.messages.collect { message ->
            messages = messages + message
            streamingText = ""
            streamingPhase = null
        }
    }

    // Streaming frames: mediator_started resets the bubble, mediator_token appends.
    LaunchedEffect(webSocket) {
        webSocket.stream.collect { event ->
            when (event) {
                is WsStreamEvent.Started -> {
                    streamingText = ""
                    streamingPhase = event.phase
                }
                is WsStreamEvent.Chunk -> streamingText += event.text
            }
        }
    }

    DisposableEffect(webSocket) {
        onDispose { webSocket.disconnect() }
    }

    Scaffold { padding ->
        Surface(modifier = Modifier.fillMaxSize().padding(padding)) {
            Column(modifier = Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedButton(onClick = onBack) { Text("Back") }
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Negotiation", style = MaterialTheme.typography.headlineMedium)
                        Text(
                            text = if (wsConnected) "● Live (real-time)" else "○ Reconnecting… (falling back to request/response)",
                            style = MaterialTheme.typography.bodySmall,
                            color = if (wsConnected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error,
                        )
                        messages.takeLast(8).forEach { msg ->
                            Text("${msg.party}: ${msg.text}")
                        }
                        if (streamingText.isNotEmpty()) {
                            Text(
                                text = "mediator (${streamingPhase ?: "thinking"}…): $streamingText▌",
                                color = MaterialTheme.colorScheme.primary,
                            )
                        }
                        OutlinedTextField(input, { input = it }, label = { Text("Message") }, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(offer, { offer = it }, label = { Text("Offer") }, modifier = Modifier.fillMaxWidth())
                        Button(onClick = {
                            val text = input
                            val amount = offer.toDoubleOrNull()
                            if (text.isBlank()) return@Button
                            input = ""
                            offer = ""
                            scope.launch {
                                if (wsConnected) {
                                    // Real-time path: server persists + broadcasts mediator reply.
                                    webSocket.sendMessage(text, amount)
                                } else {
                                    // Fallback: classic request/response, then reload history.
                                    negotiationRepo.negotiate(caseId, text, amount)
                                    refresh()
                                }
                            }
                        }, modifier = Modifier.fillMaxWidth()) { Text("Send") }
                        connectionNote.let { if (it.isNotEmpty()) Text(it, color = MaterialTheme.colorScheme.error) }
                    }
                }
            }
        }
    }
}

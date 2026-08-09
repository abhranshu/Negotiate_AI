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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.negotiateai.app.data.model.NegotiationMessageDto
import com.negotiateai.app.data.repository.CaseRepository
import com.negotiateai.app.data.repository.NegotiationRepository
import com.negotiateai.app.feature.settlement.NetworkResult
import kotlinx.coroutines.launch

@Composable
fun NegotiationChatScreen(caseId: String, onBack: () -> Unit) {
	val context = LocalContext.current
	val caseRepo = remember(context) { CaseRepository(context) }
	val negotiationRepo = remember(context) { NegotiationRepository(context) }
	val scope = rememberCoroutineScope()

	var messages by remember { mutableStateOf<List<NegotiationMessageDto>>(emptyList()) }
	var input by remember { mutableStateOf("") }
	var offer by remember { mutableStateOf("") }

	fun refresh() {
		scope.launch {
			when (val result = caseRepo.getMessages(caseId)) {
				is NetworkResult.Success -> messages = result.data ?: emptyList()
				else -> Unit
			}
		}
	}

	LaunchedEffect(caseId) { refresh() }

	Scaffold { padding ->
		Surface(modifier = Modifier.fillMaxSize().padding(padding)) {
			Column(modifier = Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
				OutlinedButton(onClick = onBack) { Text("Back") }
				Card(modifier = Modifier.fillMaxWidth()) {
					Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
						Text("Negotiation", style = MaterialTheme.typography.headlineMedium)
						messages.takeLast(6).forEach { msg ->
							Text("${msg.party}: ${msg.text}")
						}
						OutlinedTextField(input, { input = it }, label = { Text("Message") }, modifier = Modifier.fillMaxWidth())
						OutlinedTextField(offer, { offer = it }, label = { Text("Offer") }, modifier = Modifier.fillMaxWidth())
						Button(onClick = {
							scope.launch {
								negotiationRepo.negotiate(caseId, input, offer.toDoubleOrNull())
								input = ""
								offer = ""
								refresh()
							}
						}, modifier = Modifier.fillMaxWidth()) { Text("Send") }
					}
				}
			}
		}
	}
}

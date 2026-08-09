package com.negotiateai.app.feature.settlement

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.negotiateai.app.data.model.CaseDto
import com.negotiateai.app.data.repository.CaseRepository

@Composable
fun SettlementScreen(caseId: String, onBack: () -> Unit) {
	val context = LocalContext.current
	val repo = remember(context) { CaseRepository(context) }
	var case by remember { mutableStateOf<CaseDto?>(null) }

	LaunchedEffect(caseId) {
		when (val result = repo.getCase(caseId)) {
			is NetworkResult.Success -> case = result.data
			else -> Unit
		}
	}

	Scaffold { padding ->
		Surface(modifier = Modifier.fillMaxSize().padding(padding)) {
			Column(modifier = Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
				OutlinedButton(onClick = onBack) { Text("Back") }
				Card(modifier = Modifier.fillMaxWidth()) {
					Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
						Text("Settlement", style = MaterialTheme.typography.headlineMedium)
						Text("Agreed amount: ${case?.agreementAmount ?: 0.0}")
						Text("Status: ${case?.status?.name?.lowercase()?.replace('_', ' ') ?: "unknown"}")
						Text(case?.predictionRecommendation ?: "Generate settlement after negotiation")
					}
				}
			}
		}
	}
}

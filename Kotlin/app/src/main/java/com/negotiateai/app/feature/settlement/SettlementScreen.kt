package com.negotiateai.app.feature.settlement

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
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
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.negotiateai.app.data.model.CaseDto
import com.negotiateai.app.data.model.SettlementDto
import com.negotiateai.app.data.repository.CaseRepository
import com.negotiateai.app.core.network.NetworkResult
import kotlinx.coroutines.launch

@Composable
fun SettlementScreen(caseId: String, onBack: () -> Unit) {
    val context = LocalContext.current
    val repo = remember(context) { CaseRepository(context) }
    val scope = rememberCoroutineScope()

    var case by remember { mutableStateOf<CaseDto?>(null) }
    var settlement by remember { mutableStateOf<SettlementDto?>(null) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    fun loadCase() {
        scope.launch {
            when (val result = repo.getCase(caseId)) {
                is NetworkResult.Success -> case = result.data
                else -> Unit
            }
        }
    }

    fun generate() {
        loading = true
        error = null
        scope.launch {
            when (val result = repo.generateSettlement(caseId)) {
                is NetworkResult.Success -> settlement = result.data
                is NetworkResult.Error -> error = result.message
                is NetworkResult.Loading -> Unit
            }
            loading = false
            loadCase()
        }
    }

    LaunchedEffect(caseId) {
        loadCase()
        // Show an existing agreement if one was already generated.
        when (val result = repo.getSettlement(caseId)) {
            is NetworkResult.Success -> settlement = result.data
            else -> Unit   // 404 = none generated yet; show the generate button
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

                        Button(
                            onClick = { generate() },
                            enabled = !loading,
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            if (loading) {
                                CircularProgressIndicator(modifier = Modifier.padding(end = 8.dp))
                                Text("Generating legal agreement…")
                            } else {
                                Text(if (settlement != null) "🔄 Regenerate Agreement" else "🚀 Generate Settlement Agreement")
                            }
                        }
                    }
                }

                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }

                val s = settlement
                if (s != null) {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("Agreement ${s.agreementId} • ${s.date}", style = MaterialTheme.typography.titleMedium)
                            Text(
                                text = if (s.isValid) "✓ Validated (all clauses present)" else "⚠ Review needed",
                                color = if (s.isValid) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error,
                            )
                            if (s.validationNotes.isNotEmpty()) {
                                Text("Notes:")
                                s.validationNotes.forEach { Text("  • $it") }
                            }
                            Text(s.agreementText, style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                } else if (!loading && error == null) {
                    Text(case?.predictionRecommendation ?: "Reach an agreement in negotiation, then generate the settlement agreement here.")
                }
            }
        }
    }
}

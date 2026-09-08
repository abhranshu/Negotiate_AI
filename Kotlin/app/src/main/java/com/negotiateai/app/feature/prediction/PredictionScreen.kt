package com.negotiateai.app.feature.prediction

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
import com.negotiateai.app.data.model.PredictionDto
import com.negotiateai.app.data.repository.CaseRepository
import com.negotiateai.app.core.network.NetworkResult
import kotlinx.coroutines.launch

@Composable
fun PredictionScreen(caseId: String, onBack: () -> Unit) {
    val context = LocalContext.current
    val repo = remember(context) { CaseRepository(context) }
    val scope = rememberCoroutineScope()

    var case by remember { mutableStateOf<CaseDto?>(null) }
    var prediction by remember { mutableStateOf<PredictionDto?>(null) }
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

    fun runPrediction() {
        loading = true
        error = null
        scope.launch {
            when (val result = repo.runPrediction(caseId)) {
                is NetworkResult.Success -> prediction = result.data
                is NetworkResult.Error -> error = result.message
                is NetworkResult.Loading -> Unit
            }
            loading = false
            loadCase()
        }
    }

    LaunchedEffect(caseId) { loadCase() }

    Scaffold { padding ->
        Surface(modifier = Modifier.fillMaxSize().padding(padding)) {
            Column(modifier = Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedButton(onClick = onBack) { Text("Back") }

                Button(
                    onClick = { runPrediction() },
                    enabled = !loading,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    if (loading) {
                        CircularProgressIndicator(modifier = Modifier.padding(end = 8.dp))
                        Text("Running ML prediction…")
                    } else {
                        Text("🚀 Run ML Prediction")
                    }
                }

                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }

                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Prediction", style = MaterialTheme.typography.headlineMedium)

                        val p = prediction
                        if (p != null) {
                            Text("Settlement probability: ${(p.settlementProbability * 100).toInt()}%")
                            Text("Range: ₹${p.settlementRangeLow.toInt()} - ₹${p.settlementRangeHigh.toInt()}")
                            Text("Adjudication days: ~${p.adjudicationDays} days")
                            Text("Confidence: ${p.confidenceBand}")
                            if (p.recommendation.isNotBlank()) {
                                Text(p.recommendation)
                            }
                            if (p.keyFactors.isNotEmpty()) {
                                Text("Key factors:")
                                p.keyFactors.take(5).forEach { f ->
                                    Text(
                                        "  ${if (f.direction == "positive") "▲" else "▼"} " +
                                            "${f.factor.replace('_', ' ')} (${f.impact})"
                                    )
                                }
                            }
                        } else {
                            // Fall back to whatever was persisted on the case row.
                            Text("Settlement probability: ${case?.settlementProbability ?: 0.0}")
                            Text("Range: ${case?.settlementRangeLow ?: 0.0} - ${case?.settlementRangeHigh ?: 0.0}")
                            Text("Adjudication days: ${case?.adjudicationDays ?: 0}")
                            Text(case?.predictionRecommendation ?: "No prediction yet — press Run ML Prediction")
                        }
                    }
                }
            }
        }
    }
}

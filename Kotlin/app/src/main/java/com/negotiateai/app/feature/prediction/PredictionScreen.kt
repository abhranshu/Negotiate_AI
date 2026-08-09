package com.negotiateai.app.feature.prediction

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
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
import com.negotiateai.app.feature.settlement.NetworkResult

@Composable
fun PredictionScreen(caseId: String, onBack: () -> Unit) {
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
						Text("Prediction", style = MaterialTheme.typography.headlineMedium)
						Text("Settlement probability: ${case?.settlementProbability ?: 0.0}")
						Text("Range: ${case?.settlementRangeLow ?: 0.0} - ${case?.settlementRangeHigh ?: 0.0}")
						Text("Adjudication days: ${case?.adjudicationDays ?: 0}")
						Text(case?.predictionRecommendation ?: "Prediction data not available yet")
					}
				}
			}
		}
	}
}

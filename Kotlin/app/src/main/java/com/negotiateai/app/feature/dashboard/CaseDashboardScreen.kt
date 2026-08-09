package com.negotiateai.app.feature.dashboard

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import com.negotiateai.app.data.model.CaseListItem
import com.negotiateai.app.data.repository.CaseRepository
import com.negotiateai.app.core.network.NetworkResult
import kotlinx.coroutines.launch

@Composable
fun CaseDashboardScreen(
	onCaseClick: (String) -> Unit,
	onCreateCase: () -> Unit,
	onLogout: () -> Unit,
) {
	val context = LocalContext.current
	val repo = remember(context) { CaseRepository(context) }
	val scope = rememberCoroutineScope()

	var cases by remember { mutableStateOf<List<CaseListItem>>(emptyList()) }
	var loading by remember { mutableStateOf(true) }
	var error by remember { mutableStateOf<String?>(null) }

	LaunchedEffect(Unit) {
		loading = true
		when (val result = repo.listCases()) {
			is NetworkResult.Success -> cases = result.data ?: emptyList()
			is NetworkResult.Error -> error = result.message
			is NetworkResult.Loading -> Unit
		}
		loading = false
	}

	Scaffold { padding ->
		Surface(modifier = Modifier.fillMaxSize().padding(padding)) {
			Column(modifier = Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
				Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
					Column {
						Text("Cases", style = MaterialTheme.typography.headlineMedium)
						Text("Backend-synced dispute dashboard", style = MaterialTheme.typography.bodyMedium)
					}
					OutlinedButton(onClick = onLogout) { Text("Logout") }
				}

				Button(onClick = onCreateCase, modifier = Modifier.fillMaxWidth()) { Text("New case") }

				error?.let { Text(it, color = MaterialTheme.colorScheme.error) }

				if (loading) {
					CircularProgressIndicator()
				} else {
					LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
						items(cases) { case ->
							Card(
								modifier = Modifier
									.fillMaxWidth()
									.clickable { onCaseClick(case.id) }
									.padding(2.dp)
							) {
								Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
									Text(case.caseNumber ?: case.id, style = MaterialTheme.typography.titleMedium)
									Text(case.disputeType?.name?.replace('_', ' ') ?: "Dispute", style = MaterialTheme.typography.bodyMedium)
									Text("Claim: ${case.claimAmount ?: 0.0}")
									Text("Status: ${case.status.name.lowercase().replace('_', ' ')}")
								}
							}
						}
					}
				}
			}
		}
	}
}

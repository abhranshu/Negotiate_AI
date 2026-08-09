package com.negotiateai.app.feature.case

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.negotiateai.app.data.model.CreateCaseRequest
import com.negotiateai.app.data.model.DisputeType
import com.negotiateai.app.data.repository.CaseRepository
import com.negotiateai.app.feature.settlement.NetworkResult
import kotlinx.coroutines.launch

@Composable
fun CreateCaseScreen(
    onCaseCreated: (String) -> Unit,
    onBack: () -> Unit
) {

    val context = LocalContext.current
    val repo = remember(context) { CaseRepository(context) }
    val scope = rememberCoroutineScope()

    var disputeType by remember {
        mutableStateOf(DisputeType.DELAYED_PAYMENT)
    }

    var claimAmount by remember { mutableStateOf("") }
    var overdueDays by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var state by remember { mutableStateOf("") }
    var industry by remember { mutableStateOf("") }
    var respondentEmail by remember { mutableStateOf("") }

    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    Scaffold { padding ->

        Surface(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
        ) {

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {

                Text(
                    text = "Create Case",
                    style = MaterialTheme.typography.headlineMedium
                )

                OutlinedTextField(
                    value = claimAmount,
                    onValueChange = { claimAmount = it },
                    label = { Text("Claim Amount") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = overdueDays,
                    onValueChange = { overdueDays = it },
                    label = { Text("Overdue Days") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("Description") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = state,
                    onValueChange = { state = it },
                    label = { Text("State") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = industry,
                    onValueChange = { industry = it },
                    label = { Text("Industry") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = respondentEmail,
                    onValueChange = { respondentEmail = it },
                    label = { Text("Respondent Email") },
                    modifier = Modifier.fillMaxWidth()
                )

                error?.let {
                    Text(
                        text = it,
                        color = MaterialTheme.colorScheme.error
                    )
                }

                Button(
                    onClick = {
                        scope.launch {

                            loading = true
                            error = null

                            when (
                                val result = repo.createCase(
                                    CreateCaseRequest(
                                        disputeType = disputeType,
                                        claimAmount = claimAmount.toDoubleOrNull(),
                                        overdueDays = overdueDays.toIntOrNull(),
                                        description = description.ifBlank { null },
                                        state = state.ifBlank { null },
                                        industry = industry.ifBlank { null },
                                        respondentEmail = respondentEmail.ifBlank { null }
                                    )
                                )
                            ) {

                                is NetworkResult.Success -> {
                                    loading = false
                                    onCaseCreated(result.data?.id.orEmpty())
                                }

                                is NetworkResult.Error -> {
                                    loading = false
                                    error = result.message
                                }

                                is NetworkResult.Loading -> {
                                    loading = true
                                }
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !loading
                ) {

                    if (loading) {
                        CircularProgressIndicator()
                    } else {
                        Text("Create")
                    }
                }

                OutlinedButton(
                    onClick = onBack,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Back")
                }
            }
        }
    }
}

private val StatusPending = androidx.compose.ui.graphics.Color(0xFFE65100)
private val StatusPendingBg = androidx.compose.ui.graphics.Color(0xFFFFF3E0)
private val StatusEscalated = androidx.compose.ui.graphics.Color(0xFFB71C1C)
private val StatusEscalatedBg = androidx.compose.ui.graphics.Color(0xFFFFEBEE)
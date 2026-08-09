package com.negotiateai.app.feature.case

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Upload
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.negotiateai.app.core.theme.ChipShape
import com.negotiateai.app.core.theme.PredictionHigh
import com.negotiateai.app.core.theme.PredictionLow
import com.negotiateai.app.core.theme.PredictionMid
import com.negotiateai.app.data.model.CaseDto
import com.negotiateai.app.data.model.CaseStatus
import com.negotiateai.app.data.model.DocumentDto
import com.negotiateai.app.data.repository.CaseRepository
import com.negotiateai.app.core.network.NetworkResult

@Composable
fun CaseDetailScreen(
    caseId: String,
    onNegotiate: () -> Unit,
    onPredict: () -> Unit,
    onSettle: () -> Unit,
    onBack: () -> Unit,
) {
    val context = LocalContext.current
    val repo = remember(context) { CaseRepository(context) }
    val scope = rememberCoroutineScope()

    var case by remember { mutableStateOf<CaseDto?>(null) }
    var loading by remember { mutableStateOf(true) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(caseId) {
        loading = true
        when (val result = repo.getCase(caseId)) {
            is NetworkResult.Success -> case = result.data
            is NetworkResult.Error -> error = result.message
            is NetworkResult.Loading -> Unit
        }
        loading = false
    }

    Scaffold { padding ->
        Surface(modifier = Modifier.fillMaxSize().padding(padding)) {
            Column(modifier = Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                    OutlinedButton(onClick = onBack) { Text("Back") }
                    Button(onClick = onPredict) { Text("Predict") }
                }

                if (loading) CircularProgressIndicator()
                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }

                case?.let {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text(it.caseNumber ?: it.id, style = MaterialTheme.typography.headlineSmall)
                            Text(it.description ?: "No description")
                            Text("Status: ${it.status.name.lowercase().replace('_', ' ')}")
                            Text("Claim: ${it.claimAmount ?: 0.0}")
                            Text("Probability: ${it.settlementProbability ?: 0.0}")
                        }
                    }

                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                        Button(onClick = onNegotiate, modifier = Modifier.weight(1f)) { Text("Negotiate") }
                        Button(onClick = onSettle, modifier = Modifier.weight(1f)) { Text("Settle") }
                    }
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    AiInsightCard(
                        prediction = it.predictionRecommendation ?: "No prediction available yet.",
                        confidence = (it.settlementProbability ?: 0.0).toFloat(),
                        recommendedSettlement = it.settlementRangeHigh
                    )
                }
            }
        }
    }
}

@Composable
fun AiInsightCard(prediction: String, confidence: Float, recommendedSettlement: Double?) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceContainer
        )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Default.AutoAwesome,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    "AI Analysis",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary
                )
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Text(
                prediction,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    "Confidence",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    "${(confidence * 100).toInt()}%",
                    style = MaterialTheme.typography.labelSmall,
                    color = when {
                        confidence >= 0.7f -> PredictionHigh
                        confidence >= 0.4f -> PredictionMid
                        else -> PredictionLow
                    },
                    fontWeight = FontWeight.Bold
                )
            }
            
            if (recommendedSettlement != null) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "Recommended Settlement: ${formatCurrency(recommendedSettlement, "USD")}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Medium
                )
            }
        }
    }
}

@Composable
fun OverviewTab(case: CaseDto) {
    Column {
        Text(
            "Case Summary",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = MaterialTheme.colorScheme.onSurface
        )
        Spacer(modifier = Modifier.height(12.dp))
        
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surfaceContainerLowest
            ),
            border = CardDefaults.outlinedCardBorder()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    case.caseStrength ?: "Analysis not yet generated. Upload documents to enable analysis.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (case.caseStrength != null) 
                        MaterialTheme.colorScheme.onSurface 
                    else 
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
                
                if (case.caseStrength == null) {
                    Spacer(modifier = Modifier.height(16.dp))
                    Button(
                        onClick = { /* Trigger analysis */ },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = MaterialTheme.colorScheme.primaryContainer,
                            contentColor = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    ) {
                        Text("Generate Summary")
                    }
                }
            }
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Key dates
        Text(
            "Timeline",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = MaterialTheme.colorScheme.onSurface
        )
        Spacer(modifier = Modifier.height(12.dp))
        
        TimelineItem(
            title = "Case Filed",
            date = case.createdAt,
            isCompleted = true
        )
        TimelineItem(
            title = "Negotiation Started",
            date = if (case.status != CaseStatus.DRAFT) "In progress" else "Not started",
            isCompleted = case.status != CaseStatus.DRAFT
        )
        TimelineItem(
            title = "Resolution",
            date = if (case.agreementAmount != null) "Settled" else "Pending",
            isCompleted = case.status == CaseStatus.AGREEMENT || case.status == CaseStatus.CLOSED
        )
    }
}

@Composable
fun TimelineItem(title: String, date: String, isCompleted: Boolean) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(12.dp)
                .background(
                    color = if (isCompleted) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant,
                    shape = ChipShape
                )
        )
        Spacer(modifier = Modifier.width(16.dp))
        Column {
            Text(
                title,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface,
                fontWeight = FontWeight.Medium
            )
            Text(
                date,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
fun DocumentsTab(
    documents: List<DocumentDto>,
    isUploading: Boolean,
    onUpload: () -> Unit
) {
    Column {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "${documents.size} Documents",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface
            )
            
            Button(
                onClick = onUpload,
                enabled = !isUploading,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary
                ),
                modifier = Modifier.height(40.dp)
            ) {
                if (isUploading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        color = MaterialTheme.colorScheme.onPrimary,
                        strokeWidth = 2.dp
                    )
                } else {
                    Icon(Icons.Default.Upload, contentDescription = null, modifier = Modifier.size(16.dp))
                }
                Spacer(modifier = Modifier.width(8.dp))
                Text("Upload")
            }
        }
        
        Spacer(modifier = Modifier.height(12.dp))
        
        if (documents.isEmpty()) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceContainerLow
                ),
                border = CardDefaults.outlinedCardBorder()
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(32.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Icon(
                        Icons.Default.Description,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(48.dp)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        "No documents yet",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Text(
                        "Upload contracts, emails, or evidence to enable AI analysis",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        } else {
            documents.forEach { document ->
                DocumentItem(document = document)
                Spacer(modifier = Modifier.height(8.dp))
            }
        }
    }
}

@Composable
fun DocumentItem(document: DocumentDto) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceContainerLowest
        ),
        border = CardDefaults.outlinedCardBorder()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                Icons.Default.Description,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(24.dp)
            )
            Spacer(modifier = Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    document.filename,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                    fontWeight = FontWeight.Medium
                )
                Text(
                    "Uploaded: ${document.uploadedAt} • ${document.docType?.uppercase() ?: "UNKNOWN"}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            if (document.isValid) {
                Icon(
                    Icons.Default.AutoAwesome,
                    contentDescription = "AI Validated",
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(16.dp)
                )
            }
        }
    }
}

@Composable
fun HistoryTab() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(32.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            "Activity history coming soon",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

// Helper function
fun formatCurrency(amount: Double?, currency: String): String {
    return if (amount != null) {
        "$currency ${String.format("%,.2f", amount)}"
    } else {
        "Not specified"
    }
}

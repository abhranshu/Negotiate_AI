package com.negotiateai.app.feature.case

import android.Manifest
import android.content.Context
import android.media.MediaRecorder
import android.net.Uri
import android.provider.OpenableColumns
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.material.icons.filled.Mic
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
import java.io.File
import kotlinx.coroutines.launch

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

    // Module 1 (voice) + Module 2 (documents) state
    var documents by remember { mutableStateOf<List<DocumentDto>>(emptyList()) }
    var mediaRecorder by remember { mutableStateOf<MediaRecorder?>(null) }
    var audioFile by remember { mutableStateOf<File?>(null) }
    var isRecording by remember { mutableStateOf(false) }
    var voiceBusy by remember { mutableStateOf(false) }
    var voiceStatus by remember { mutableStateOf<String?>(null) }
    var docsBusy by remember { mutableStateOf(false) }
    var docsStatus by remember { mutableStateOf<String?>(null) }

    fun loadCase() {
        scope.launch {
            when (val result = repo.getCase(caseId)) {
                is NetworkResult.Success -> case = result.data
                is NetworkResult.Error -> error = result.message
                is NetworkResult.Loading -> Unit
            }
        }
    }

    fun loadDocuments() {
        scope.launch {
            when (val result = repo.getDocuments(caseId)) {
                is NetworkResult.Success -> documents = result.data ?: emptyList()
                else -> Unit
            }
        }
    }

    fun startRecording() {
        if (isRecording) return
        voiceStatus = null
        try {
            val file = File(context.cacheDir, "voice_note_${System.currentTimeMillis()}.m4a")
            val recorder = MediaRecorder().apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setOutputFile(file.absolutePath)
                prepare()
                start()
            }
            audioFile = file
            mediaRecorder = recorder
            isRecording = true
            voiceStatus = "Recording… tap Stop to upload"
        } catch (e: Exception) {
            voiceStatus = "Could not start recording: ${e.message}"
        }
    }

    fun stopAndUpload() {
        val recorder = mediaRecorder ?: return
        val file = audioFile ?: return
        isRecording = false
        voiceBusy = true
        voiceStatus = "Uploading voice note…"
        scope.launch {
            try {
                recorder.stop()
            } catch (e: Exception) {
                // recorder throws if the clip was too short — still try to upload
            } finally {
                try { recorder.release() } catch (_: Exception) {}
            }
            mediaRecorder = null
            when (val result = repo.uploadVoice(caseId, file)) {
                is NetworkResult.Success -> {
                    voiceStatus = "Voice processed — case auto-filled"
                    loadCase()
                }
                is NetworkResult.Error -> voiceStatus = result.message
                is NetworkResult.Loading -> Unit
            }
            file.delete()
            voiceBusy = false
        }
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) startRecording() else voiceStatus = "Microphone permission denied"
    }

    // Pick one or more files and upload them for Module 2 classification.
    val docPicker = rememberLauncherForActivityResult(
        ActivityResultContracts.GetMultipleContents()
    ) { uris ->
        if (uris.isEmpty()) return@rememberLauncherForActivityResult
        scope.launch {
            docsBusy = true
            docsStatus = null
            val files = uris.mapNotNull { uri -> uriToCacheFile(context, uri) }
            when (val result = repo.uploadDocuments(caseId, files)) {
                is NetworkResult.Success -> {
                    docsStatus = "Uploaded ${result.data?.size ?: files.size} document(s)"
                    loadDocuments()
                }
                is NetworkResult.Error -> docsStatus = result.message
                is NetworkResult.Loading -> Unit
            }
            docsBusy = false
        }
    }

    LaunchedEffect(caseId) {
        loading = true
        loadCase()
        loadDocuments()
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

                    Spacer(modifier = Modifier.height(16.dp))

                    VoiceCard(
                        isRecording = isRecording,
                        busy = voiceBusy,
                        status = voiceStatus,
                        onRecord = { permissionLauncher.launch(Manifest.permission.RECORD_AUDIO) },
                        onStop = { stopAndUpload() },
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    DocumentsCard(
                        documents = documents,
                        busy = docsBusy,
                        status = docsStatus,
                        onUpload = {
                            docPicker.launch("application/pdf,application/msword,image/*,text/plain")
                        },
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

// Helper: copy a content:// URI (from the document picker) into a cache file so
// it can be uploaded as a multipart part.
private fun uriToCacheFile(context: Context, uri: Uri): File? {
    return try {
        val resolver = context.contentResolver
        val displayName = resolver.query(uri, null, null, null, null)?.use { cursor ->
            val idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            if (idx >= 0 && cursor.moveToFirst()) cursor.getString(idx) else null
        }
        val safeName = (displayName ?: "upload_${System.currentTimeMillis()}.bin")
            .substringAfterLast('/')
            .ifBlank { "upload_${System.currentTimeMillis()}.bin" }
        val file = File(context.cacheDir, safeName)
        resolver.openInputStream(uri)?.use { input ->
            file.outputStream().use { output -> input.copyTo(output) }
        }
        file
    } catch (e: Exception) {
        null
    }
}

@Composable
fun VoiceCard(
    isRecording: Boolean,
    busy: Boolean,
    status: String?,
    onRecord: () -> Unit,
    onStop: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("🎙️ Voice Dispute Intake", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Text(
                "Record a voice note; Whisper ASR + NER auto-fills the dispute form.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (isRecording) {
                    Button(onClick = onStop, enabled = !busy, modifier = Modifier.weight(1f)) {
                        Icon(Icons.Default.Mic, contentDescription = null)
                        Text("Stop & Upload")
                    }
                } else {
                    OutlinedButton(onClick = onRecord, enabled = !busy, modifier = Modifier.weight(1f)) {
                        Icon(Icons.Default.Mic, contentDescription = null)
                        Text("Record Voice Note")
                    }
                }
            }
            status?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
        }
    }
}

@Composable
fun DocumentsCard(
    documents: List<DocumentDto>,
    busy: Boolean,
    status: String?,
    onUpload: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    "📄 Documents (${documents.size})",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                )
                Button(onClick = onUpload, enabled = !busy) {
                    Icon(Icons.Default.Upload, contentDescription = null)
                    Text("Upload")
                }
            }
            if (busy) {
                CircularProgressIndicator()
            } else if (documents.isEmpty()) {
                Text(
                    "No documents yet — upload contracts, invoices, or delivery proofs for AI analysis.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            } else {
                documents.forEach { DocumentItem(document = it) }
            }
            status?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
        }
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

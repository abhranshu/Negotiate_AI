package com.negotiateai.app.feature.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
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
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.negotiateai.app.data.model.RegisterRequest
import com.negotiateai.app.data.model.UserRole
import com.negotiateai.app.data.repository.AuthRepository
import com.negotiateai.app.feature.settlement.NetworkResult
import kotlinx.coroutines.launch

@Composable
fun AuthScreen(onAuthSuccess: () -> Unit) {
    val context = LocalContext.current
    val repo = remember(context) { AuthRepository(context) }
    val scope = rememberCoroutineScope()

    var isLoginMode by remember { mutableStateOf(true) }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var fullName by remember { mutableStateOf("") }
    var companyName by remember { mutableStateOf("") }
    var isClaimant by remember { mutableStateOf(true) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    Scaffold { padding ->
        Surface(modifier = Modifier.fillMaxSize().padding(padding)) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp),
                verticalArrangement = Arrangement.Center
            ) {
                Text("NegotiateAI", style = MaterialTheme.typography.headlineMedium)
                Text("MSME dispute resolution", style = MaterialTheme.typography.bodyMedium)
                Spacer(Modifier.height(24.dp))

                if (!isLoginMode) {
                    OutlinedTextField(fullName, { fullName = it }, label = { Text("Full name") }, modifier = Modifier.fillMaxWidth())
                    Spacer(Modifier.height(12.dp))
                    OutlinedTextField(companyName, { companyName = it }, label = { Text("Company name") }, modifier = Modifier.fillMaxWidth())
                    Spacer(Modifier.height(12.dp))
                }

                OutlinedTextField(email, { email = it }, label = { Text("Email") }, modifier = Modifier.fillMaxWidth())
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(password, { password = it }, label = { Text("Password") }, visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth())
                Spacer(Modifier.height(12.dp))

                if (!isLoginMode) {
                    Text("Role")
                    HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))
                    OutlinedButton(onClick = { isClaimant = true }) { Text(if (isClaimant) "Claimant" else "Set as claimant") }
                }

                error?.let {
                    Spacer(Modifier.height(12.dp))
                    Text(it, color = MaterialTheme.colorScheme.error)
                }

                Spacer(Modifier.height(20.dp))
                Button(
                    onClick = {
                        scope.launch {
                            loading = true
                            error = null
                            val authResult = if (isLoginMode) {
                                repo.login(email.trim(), password)
                            } else {
                                val reg = repo.register(
                                    RegisterRequest(
                                        email = email.trim(),
                                        password = password,
                                        fullName = fullName.trim(),
                                        role = if (isClaimant) UserRole.CLAIMANT else UserRole.RESPONDENT,
                                        companyName = companyName.takeIf { it.isNotBlank() }
                                    )
                                )
                                when (reg) {
                                    is NetworkResult.Success -> repo.login(email.trim(), password)
                                    is NetworkResult.Error -> reg
                                    is NetworkResult.Loading -> reg
                                }
                            }

                            loading = false
                            when (authResult) {
                                is NetworkResult.Success -> onAuthSuccess()
                                is NetworkResult.Error -> error = authResult.message
                                is NetworkResult.Loading -> Unit
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    if (loading) CircularProgressIndicator(modifier = Modifier.height(18.dp)) else Text(if (isLoginMode) "Sign in" else "Create account")
                }

                Spacer(Modifier.height(12.dp))
                OutlinedButton(onClick = { isLoginMode = !isLoginMode }, modifier = Modifier.fillMaxWidth()) {
                    Text(if (isLoginMode) "Need an account? Register" else "Have an account? Sign in")
                }
            }
        }
    }
}

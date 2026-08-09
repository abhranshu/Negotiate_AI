package com.negotiateai.app

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import com.negotiateai.app.data.SessionManager
import com.negotiateai.app.navigation.AppNavigation

@Composable
fun NegotiateAiApp() {
	val context = LocalContext.current
	val sessionManager = remember(context) { SessionManager(context) }
	AppNavigation(sessionManager = sessionManager)
}

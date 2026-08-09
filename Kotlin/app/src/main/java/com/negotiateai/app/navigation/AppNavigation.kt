package com.negotiateai.app.navigation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.negotiateai.app.data.SessionManager
import com.negotiateai.app.feature.auth.AuthScreen
import com.negotiateai.app.feature.case.CaseDetailScreen
import com.negotiateai.app.feature.case.CreateCaseScreen
import com.negotiateai.app.feature.dashboard.CaseDashboardScreen
import com.negotiateai.app.feature.negotiation.NegotiationChatScreen
import com.negotiateai.app.feature.prediction.PredictionScreen
import com.negotiateai.app.feature.settlement.SettlementScreen
import kotlinx.coroutines.launch

object Routes {
    const val SPLASH = "splash"
    const val AUTH = "auth"
    const val DASHBOARD = "dashboard"
    const val CREATE_CASE = "create_case"
    const val CASE_DETAIL = "case_detail/{caseId}"
    const val NEGOTIATION = "negotiation/{caseId}"
    const val PREDICTION = "prediction/{caseId}"
    const val SETTLEMENT = "settlement/{caseId}"

    fun caseDetail(caseId: String) = "case_detail/$caseId"
    fun negotiation(caseId: String) = "negotiation/$caseId"
    fun prediction(caseId: String) = "prediction/$caseId"
    fun settlement(caseId: String) = "settlement/$caseId"
}

@Composable
fun AppNavigation(
    sessionManager: SessionManager,
    navController: NavHostController = rememberNavController(),
) {
    NavHost(navController = navController, startDestination = Routes.SPLASH) {
        composable(Routes.SPLASH) {
            SplashGate(
                sessionManager = sessionManager,
                onGoAuth = {
                    navController.navigate(Routes.AUTH) {
                        popUpTo(Routes.SPLASH) { inclusive = true }
                    }
                },
                onGoDashboard = {
                    navController.navigate(Routes.DASHBOARD) {
                        popUpTo(Routes.SPLASH) { inclusive = true }
                    }
                }
            )
        }

        composable(Routes.AUTH) {
            AuthScreen(onAuthSuccess = {
                navController.navigate(Routes.DASHBOARD) {
                    popUpTo(Routes.AUTH) { inclusive = true }
                }
            })
        }

        composable(Routes.DASHBOARD) {
            CaseDashboardScreen(
                onCaseClick = { navController.navigate(Routes.caseDetail(it)) },
                onCreateCase = { navController.navigate(Routes.CREATE_CASE) },
                onLogout = {
                    val scope = rememberCoroutineScope()
                    scope.launch {
                        sessionManager.clearAuthToken()
                        sessionManager.clearUserId()
                        navController.navigate(Routes.AUTH) {
                            popUpTo(0) { inclusive = true }
                        }
                    }
                }
            )
        }

        composable(Routes.CREATE_CASE) {
            CreateCaseScreen(
                onCaseCreated = { caseId ->
                    navController.navigate(Routes.caseDetail(caseId)) {
                        popUpTo(Routes.DASHBOARD)
                    }
                },
                onBack = { navController.popBackStack() }
            )
        }

        composable(Routes.CASE_DETAIL) { backStackEntry ->
            val caseId = backStackEntry.arguments?.getString("caseId").orEmpty()
            CaseDetailScreen(
                caseId = caseId,
                onNegotiate = { navController.navigate(Routes.negotiation(caseId)) },
                onPredict = { navController.navigate(Routes.prediction(caseId)) },
                onSettle = { navController.navigate(Routes.settlement(caseId)) },
                onBack = { navController.popBackStack() }
            )
        }

        composable(Routes.NEGOTIATION) { backStackEntry ->
            val caseId = backStackEntry.arguments?.getString("caseId").orEmpty()
            NegotiationChatScreen(caseId = caseId, onBack = { navController.popBackStack() })
        }

        composable(Routes.PREDICTION) { backStackEntry ->
            val caseId = backStackEntry.arguments?.getString("caseId").orEmpty()
            PredictionScreen(caseId = caseId, onBack = { navController.popBackStack() })
        }

        composable(Routes.SETTLEMENT) { backStackEntry ->
            val caseId = backStackEntry.arguments?.getString("caseId").orEmpty()
            SettlementScreen(caseId = caseId, onBack = { navController.popBackStack() })
        }
    }
}

@Composable
private fun SplashGate(
    sessionManager: SessionManager,
    onGoAuth: () -> Unit,
    onGoDashboard: () -> Unit,
) {
    val token by sessionManager.authToken.collectAsState(initial = null)
    LaunchedEffect(token) {
        if (token.isNullOrBlank()) onGoAuth() else onGoDashboard()
    }
    Surface(modifier = Modifier.fillMaxSize()) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                CircularProgressIndicator()
                Text("Loading NegotiateAI", style = MaterialTheme.typography.titleMedium)
            }
        }
    }
}
package com.negotiateai.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.negotiateai.app.core.theme.NegotiateAITheme
import com.negotiateai.app.navigation.AppNavigation

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            NegotiateAITheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    NegotiateAiApp()
                }
            }
        }
    }
}

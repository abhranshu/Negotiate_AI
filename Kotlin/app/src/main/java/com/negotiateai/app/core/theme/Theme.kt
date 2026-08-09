package com.negotiateai.app.core.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// ── Light scheme (primary mode — gov-tech is light-first) ─────────
private val LightColorScheme = lightColorScheme(
    primary = PrimaryContainer,              // #006666 per DESIGN.md "Primary"
    onPrimary = OnPrimary,
    primaryContainer = PrimaryFixed,         // light teal fill
    onPrimaryContainer = OnPrimaryFixedVariant,
    inversePrimary = InversePrimary,

    secondary = Secondary,
    onSecondary = OnSecondary,
    secondaryContainer = SecondaryContainer,
    onSecondaryContainer = OnSecondaryContainer,

    tertiary = Tertiary,
    onTertiary = OnTertiary,
    tertiaryContainer = TertiaryFixed,
    onTertiaryContainer = OnTertiaryFixedVariant,

    error = Error,
    onError = OnError,
    errorContainer = ErrorContainer,
    onErrorContainer = OnErrorContainer,

    background = Background,
    onBackground = OnBackground,

    surface = Surface,
    onSurface = OnSurface,
    surfaceVariant = SurfaceVariant,
    onSurfaceVariant = OnSurfaceVariant,
    surfaceTint = SurfaceTint,

    surfaceDim = SurfaceDim,
    surfaceBright = SurfaceBright,
    surfaceContainerLowest = SurfaceContainerLowest,
    surfaceContainerLow = SurfaceContainerLow,
    surfaceContainer = SurfaceContainer,
    surfaceContainerHigh = SurfaceContainerHigh,
    surfaceContainerHighest = SurfaceContainerHighest,

    inverseSurface = InverseSurface,
    inverseOnSurface = InverseOnSurface,

    outline = Outline,
    outlineVariant = OutlineVariant,
)

// ── Dark scheme (fallback — tones flipped for legibility) ─────────
private val DarkColorScheme = darkColorScheme(
    primary = PrimaryFixedDim,               // #86D4D3 on dark
    onPrimary = OnPrimaryFixed,
    primaryContainer = Primary,              // deep teal chip
    onPrimaryContainer = OnPrimaryContainer,
    inversePrimary = Primary,

    secondary = SecondaryFixedDim,
    onSecondary = OnSecondaryFixed,
    secondaryContainer = OnSecondaryFixedVariant,
    onSecondaryContainer = SecondaryFixed,

    tertiary = TertiaryFixedDim,
    onTertiary = OnTertiaryFixed,
    tertiaryContainer = OnTertiaryFixedVariant,
    onTertiaryContainer = TertiaryFixed,

    error = Color(0xFFFFB4AB),
    onError = Color(0xFF690005),
    errorContainer = OnErrorContainer,
    onErrorContainer = ErrorContainer,

    background = Color(0xFF111415),
    onBackground = InverseOnSurface,

    surface = Color(0xFF111415),
    onSurface = InverseOnSurface,
    surfaceVariant = OnSurfaceVariant,
    onSurfaceVariant = OutlineVariant,
    surfaceTint = PrimaryFixedDim,

    surfaceDim = Color(0xFF111415),
    surfaceBright = Color(0xFF373A3B),
    surfaceContainerLowest = Color(0xFF0C0F10),
    surfaceContainerLow = OnSurface,
    surfaceContainer = Color(0xFF1D2021),
    surfaceContainerHigh = Color(0xFF272A2B),
    surfaceContainerHighest = InverseSurface,

    inverseSurface = InverseOnSurface,
    inverseOnSurface = InverseSurface,

    outline = Color(0xFF899392),
    outlineVariant = OnSurfaceVariant,
)

// ── Theme entry point ──────────────────────────────────────────────
@Composable
fun NegotiateAITheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = NegotiateAITypography,   // from Type.kt
        shapes = NegotiateAIShapes,           // from Shapes.kt
        content = content
    )
}
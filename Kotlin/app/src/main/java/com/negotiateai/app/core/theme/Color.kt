package com.negotiateai.app.core.theme

import androidx.compose.ui.graphics.Color

// ── DESIGN.md color tokens ────────────────────────────────────────

// Surface hierarchy (Level 0 → Level 2 elevation)
val Surface = Color(0xFFF8F9FA)               // page background
val SurfaceDim = Color(0xFFD9DADB)            // sunken areas
val SurfaceBright = Color(0xFFF8F9FA)         // elevated surfaces
val SurfaceContainerLowest = Color(0xFFFFFFFF) // cards (Level 0 base)
val SurfaceContainerLow = Color(0xFFF3F4F5)   // grouped content
val SurfaceContainer = Color(0xFFEDEEEF)      // default container
val SurfaceContainerHigh = Color(0xFFE7E8E9)  // raised container
val SurfaceContainerHighest = Color(0xFFE1E3E4) // highest surface
val SurfaceVariant = Color(0xFFE1E3E4)
val SurfaceTint = Color(0xFF096969)

// Content / text
val OnSurface = Color(0xFF191C1D)             // primary text — "charcoal"
val OnSurfaceVariant = Color(0xFF3F4948)      // secondary text
val InverseSurface = Color(0xFF2E3132)
val InverseOnSurface = Color(0xFFF0F1F2)

// Borders & outlines (1px institutional strokes)
val Outline = Color(0xFF6F7979)               // input borders (#CED4DA family)
val OutlineVariant = Color(0xFFBEC9C8)        // card borders (#DEE2E6 family)

// Primary — institutional teal (#006666 per DESIGN.md)
val Primary = Color(0xFF004C4C)               // deep teal (pressed/dark)
val OnPrimary = Color(0xFFFFFFFF)
val PrimaryContainer = Color(0xFF006666)      // ★ brand primary
val OnPrimaryContainer = Color(0xFF93E1E0)    // text on teal fill
val InversePrimary = Color(0xFF86D4D3)        // teal on dark surfaces
val PrimaryFixed = Color(0xFFA2F0EF)          // light teal chip fill
val PrimaryFixedDim = Color(0xFF86D4D3)
val OnPrimaryFixed = Color(0xFF002020)
val OnPrimaryFixedVariant = Color(0xFF004F4F)

// Secondary — neutral grays
val Secondary = Color(0xFF5B5F63)
val OnSecondary = Color(0xFFFFFFFF)
val SecondaryContainer = Color(0xFFDDE0E5)
val OnSecondaryContainer = Color(0xFF5F6368)
val SecondaryFixed = Color(0xFFE0E3E8)
val SecondaryFixedDim = Color(0xFFC3C7CC)
val OnSecondaryFixed = Color(0xFF181C20)
val OnSecondaryFixedVariant = Color(0xFF43474C)

// Tertiary — slate accents
val Tertiary = Color(0xFF3C454C)
val OnTertiary = Color(0xFFFFFFFF)
val TertiaryContainer = Color(0xFF535C64)
val OnTertiaryContainer = Color(0xFFCBD4DD)
val TertiaryFixed = Color(0xFFDBE4ED)
val TertiaryFixedDim = Color(0xFFBFC8D0)
val OnTertiaryFixed = Color(0xFF141D23)
val OnTertiaryFixedVariant = Color(0xFF3F484F)

// Error — muted institutional red
val Error = Color(0xFFBA1A1A)
val OnError = Color(0xFFFFFFFF)
val ErrorContainer = Color(0xFFFFDAD6)
val OnErrorContainer = Color(0xFF93000A)

// Background
val Background = Color(0xFFF8F9FA)
val OnBackground = Color(0xFF191C1D)

// ── Semantic status colors ────────────────────────────────────────
// DESIGN.md: "Chips/Badges — light background tints
//             (light green for Active, light orange for Pending)"
// These are referenced by CaseStatusChip and PredictionGauge.

// Success / Active — muted green
val StatusActive = Color(0xFF1B5E20)          // text
val StatusActiveBg = Color(0xFFE6F4EA)        // chip background

// Pending — muted orange
val StatusPending = Color(0xFFE65100)
val StatusPendingBg = Color(0xFFFFF3E0)

// In-progress / Negotiating — primary teal variant
val StatusNegotiating = Color(0xFF004C4C)
val StatusNegotiatingBg = Color(0xFFE0F2F1)

// Settled / Resolved — institutional blue
val StatusSettled = Color(0xFF0D47A1)
val StatusSettledBg = Color(0xFFE3F2FD)

// Escalated / Rejected — subdued red
val StatusEscalated = Color(0xFFB71C1C)
val StatusEscalatedBg = Color(0xFFFFEBEE)

// ── Prediction gauge gradient ─────────────────────────────────────
// Outcome prediction confidence (0 → 100%)
val PredictionLow = Color(0xFFBA1A1A)         // 0–33%   → error red
val PredictionMid = Color(0xFFE65100)         // 34–66%  → caution amber
val PredictionHigh = Color(0xFF1B5E20)        // 67–100% → success green
val PredictionTrack = Color(0xFFEDEEEF)       // gauge background track
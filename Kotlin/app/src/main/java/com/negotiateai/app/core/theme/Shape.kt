package com.negotiateai.app.core.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Shapes
import androidx.compose.ui.unit.dp

// ── DESIGN.md shape scale ─────────────────────────────────────────
// rounded-sm: 4dp · DEFAULT: 8dp · md: 12dp · lg: 16dp · xl: 24dp · full: pill
//
// DESIGN.md rules:
//   · Buttons, inputs, cards → 8dp (DEFAULT)
//   · Status chips / badges  → pill (full)
//   · Sheets / large panels  → 12–16dp
val NegotiateAIShapes = Shapes(

    // small — text fields, small buttons → 8dp per DESIGN.md
    // (DESIGN.md mandates 8dp for ALL primary components;
    //  4dp sm is reserved for tight elements like checkboxes)
    small = RoundedCornerShape(8.dp),

    // medium — cards, standard buttons, dialogs → 8dp DEFAULT
    medium = RoundedCornerShape(8.dp),

    // large — bottom sheets, large surfaces → 16dp
    large = RoundedCornerShape(16.dp),

    // extraLarge — full-screen modals, hero containers → 24dp
    extraLarge = RoundedCornerShape(24.dp),
)

// ── Extra shape constants ─────────────────────────────────────────
// DESIGN.md: status tags/chips use pill radius to differentiate
// from interactive buttons.
val ChipShape = RoundedCornerShape(999.dp)   // "full" pill

// 4dp for micro-elements (checkboxes, tiny indicators)
val TinyShape = RoundedCornerShape(4.dp)

// 12dp for elevated cards in data-dense consoles
val CardDenseShape = RoundedCornerShape(12.dp)
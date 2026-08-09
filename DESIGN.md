---
name: NegotiateAI Gov-Tech
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#3f4948'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#6f7979'
  outline-variant: '#bec9c8'
  surface-tint: '#096969'
  primary: '#004c4c'
  on-primary: '#ffffff'
  primary-container: '#006666'
  on-primary-container: '#93e1e0'
  inverse-primary: '#86d4d3'
  secondary: '#5b5f63'
  on-secondary: '#ffffff'
  secondary-container: '#dde0e5'
  on-secondary-container: '#5f6368'
  tertiary: '#3c454c'
  on-tertiary: '#ffffff'
  tertiary-container: '#535c64'
  on-tertiary-container: '#cbd4dd'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#a2f0ef'
  primary-fixed-dim: '#86d4d3'
  on-primary-fixed: '#002020'
  on-primary-fixed-variant: '#004f4f'
  secondary-fixed: '#e0e3e8'
  secondary-fixed-dim: '#c3c7cc'
  on-secondary-fixed: '#181c20'
  on-secondary-fixed-variant: '#43474c'
  tertiary-fixed: '#dbe4ed'
  tertiary-fixed-dim: '#bfc8d0'
  on-tertiary-fixed: '#141d23'
  on-tertiary-fixed-variant: '#3f484f'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  h1:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  h1-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  h3:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
---

## Brand & Style
The design system is engineered for public infrastructure excellence, prioritizing utility, accessibility, and institutional trust. It targets government officials, enterprise stakeholders, and citizens who require a high-performance interface for complex negotiations.

The aesthetic follows a **Modern Corporate/Institutional** style:
- **Minimalist:** Heavy use of whitespace to reduce cognitive load during data-heavy tasks.
- **Trustworthy:** A stable, high-contrast environment that echoes established digital public goods.
- **Efficient:** No-nonsense layouts and minimal motion to ensure low latency and immediate clarity.
- **Systematic:** Every element is governed by a rigorous grid, ensuring a predictable and professional user experience across all modules.

## Colors
The palette is rooted in institutional stability and legibility.

- **Primary (#006666):** A deep teal used exclusively for primary actions, progress indicators, and active states. It provides a distinct but professional point of focus.
- **Neutral/Surface (#F8F9FA):** Used for background fills and container grouping to separate content sections without using heavy lines.
- **Text/Charcoal (#212529):** High-contrast typography ensures maximum readability across all lighting conditions and display types.
- **Functional Colors:** Success and error states use traditional, muted tones to provide feedback without causing alarm.

## Typography
This design system utilizes **Inter** for all roles due to its exceptional legibility at small sizes and its neutral, systematic character.

- **Headlines:** Use Bold or SemiBold weights with slight negative letter-spacing to appear grounded and authoritative.
- **Body Text:** Standardized on a 16px base for comfort in long-form reading and data entry.
- **Labels:** Used for metadata and table headers, often utilizing a Medium or SemiBold weight to distinguish from interactive body text.
- **Accessibility:** High contrast ratios (minimum 7:1 for body text) are mandatory for all typographic elements.

## Layout & Spacing
The layout is based on a **12-column fluid grid** for desktop and a **4-column grid** for mobile.

- **Rhythm:** An 8px linear scale governs all padding, margins, and component heights.
- **Safe Zones:** Content is typically housed within a 1280px maximum width container on desktop to prevent excessive line lengths.
- **Data Density:** For management consoles, use "Compact" spacing (12px gutters); for landing pages or onboarding, use "Spacious" spacing (24px+ gutters).
- **Alignment:** All elements must align to the baseline grid to maintain a sense of structural integrity.

## Elevation & Depth
Depth is communicated through **Tonal Layers** and extremely subtle shadows, avoiding heavy skeumorphism.

- **Level 0 (Base):** #FFFFFF background.
- **Level 1 (Cards):** #F8F9FA surface with a 1px border (#DEE2E6) or a very soft shadow (0px 2px 4px rgba(0,0,0,0.05)).
- **Level 2 (Dropdowns/Modals):** Floating elements use a more defined shadow (0px 8px 16px rgba(0,0,0,0.08)) to indicate temporary interaction layers.
- **Outlines:** In lieu of shadows, use 1px solid strokes for input fields and button boundaries to maintain a "flat" institutional feel.

## Shapes
The shape language is strictly **Rounded (8px)**, striking a balance between modern accessibility and professional structure.

- **Components:** Buttons, Input fields, and Cards all utilize the 0.5rem (8px) corner radius.
- **Exceptions:** Status tags/chips may use a "Pill" (100px) radius to differentiate them from interactive buttons.
- **Icons:** Use outlined, 24px grid icons with a 2px stroke weight to match the clean, technical aesthetic.

## Components
- **Buttons:** Primary buttons are solid #006666 with white text. Secondary buttons use a #006666 outline with no fill. All buttons have a height of 40px (Medium) or 48px (Large).
- **Cards:** White background, 1px #DEE2E6 border, 8px corner radius. Used to group negotiation details, user profiles, or status summaries.
- **Input Fields:** 1px #CED4DA border that transitions to #006666 on focus. Labels are always visible above the field (not floating) for clarity.
- **Chips/Badges:** Small, 24px height indicators with light background tints (e.g., light green for "Active", light orange for "Pending").
- **Data Tables:** High-density rows with 1px horizontal dividers only. Header cells use `label-sm` with a light gray background (#F8F9FA).
- **Navigation:** A clean top-bar with a white background and a subtle bottom border. Use the primary teal only for the active page indicator.
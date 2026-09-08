export const T = {
  // ── DESIGN.md institutional palette ──────────────────────────────────────
  surface:      '#F8F9FA',   // primary background (DESIGN.md surface)
  surfaceDim:   '#D9DADB',
  surfaceBright:'#F8F9FA',
  surfaceContainerLowest: '#FFFFFF',
  surfaceContainerLow: '#F3F4F5',
  surfaceContainer: '#EDEEEF',
  surfaceContainerHigh: '#E7E8E9',
  surfaceContainerHighest:'#E1E3E4',

  onSurface:    '#191C1D',   // primary text (high contrast)
  onSurfaceVariant: '#3F4948', // secondary text
  inverseSurface: '#2E3132',
  inverseOnSurface: '#F0F1F2',

  outline:      '#6F7979',
  outlineVariant:'#BEC9C8',

  surfaceTint:  '#096969',
  primary:      '#006666',   // deep teal (DESIGN.md primary)
  onPrimary:    '#FFFFFF',
  primaryContainer: '#006666',
  onPrimaryContainer: '#93E1E0',
  inversePrimary:'#86D4D3',

  secondary:    '#5B5F63',
  onSecondary:  '#FFFFFF',
  secondaryContainer: '#DDE0E5',
  onSecondaryContainer: '#5F6368',

  tertiary:     '#3C454C',
  onTertiary:   '#FFFFFF',
  tertiaryContainer: '#535C64',
  onTertiaryContainer: '#CBD4DD',

  error:        '#BA1A1A',
  onError:      '#FFFFFF',
  errorContainer:'#FFdad6',
  onErrorContainer:'#93000A',

  // Functional aliases (keep short names for existing component usage)
  bg:           '#F8F9FA',
  card:         '#FFFFFF',
  border:       '#DEE2E6',
  accent:       '#006666',
  accent2:      '#006666',
  green:        '#10B981',
  red:          '#BA1A1A',
  yellow:       '#F59E0B',
  purple:       '#3C454C',
  muted:        '#6F7979',
  text:         '#191C1D',
  textSecondary:'#3F4948',
};
 
export const css = {
  // ── DESIGN.md system: 8px spacing, 8px radius, Inter font, light institutional ──
  app:       { minHeight: '100vh', background: T.surface, color: T.onSurface, fontFamily: "'Inter', sans-serif" },

  // Top navigation bar (DESIGN.md: clean top-bar, white bg, subtle bottom border)
  header:    { background: '#FFFFFF', borderBottom: '1px solid ' + T.border,
               padding: '0 24px', height: 60,
               display: 'flex', alignItems: 'center', justifyContent: 'space-between',
               position: 'sticky', top: 0, zIndex: 100 },

  logo:      { fontSize: 20, fontWeight: 700, fontFamily: "'Inter', sans-serif",
               color: T.primary, letterSpacing: '-0.02em' },

  badge:     { padding: '3px 10px', borderRadius: 100, fontSize: 11, fontWeight: 600 },

  // Primary button (DESIGN.md: solid primary #006666, white text, 40px height, 8px radius)
  btn:       { padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
               fontWeight: 600, fontSize: 14, transition: 'all 0.2s',
               background: T.primary, color: T.onPrimary,
               height: 40, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
               gap: 6 },

  // Card (DESIGN.md: white bg, 1px #DEE2E6 border, 8px radius)
  card:      { background: T.surfaceContainerLowest, border: '1px solid ' + T.border,
               borderRadius: 8, padding: 20, marginBottom: 16,
               transition: 'all 0.3s cubic-bezier(0.16,1,0.3,1)' },

  title:     { fontSize: 16, fontWeight: 700, marginBottom: 16, color: T.onSurface,
               display: 'flex', alignItems: 'center', gap: 8 },

  // Input (DESIGN.md: 1px #CED4DA border → primary on focus, visible label above)
  input:     { width: '100%', padding: '10px 14px', background: '#FFFFFF',
               border: '1px solid #CED4DA', borderRadius: 8,
               color: T.onSurface, fontSize: 14, outline: 'none', marginBottom: 12,
               fontFamily: "'Inter', sans-serif", transition: 'border-color 0.2s, box-shadow 0.2s' },

  select:    { width: '100%', padding: '10px 14px', background: '#FFFFFF',
               border: '1px solid #CED4DA', borderRadius: 8,
               color: T.onSurface, fontSize: 14, outline: 'none', marginBottom: 12,
               fontFamily: "'Inter', sans-serif", transition: 'border-color 0.2s' },

  label:     { fontSize: 13, color: T.textSecondary, marginBottom: 4, display: 'block',
               fontWeight: 600, fontFamily: "'Inter', sans-serif" },

  row:       { display: 'flex', gap: 12, flexWrap: 'wrap' },
  col:       { flex: 1, minWidth: 200 },

  grid2:     { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  grid3:     { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 },

  metric:    { textAlign: 'center', padding: '16px 8px', background: T.surface,
               borderRadius: 8, border: '1px solid ' + T.border },
  metricVal: { fontSize: 28, fontWeight: 800, display: 'block', color: T.onSurface },
  metricLbl: { fontSize: 12, color: T.textSecondary, marginTop: 2, fontWeight: 500 },

  chip:      { display: 'inline-block', padding: '4px 10px', borderRadius: 100, fontSize: 11,
               background: T.surface, color: T.textSecondary, margin: '2px',
               border: '1px solid ' + T.border, fontWeight: 500 },

  progress:  { height: 6, background: T.surfaceContainerHigh, borderRadius: 3,
               overflow: 'hidden', margin: '8px 0' },
  bar:       { height: '100%', borderRadius: 3, transition: 'width 0.5s ease' },

  scroll:    { overflowY: 'auto', maxHeight: 400, scrollbarWidth: 'thin' },

  msg:       { padding: '12px 16px', borderRadius: 8, marginBottom: 10,
               maxWidth: '80%', fontSize: 14, fontFamily: "'Inter', sans-serif" },

  divider:   { height: 1, background: T.surfaceContainerHigh, margin: '16px 0' },

  tab:       { padding: '10px 18px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
               fontWeight: 600, border: 'none', transition: 'all 0.2s',
               fontFamily: "'Inter', sans-serif", height: 40, display: 'inline-flex',
               alignItems: 'center' },

  // Ghost button (outline only)
  btnGhost:  { padding: '10px 20px', borderRadius: 8, cursor: 'pointer',
               fontWeight: 600, fontSize: 14, transition: 'all 0.2s',
               background: 'transparent', color: T.primary, border: '1px solid ' + T.primary,
               height: 40, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
               gap: 6 },

  // Small text helper
  small:     { fontSize: 12, color: T.textSecondary },

  // Section header
  sectionHeader: { fontSize: 24, fontWeight: 700, marginBottom: 24, color: T.onSurface },

  // Data table
  table:     { width: '100%', borderCollapse: 'collapse', fontSize: 14 },
  tableHead: { padding: '10px 14px', textAlign: 'left', fontSize: 12,
               color: T.textSecondary, fontWeight: 600, borderBottom: '1px solid ' + T.border },
  tableCell: { padding: '12px 14px', borderBottom: '1px solid ' + T.surfaceContainerHigh },
  tableRow:  { transition: 'background 0.15s' },
};
 
export const fmt = n => n ? '\u20B9' + Number(n).toLocaleString('en-IN') : '\u2014';
export const pct = n => n ? (n * 100).toFixed(1) + '%' : '\u2014';
export const confColor = { high: T.green, medium: T.yellow, low: T.red };
export const sentiColor = { cooperative: T.green, conciliatory: T.accent2, neutral: T.muted, frustrated: T.yellow, hostile: T.red };
export const T = {
  bg: '#0a0f1e', surface: '#0f1626', card: '#131d30', border: '#1e2d45',
  accent: '#3b82f6', accent2: '#06b6d4', green: '#10b981', red: '#ef4444',
  yellow: '#f59e0b', purple: '#8b5cf6', muted: '#64748b', text: '#e2eaf5',
};

export const css = {
  app:       { minHeight: '100vh', background: T.bg, color: T.text, fontFamily: "'Segoe UI', sans-serif" },
  header:    { background: T.surface, borderBottom: '1px solid ' + T.border, padding: '0 24px', height: 60,
               display: 'flex', alignItems: 'center', justifyContent: 'space-between',
               position: 'sticky', top: 0, zIndex: 100 },
  logo:      { fontSize: 20, fontWeight: 700, background: 'linear-gradient(135deg,' + T.accent + ',' + T.accent2 + ')',
               WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' },
  badge:     { padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600 },
  btn:       { padding: '8px 18px', borderRadius: 8, border: 'none', cursor: 'pointer',
               fontWeight: 600, fontSize: 13, transition: 'all 0.2s' },
  card:      { background: T.card, border: '1px solid ' + T.border, borderRadius: 12,
               padding: 20, marginBottom: 16 },
  title:     { fontSize: 16, fontWeight: 700, marginBottom: 16, color: T.text,
               display: 'flex', alignItems: 'center', gap: 8 },
  input:     { width: '100%', padding: '10px 14px', background: T.bg, border: '1px solid ' + T.border,
               borderRadius: 8, color: T.text, fontSize: 14, outline: 'none', marginBottom: 12 },
  select:    { width: '100%', padding: '10px 14px', background: T.bg, border: '1px solid ' + T.border,
               borderRadius: 8, color: T.text, fontSize: 14, outline: 'none', marginBottom: 12 },
  label:     { fontSize: 12, color: T.muted, marginBottom: 4, display: 'block', fontWeight: 600 },
  row:       { display: 'flex', gap: 12, flexWrap: 'wrap' },
  col:       { flex: 1, minWidth: 200 },
  grid2:     { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  grid3:     { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 },
  metric:    { textAlign: 'center', padding: '12px 8px', background: T.bg, borderRadius: 10,
               border: '1px solid ' + T.border },
  metricVal: { fontSize: 24, fontWeight: 800, display: 'block' },
  metricLbl: { fontSize: 11, color: T.muted, marginTop: 2 },
  chip:      { display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11,
               background: T.border, color: T.text, margin: '2px' },
  progress:  { height: 6, background: T.border, borderRadius: 3, overflow: 'hidden', margin: '8px 0' },
  bar:       { height: '100%', borderRadius: 3, transition: 'width 0.5s ease' },
  scroll:    { overflowY: 'auto', maxHeight: 400 },
  msg:       { padding: '10px 14px', borderRadius: 10, marginBottom: 10, maxWidth: '80%', fontSize: 13 },
  divider:   { height: 1, background: T.border, margin: '16px 0' },
  tab:       { padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
               fontWeight: 600, border: 'none', transition: 'all 0.2s' },
};

export const fmt = n => n ? '₹' + Number(n).toLocaleString('en-IN') : '—';
export const pct = n => n ? (n * 100).toFixed(1) + '%' : '—';
export const confColor = { high: T.green, medium: T.yellow, low: T.red };
export const sentiColor = { cooperative: T.green, conciliatory: T.accent2, neutral: T.muted, frustrated: T.yellow, hostile: T.red };
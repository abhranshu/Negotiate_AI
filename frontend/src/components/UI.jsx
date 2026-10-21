import React from 'react';

/*
 * Shared UI primitives.
 *
 * Everything interactive/stateful lives here so hover, active, focus-visible,
 * disabled and loading states are defined once (in global.css) instead of being
 * re-approximated inline on every screen — inline styles cannot express a
 * pseudo-class, which is why most buttons previously had no feedback at all.
 */

/* ── Spinner ──────────────────────────────────────────────────────────────────
   Standalone inline spinner. Buttons use it via the `Button` component's
   `loading` prop so the two never drift apart. */
export const Spinner = React.memo(function Spinner({ size = 14 }) {
  return (
    <span aria-hidden="true" style={{
      display: 'inline-block',
      width: size, height: size,
      border: '2px solid var(--border)',
      borderTop: '2px solid currentColor',
      borderRadius: '50%',
      marginRight: 6,
      flexShrink: 0,
      verticalAlign: '-2px',
      animation: 'spin 0.7s linear infinite',
    }} />
  );
});

/* ── Button ───────────────────────────────────────────────────────────────────
   variant: primary | accent | success | secondary | ghost | plain
   size:    sm | md | lg  (+ icon for square, block for full width)
   `loading` keeps the label visible (so the button never changes width mid
   request) and reports the busy state to assistive tech. */
export const Button = React.memo(function Button({
  variant = 'primary',
  size = 'md',
  block = false,
  icon = false,
  loading = false,
  disabled = false,
  className = '',
  children,
  ...rest
}) {
  // Map legacy/alias variant names to real CSS classes so every caller renders
  // a styled button (previously `accent`/`success`/`secondary`/`plain` had no
  // CSS and came out as unstyled grey HTML buttons).
  const variantClass = {
    primary:   'btn-primary',
    accent:    'btn-accent',
    success:   'btn-success',
    secondary: 'btn-secondary',
    ghost:     'btn-ghost',
    plain:     'btn-plain',
  }[variant] || 'btn-primary';

  const classes = [
    'btn',
    variantClass,
    size !== 'md' ? `btn-${size}` : '',
    block ? 'btn-block' : '',
    icon ? 'btn-icon' : '',
    loading ? 'is-busy' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <button
      type="button"
      className={classes}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading && <Spinner />}
      {children}
    </button>
  );
});

/* ── Badge ────────────────────────────────────────────────────────────────────
   The previous implementation built colour strings with string.replace on
   var() tokens, which produced invalid CSS (e.g. "rgba(0,0.1),") — every badge
   that passed var(--primary) silently lost its background and border.
   color-mix handles hex and var() uniformly. */
export const Badge = React.memo(function Badge({ text, color }) {
  const c = color || 'var(--outline)';
  const isVar = typeof c === 'string' && c.trim().startsWith('var(');
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      padding: '3px 10px', borderRadius: 'var(--r-pill)',
      fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap',
      color: c,
      // color-mix with a var() token fails on older browsers (and some
      // mobile WebViews) leaving the badge with no background/border.
      // Fall back to translucent hex overlays for var() colours.
      background: isVar ? 'rgba(0,102,102,0.08)' : `${c}1F`,
      border: isVar ? '1px solid rgba(0,102,102,0.30)' : `1px solid ${c}55`,
    }}>{text}</span>
  );
});

/* ── Alert ───────────────────────────────────────────────────────────────────── */
export const Alert = React.memo(function Alert({ msg, type = 'info' }) {
  if (!msg) return null;

  const tones = {
    error:   { fg: 'var(--error)',   bg: 'rgba(186,26,26,0.06)',  bd: 'rgba(186,26,26,0.22)',  icon: '⚠️' },
    success: { fg: 'var(--success)', bg: 'rgba(14,159,110,0.07)', bd: 'rgba(14,159,110,0.24)', icon: '✅' },
    info:    { fg: 'var(--primary)', bg: 'rgba(0,102,102,0.06)',  bd: 'rgba(0,102,102,0.2)',   icon: 'ℹ️' },
  };
  const t = tones[type] || tones.info;

  // Never render non-string values as React children — normalize defensively
  // (prevents "Objects are not valid as a React child").
  const text = typeof msg === 'string'
    ? msg
    : Array.isArray(msg)
      ? msg.filter(m => typeof m === 'string' || typeof m === 'number').join(', ')
      : JSON.stringify(msg);

  return (
    <div className="animate-fade-in-up" role={type === 'error' ? 'alert' : 'status'} style={{
      display: 'flex', alignItems: 'center', gap: 8,
      padding: '10px 14px', borderRadius: 'var(--r-md)', fontSize: 13,
      marginBottom: 12, color: t.fg, background: t.bg, border: `1px solid ${t.bd}`,
    }}>
      <span aria-hidden="true">{t.icon}</span>
      <span>{text}</span>
    </div>
  );
});

/* ── EmptyState ────────────────────────────────────────────────────────────────
   `action` is an optional node (usually a Button) rendered under the copy, so an
   empty screen can offer the one thing the user is meant to do next. */
export const EmptyState = React.memo(function EmptyState({ icon, text, subtext, action }) {
  return (
    <div className="animate-scale-in" style={{
      textAlign: 'center', padding: '44px 20px', color: 'var(--text-secondary)',
    }}>
      <div aria-hidden="true" style={{
        width: 64, height: 64, margin: '0 auto 16px', borderRadius: 'var(--r-xl)', fontSize: 28,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--surface-container-low)', border: '1px solid var(--border)',
      }}>{icon}</div>
      <div style={{ fontWeight: 700, marginBottom: 4, color: 'var(--on-surface)' }}>{text}</div>
      <div style={{ fontSize: 13, maxWidth: 400, margin: '0 auto', lineHeight: 1.6 }}>
        {subtext}
      </div>
      {action && <div style={{ marginTop: 18 }}>{action}</div>}
    </div>
  );
});

/* ── Tab ───────────────────────────────────────────────────────────────────────
   A real ARIA tab: it reports `aria-selected` (not `aria-current`) and keeps the
   roving tabindex convention — only the selected tab is reachable with Tab, the
   arrows move between tabs (handled by the owning tablist). */
export const Tab = React.memo(function Tab({ active, value, onSelect, label, id, panelId }) {
  // Bind the value here so callers can pass one stable `onSelect` instead of a
  // fresh arrow per tab (which would make this memo useless).
  const handleClick = React.useCallback(() => onSelect(value), [onSelect, value]);

  return (
    <button
      type="button"
      id={id}
      role="tab"
      aria-selected={active ? true : false}
      aria-controls={panelId}
      tabIndex={active ? 0 : -1}
      className={'tab' + (active ? ' is-active' : '')}
      onClick={active ? undefined : handleClick}
    >
      {label}
    </button>
  );
});

/* ── Skeletons ─────────────────────────────────────────────────────────────────
   Used only where a real network round-trip leaves a visible gap — they keep the
   layout from collapsing and shifting when the data lands. */

export const Skeleton = React.memo(function Skeleton({
  width = '100%', height = 12, radius = 'var(--r-sm)', className = '', style,
}) {
  return (
    <div
      className={`skeleton ${className}`}
      aria-hidden="true"
      style={{ width, height, borderRadius: radius, ...style }}
    />
  );
});

/* Placeholder rows sized to match the cases table (6 columns). */
export const SkeletonTableRows = React.memo(function SkeletonTableRows({ rows = 4, cols = 6 }) {
  const widths = ['70%', '80%', '55%', '60%', '65%', '50%'];
  return (
    <>
      {Array.from({ length: rows }).map((_, r) => (
        <tr key={r}>
          {Array.from({ length: cols }).map((__, c) => (
            <td key={c} style={{ padding: '12px 14px', borderBottom: '1px solid var(--surface-container-high)' }}>
              <Skeleton width={widths[c % widths.length]} height={13} />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
});

/* Generic card placeholder for panel-level loading (mimics the panel layout). */
export const SkeletonCard = React.memo(function SkeletonCard({ lines = 3, height = 96 }) {
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <Skeleton width="35%" height={14} radius="var(--r-sm)" style={{ marginBottom: 14 }} />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} width={i === lines - 1 ? '60%' : '100%'} height={11}
          style={{ marginBottom: i === lines - 1 ? 0 : 10 }} />
      ))}
      {height > 0 && <Skeleton height={height} radius="var(--r-md)" style={{ marginTop: 16 }} />}
    </div>
  );
});

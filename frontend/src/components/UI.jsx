import React from 'react';
import { css } from '../theme';

export const Spinner = React.memo(function Spinner() {
  return (
    <span style={{
      display: 'inline-block', width: 14, height: 14,
      border: '2px solid var(--border)',
      borderTop: '2px solid var(--primary)',
      borderRadius: '50%', marginRight: 6,
      animation: 'spin 0.7s linear infinite',
    }} />
  );
});

export const Badge = React.memo(function Badge({ text, color }) {
  return (
    <span style={{
      ...css.badge,
      background: typeof color === 'string' && color.startsWith('var(')
        ? color.replace('var(', 'rgba(0,').replace(')', ',0.1),')
        : color + '22',
      color: typeof color === 'string' && color.startsWith('var(')
        ? color
        : color,
      border: typeof color === 'string' && color.startsWith('var(')
        ? color.replace('var(', 'rgba(0,').replace(')', ',0.3),')
        : color + '44',
    }}>{text}</span>
  );
});

export const Stat = React.memo(function Stat({ label, value, color }) {
  return (
    <div style={css.metric}>
      <span style={{ ...css.metricVal, color: color || 'var(--primary)' }}>{value}</span>
      <div style={css.metricLbl}>{label}</div>
    </div>
  );
});

export const Section = React.memo(function Section({ icon, title, children }) {
  return (
    <div style={css.card}>
      <div style={css.title}><span>{icon}</span> {title}</div>
      {children}
    </div>
  );
});

export const ProgressBar = React.memo(function ProgressBar({ pct, color }) {
  return (
    <div style={css.progress}>
      <div style={{ ...css.bar, width: (pct || 0) + '%', background: color || 'var(--primary)' }} />
    </div>
  );
});

export const Alert = React.memo(function Alert({ msg, type }) {
  if (!msg) return null;
  const icons = { error: '⚠️', success: '✅', info: 'ℹ️' };
  const colors = {
    error: '#BA1A1A',
    success: '#10B981',
    info: 'var(--primary)',
  };
  const c = colors[type] || 'var(--primary)';
  // Never render non-string values as React children — normalize defensively
  // (prevents "Objects are not valid as a React child").
  const text = typeof msg === 'string'
    ? msg
    : Array.isArray(msg)
      ? msg.filter(m => typeof m === 'string' || typeof m === 'number').join(', ')
      : JSON.stringify(msg);
  return (
    <div className="animate-fade-in-up" style={{
      display: 'flex', alignItems: 'center', gap: 8,
      padding: '10px 14px', borderRadius: 8, fontSize: 13, marginBottom: 12,
      background: typeof c === 'string' && c.startsWith('#')
        ? c + '15'
        : 'rgba(0,102,102,0.06)',
      border: typeof c === 'string' && c.startsWith('#')
        ? c + '33'
        : 'rgba(0,102,102,0.2)',
      color: c,
    }}><span>{icons[type] || 'ℹ️'}</span>{text}</div>
  );
});

export const EmptyState = React.memo(function EmptyState({ icon, text, subtext }) {
  return (
    <div className="animate-scale-in" style={{ textAlign: 'center', padding: '44px 20px', color: 'var(--text-secondary)' }}>
      <div style={{
        width: 64, height: 64, margin: '0 auto 16px', borderRadius: 16, fontSize: 28,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--surface)',
        border: '1px solid var(--border)',
      }}>{icon}</div>
      <div style={{ fontWeight: 700, marginBottom: 4, color: 'var(--on-surface)' }}>{text}</div>
      <div style={{ fontSize: 13, maxWidth: 400, margin: '0 auto', lineHeight: 1.6, color: 'var(--text-secondary)' }}>{subtext}</div>
    </div>
  );
});

export const Tab = React.memo(function Tab({ active, onClick, label }) {
  return (
    <button style={{
      ...css.tab,
      height: 40,
      background: active ? 'var(--primary)' : 'transparent',
      color: active ? 'var(--on-primary)' : 'var(--text-secondary)',
      boxShadow: active ? '0 2px 8px rgba(0,102,102,0.25)' : 'none',
      border: active ? 'none' : '1px solid var(--border)',
    }} onClick={onClick}>
      {label}
    </button>
  );
});

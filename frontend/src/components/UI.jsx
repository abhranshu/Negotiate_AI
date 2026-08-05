import React from 'react';
import { T, css } from '../theme';

export function Spinner() {
  return (
    <span style={{
      display: 'inline-block', width: 14, height: 14,
      border: '2px solid ' + T.border,
      borderTop: '2px solid ' + T.accent,
      borderRadius: '50%', marginRight: 6,
      animation: 'spin 0.7s linear infinite',
    }} />
  );
}

export function Badge({ text, color }) {
  return (
    <span style={{
      ...css.badge,
      background: color + '22',
      color: color,
      border: '1px solid ' + color + '44',
    }}>{text}</span>
  );
}

export function Stat({ label, value, color }) {
  return (
    <div style={css.metric}>
      <span style={{ ...css.metricVal, color: color || T.accent }}>{value}</span>
      <div style={css.metricLbl}>{label}</div>
    </div>
  );
}

export function Section({ icon, title, children }) {
  return (
    <div style={css.card}>
      <div style={css.title}><span>{icon}</span> {title}</div>
      {children}
    </div>
  );
}

export function ProgressBar({ pct, color }) {
  return (
    <div style={css.progress}>
      <div style={{ ...css.bar, width: (pct || 0) + '%', background: color || T.accent }} />
    </div>
  );
}

export function Alert({ msg, type }) {
  if (!msg) return null;
  const colors = { error: T.red, success: T.green, info: T.accent };
  const c = colors[type] || T.accent;
  return (
    <div style={{
      padding: '10px 14px', borderRadius: 8, fontSize: 13, marginBottom: 12,
      background: c + '22', border: '1px solid ' + c + '44', color: c,
    }}>{msg}</div>
  );
}

export function EmptyState({ icon, text, subtext }) {
  return (
    <div style={{ textAlign: 'center', padding: '40px 20px', color: T.muted }}>
      <div style={{ fontSize: 48, marginBottom: 12 }}>{icon}</div>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{text}</div>
      <div style={{ fontSize: 13 }}>{subtext}</div>
    </div>
  );
}

export function Tab({ active, onClick, label }) {
  return (
    <button style={{
      ...css.tab,
      background: active ? T.accent : 'transparent',
      color: active ? '#fff' : T.muted,
    }} onClick={onClick}>{label}</button>
  );
}
import React, { useState, useEffect } from 'react';
import API from '../api';
import { T, css, fmt, pct, confColor } from '../theme';
import { Badge, Spinner, EmptyState, Alert } from './UI';

const DISPUTE_ICONS = {
  delayed_payment: '⏰', non_payment: '🚫', short_payment: '📉',
  quality_dispute: '🔍', quantity_dispute: '📦', contract_breach: '📋',
};
const STATUS_COLORS = {
  draft: '#64748b', submitted: '#3b82f6', in_progress: '#f59e0b',
  agreement: '#10b981', closed: '#06b6d4', escalated: '#ef4444',
};

export default function CaseDashboard({ user, onSelectCase, onCreateCase, refreshKey }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  useEffect(() => {
    setLoading(true);
    API.get('/api/cases')
      .then(r => setCases(r.data))
      .catch(() => setErr('Failed to load cases'))
      .finally(() => setLoading(false));
  }, [refreshKey]);   // re-fetch whenever refreshKey changes

  const stats = [
    { label: 'Total Cases', value: cases.length, color: T.accent },
    { label: 'Active',      value: cases.filter(c => c.status === 'in_progress').length, color: T.yellow },
    { label: 'Agreed',      value: cases.filter(c => c.status === 'agreement').length,   color: T.green },
    { label: 'Total Claim', value: fmt(cases.reduce((s, c) => s + (c.claim_amount || 0), 0)), color: T.purple },
  ];

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 16px' }}>
      {/* Header Row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Welcome back, {user?.full_name?.split(' ')[0]} 👋</h1>
          <p style={{ color: T.muted, fontSize: 13, marginTop: 4 }}>Manage and resolve your MSME payment disputes</p>
        </div>
        <button style={{ ...css.btn, background: `linear-gradient(135deg,${T.accent},${T.accent2})`,
          color: '#fff', padding: '10px 20px', fontSize: 14 }} onClick={onCreateCase}>
          ＋ New Case
        </button>
      </div>

      {/* Stats Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 24 }}>
        {stats.map(s => (
          <div key={s.label} style={{ ...css.card, margin: 0, textAlign: 'center', padding: '16px 12px' }}>
            <div style={{ fontSize: 28, fontWeight: 800, color: s.color }}>{s.value}</div>
            <div style={{ color: T.muted, fontSize: 12, marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* ML Pipeline Status Bar */}
      <div style={{ ...css.card, marginBottom: 24 }}>
        <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: T.muted }}>5-STEP ML PIPELINE</div>
        <div style={{ display: 'flex', alignItems: 'center', overflowX: 'auto', gap: 0 }}>
          {[
            { icon: '🎙️', label: 'Voice Input', desc: 'Whisper ASR + NER' },
            { icon: '📄', label: 'Document AI', desc: 'OCR + DistilBERT' },
            { icon: '📊', label: 'Prediction', desc: 'XGBoost + SHAP' },
            { icon: '🤝', label: 'Negotiation', desc: 'Game Theory + LLM' },
            { icon: '📜', label: 'Settlement', desc: 'MSMED Compliant PDF' },
          ].map((step, i) => (
            <React.Fragment key={step.label}>
              <div style={{ flex: 1, textAlign: 'center', padding: '10px 6px',
                background: T.bg, borderRadius: 10, border: `1px solid ${T.border}`,
                minWidth: 100 }}>
                <div style={{ fontSize: 22 }}>{step.icon}</div>
                <div style={{ fontSize: 11, fontWeight: 600, marginTop: 4 }}>{step.label}</div>
                <div style={{ fontSize: 10, color: T.muted }}>{step.desc}</div>
              </div>
              {i < 4 && <div style={{ color: T.border, fontSize: 18, padding: '0 4px' }}>›</div>}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Cases Table */}
      <div style={css.card}>
        <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>📁 Your Cases</div>
        {err && <Alert msg={err} type="error" />}
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}><Spinner /> Loading cases...</div>
        ) : cases.length === 0 ? (
          <EmptyState icon="📂" text="No cases yet"
            subtext="Create your first dispute case to get started with the AI pipeline" />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${T.border}` }}>
                  {['Case #', 'Type', 'Claim', 'Status', 'Date', ''].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: 12,
                      color: T.muted, fontWeight: 600 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cases.map(c => (
                  <tr key={c.id} style={{ borderBottom: `1px solid ${T.border}`, cursor: 'pointer',
                    transition: 'background 0.15s' }}
                    onMouseEnter={e => e.currentTarget.style.background = T.surface}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    onClick={() => onSelectCase(c)}>
                    <td style={{ padding: '12px', fontWeight: 600, fontSize: 13 }}>{c.case_number || c.id?.slice(0, 8)}</td>
                    <td style={{ padding: '12px', fontSize: 13 }}>
                      {DISPUTE_ICONS[c.dispute_type] || '📋'} {c.dispute_type?.replace(/_/g, ' ') || '—'}
                    </td>
                    <td style={{ padding: '12px', fontWeight: 600, color: T.accent2 }}>{fmt(c.claim_amount)}</td>
                    <td style={{ padding: '12px' }}>
                      <Badge text={c.status?.replace(/_/g, ' ')} color={STATUS_COLORS[c.status] || T.muted} />
                    </td>
                    <td style={{ padding: '12px', fontSize: 12, color: T.muted }}>
                      {new Date(c.created_at).toLocaleDateString('en-IN')}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <button style={{ ...css.btn, background: T.accent, color: '#fff', padding: '5px 14px', fontSize: 12 }}>
                        Open →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
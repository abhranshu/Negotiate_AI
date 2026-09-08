import React, { useState, useEffect } from 'react';
import API from '../api';
import { css, fmt } from '../theme';
import { Badge, Spinner, EmptyState, Alert } from './UI';

const DISPUTE_ICONS = {
  delayed_payment: '⏰', non_payment: '🚫', short_payment: '📉',
  quality_dispute: '🔍', quantity_dispute: '📦', contract_breach: '📋',
};
const STATUS_COLORS = {
  draft:       '#6F7979',
  submitted:   '#3B82F6',
  in_progress: '#F59E0B',
  agreement:   '#10B981',
  closed:      '#006666',
  escalated:   '#BA1A1A',
};
const STATUS_LABELS = {
  draft: 'Draft', submitted: 'Submitted', in_progress: 'In Progress',
  agreement: 'Agreement', closed: 'Closed', escalated: 'Escalated',
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
  }, [refreshKey]);

  const stats = [
    { label: 'Total Cases',   value: cases.length,          color: 'var(--primary)' },
    { label: 'Active',        value: cases.filter(c => c.status === 'in_progress').length, color: '#F59E0B' },
    { label: 'Agreed',        value: cases.filter(c => c.status === 'agreement').length,     color: '#10B981' },
    { label: 'Total Claim',   value: fmt(cases.reduce((s, c) => s + (c.claim_amount || 0), 0)), color: 'var(--primary)' },
  ];

  return (
    <div style={{ animation: 'fadeInUp 0.5s ease-out both' }}>
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
        marginBottom: 28, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{
            fontSize: 24, fontWeight: 700, margin: 0, color: 'var(--on-surface)',
            fontFamily: "'Inter', sans-serif", letterSpacing: '-0.02em'
          }}>
            Welcome back, {user?.full_name?.split(' ')[0]}
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 4, marginBottom: 0 }}>
            Manage and resolve your MSME payment disputes
          </p>
        </div>
        <button
          style={{
            ...css.btn,
            background: 'var(--primary)',
            color: 'var(--on-primary)',
            padding: '10px 20px',
            fontSize: 14,
            boxShadow: '0 2px 8px rgba(0,102,102,0.25)',
            display: 'inline-flex', alignItems: 'center', gap: 6,
          }}
          onClick={onCreateCase}
        >
          <span>+</span> New Case
        </button>
      </div>

      {/* Stats cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 16,
        marginBottom: 24
      }}>
        {stats.map((s, i) => (
          <div
            key={s.label}
            className="app-card-hover"
            style={{
              background: 'var(--surface-container-lowest)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '20px 16px',
              textAlign: 'center',
            }}
          >
            <div style={{
              fontSize: 32, fontWeight: 800,
              color: s.color,
              marginBottom: 6,
              fontFamily: "'Inter', sans-serif"
            }}>
              {s.value}
            </div>
            <div style={{
              fontSize: 12, color: 'var(--text-secondary)',
              fontWeight: 500, margin: 0
            }}>
              {s.label}
            </div>
          </div>
        ))}
      </div>

      {/* ML Pipeline status bar */}
      <div className="app-card-hover"
        style={{
          background: 'var(--surface-container-lowest)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          padding: '16px 20px',
          marginBottom: 24,
        }}
      >
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)',
          marginBottom: 14, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
          5-Step ML Pipeline
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 0, overflowX: 'auto' }}>
          {[
            { icon: '🎙️', label: 'Voice Input',   desc: 'Whisper ASR + NER' },
            { icon: '📄',  label: 'Document AI',   desc: 'OCR + DistilBERT' },
            { icon: '📊',  label: 'Prediction',    desc: 'XGBoost + SHAP' },
            { icon: '🤝',  label: 'Negotiation',   desc: 'Game Theory + LLM' },
            { icon: '📜',  label: 'Settlement',    desc: 'MSMED Compliant PDF' },
          ].map((step, i) => (
            <React.Fragment key={step.label}>
              <div style={{
                flex: 1,
                textAlign: 'center',
                padding: '12px 8px',
                background: 'var(--surface)',
                borderRadius: 8,
                border: '1px solid var(--border)',
                minWidth: 100,
              }}>
                <div style={{ fontSize: 22, marginBottom: 4 }}>{step.icon}</div>
                <div style={{
                  fontSize: 11, fontWeight: 600, color: 'var(--on-surface)',
                  marginBottom: 2
                }}>{step.label}</div>
                <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>
                  {step.desc}
                </div>
              </div>
              {i < 4 && (
                <div style={{
                  color: 'var(--border)',
                  fontSize: 16,
                  padding: '0 4px',
                  display: 'flex',
                  alignItems: 'center',
                  alignSelf: 'center',
                }}>
                  →
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Cases table */}
      <div className="app-card-hover"
        style={{
          background: 'var(--surface-container-lowest)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          padding: '20px',
        }}
      >
        <div style={{
          fontSize: 15, fontWeight: 700, marginBottom: 16,
          color: 'var(--on-surface)'
        }}>
          Your Cases
        </div>

        {err && (
          <Alert msg={err} type="error" />
        )}

        {loading ? (
          <div style={{ textAlign: 'center', padding: 48 }}>
            <div style={{
              width: 24, height: 24, margin: '0 auto 12px',
              border: '3px solid var(--border)',
              borderTopColor: 'var(--primary)',
              borderRadius: '50%',
              animation: 'spin 0.7s linear infinite',
            }} />
            <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
              Loading cases...
            </div>
          </div>
        ) : cases.length === 0 ? (
          <EmptyState
            icon="📁"
            text="No cases yet"
            subtext="Create your first dispute case to get started with the AI pipeline"
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="institutional">
              <thead>
                <tr>
                  <th style={css.tableHead}>Case</th>
                  <th style={css.tableHead}>Type</th>
                  <th style={css.tableHead}>Claim Amount</th>
                  <th style={css.tableHead}>Status</th>
                  <th style={css.tableHead}>Created</th>
                  <th style={css.tableHead} style={{ width: 120, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {cases.map(c => (
                  <tr
                    key={c.id}
                    className="app-card-hover"
                    style={{ cursor: 'pointer' }}
                    onClick={() => onSelectCase(c)}
                  >
                    <td style={css.tableCell}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>
                        {c.case_number || c.id?.slice(0, 8)}
                      </div>
                    </td>
                    <td style={css.tableCell}>
                      <span style={{ marginRight: 6 }}>
                        {DISPUTE_ICONS[c.dispute_type] || '📋'}
                      </span>
                      <span style={{
                        fontSize: 13,
                        color: 'var(--text-secondary)',
                        textTransform: 'capitalize',
                      }}>
                        {c.dispute_type?.replace(/_/g, ' ') || '—'}
                      </span>
                    </td>
                    <td style={css.tableCell}>
                      <span style={{
                        fontWeight: 700,
                        color: 'var(--primary)',
                        fontSize: 13,
                      }}>
                        {fmt(c.claim_amount)}
                      </span>
                    </td>
                    <td style={css.tableCell}>
                      <span style={{
                        display: 'inline-block',
                        padding: '4px 10px',
                        borderRadius: 100,
                        fontSize: 11,
                        fontWeight: 600,
                        background: (STATUS_COLORS[c.status] || '#6F7979') + '18',
                        color: STATUS_COLORS[c.status] || '#6F7979',
                        border: '1px solid ' + (STATUS_COLORS[c.status] || '#6F7979') + '44',
                      }}>
                        {STATUS_LABELS[c.status] || c.status}
                      </span>
                    </td>
                    <td style={css.tableCell}>
                      <span style={{
                        fontSize: 12, color: 'var(--text-secondary)'
                      }}>
                        {new Date(c.created_at).toLocaleDateString('en-IN', {
                          day: 'numeric', month: 'short', year: 'numeric'
                        })}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                      <button
                        style={{
                          background: 'var(--primary)',
                          color: 'var(--on-primary)',
                          border: 'none',
                          borderRadius: 8,
                          padding: '8px 16px',
                          fontSize: 13,
                          fontWeight: 600,
                          cursor: 'pointer',
                          boxShadow: '0 2px 8px rgba(0,102,102,0.2)',
                          transition: 'all 0.2s',
                        }}
                        onClick={e => { e.stopPropagation(); onSelectCase(c); }}
                      >
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

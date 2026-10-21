import React, { useState, useEffect, useMemo } from 'react';
import API from '../api';
import { css, fmt } from '../theme';
import { EmptyState, Alert, Button, Badge, Skeleton, SkeletonTableRows } from './UI';

const DISPUTE_ICONS = {
  delayed_payment: '⏰', non_payment: '🚫', short_payment: '📉',
  quality_dispute: '🔍', quantity_dispute: '📦', contract_breach: '📋',
};
const STATUS_COLORS = {
  draft:       '#6F7979',
  submitted:   '#1D4ED8',
  in_progress: '#B45309',
  agreement:   '#0E9F6E',
  closed:      '#006666',
  escalated:   '#BA1A1A',
};
const STATUS_LABELS = {
  draft: 'Draft', submitted: 'Submitted', in_progress: 'In Progress',
  agreement: 'Agreement', closed: 'Closed', escalated: 'Escalated',
};

export default React.memo(function CaseDashboard({ user, onSelectCase, onCreateCase, refreshKey }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  useEffect(() => {
    // Guest/demo mode has no JWT — don't hit the API, it would 401 and
    // overwrite the real error state with "Failed to load cases".
    if (user?.is_guest) { setCases([]); setLoading(false); return; }
    let cancelled = false;
    setLoading(true); setErr('');
    API.get('/api/cases')
      .then(r => { if (!cancelled) setCases(r.data); })
      .catch(() => { if (!cancelled) setErr('Failed to load cases'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [refreshKey, user?.is_guest]);

  const stats = useMemo(() => [
    { label: 'Total Cases',   value: cases.length,          color: 'var(--primary)' },
    { label: 'Active',        value: cases.filter(c => c.status === 'in_progress').length, color: '#F59E0B' },
    { label: 'Agreed',        value: cases.filter(c => c.status === 'agreement').length,     color: '#10B981' },
    { label: 'Total Claim',   value: fmt(cases.reduce((s, c) => s + (c.claim_amount || 0), 0)), color: 'var(--primary)' },
  ], [cases]);

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
        <Button variant="primary" onClick={onCreateCase}>
          <span aria-hidden="true">+</span> New Case
        </Button>
      </div>

      {/* Stats cards. While loading these show skeletons rather than zeros:
          the previous version rendered "0" first and then jumped to the real
          numbers, which read as wrong data and shifted the layout. */}
      <div className="grid-cols-4" style={{ display: 'grid', gap: 16, marginBottom: 24 }}>
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card" style={{ padding: '20px 16px', textAlign: 'center' }}>
              <Skeleton width={72} height={30} radius="var(--r-sm)" style={{ margin: '0 auto 10px' }} />
              <Skeleton width={92} height={11} style={{ margin: '0 auto' }} />
            </div>
          ))
        ) : (
          stats.map(s => (
            <div
              key={s.label}
              className="card card-hover"
              style={{ padding: '20px 16px', textAlign: 'center' }}
            >
              <div style={{
                fontSize: 32, fontWeight: 800, color: s.color,
                marginBottom: 6, letterSpacing: '-0.02em',
              }}>
                {s.value}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>
                {s.label}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Cases table */}
      <div className="card" style={{ padding: 20 }}>
        <div style={{
          fontSize: 15, fontWeight: 700, marginBottom: 16,
          color: 'var(--on-surface)'
        }}>
          Your Cases
        </div>

        {err && (
          <Alert msg={err} type="error" />
        )}

        {!loading && cases.length === 0 ? (
          user?.is_guest ? (
            <EmptyState
              icon="👋"
              text="Welcome to the demo"
              subtext="You're exploring without an account — sign in to load real cases, or create a case to try the AI pipeline."
            />
          ) : (
          <EmptyState
            icon="📁"
            text="No cases yet"
            subtext="Create your first dispute case to get started with the AI pipeline"
            action={<Button variant="primary" onClick={onCreateCase}>Create your first case</Button>}
          />
          )
        ) : (
          <div className="table-wrap">
            <table className="institutional" aria-busy={loading || undefined}>
              <thead>
                <tr>
                  <th style={css.tableHead}>Case</th>
                  <th style={css.tableHead}>Type</th>
                  <th style={css.tableHead}>Claim Amount</th>
                  <th style={css.tableHead}>Status</th>
                  <th style={css.tableHead}>Created</th>
                  <th style={{ ...css.tableHead, width: 120, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading && <SkeletonTableRows rows={4} cols={6} />}
                {!loading && cases.map(c => (
                  <tr
                    key={c.id}
                    className="is-clickable"
                    tabIndex={0}
                    aria-label={`Open case ${c.case_number || c.id}`}
                    onClick={() => onSelectCase(c)}
                    onKeyDown={e => {
                      // Only when the row itself is focused — otherwise the
                      // nested "Open" button would trigger this a second time.
                      if (e.target !== e.currentTarget) return;
                      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelectCase(c); }
                    }}
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
                      <Badge
                        text={STATUS_LABELS[c.status] || c.status}
                        color={STATUS_COLORS[c.status] || '#6F7979'}
                      />
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
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={e => { e.stopPropagation(); onSelectCase(c); }}
                      >
                        Open →
                      </Button>
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
})

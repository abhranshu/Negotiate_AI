import React, { useState } from 'react';
import API, { getApiError } from '../api';
import { css } from '../theme';
import { Alert, Button } from './UI';

const DISPUTE_TYPES = [
  { value: 'delayed_payment',  label: 'Delayed Payment' },
  { value: 'non_payment',      label: 'Non Payment' },
  { value: 'short_payment',    label: 'Short Payment' },
  { value: 'quality_dispute',  label: 'Quality Dispute' },
  { value: 'quantity_dispute', label: 'Quantity Dispute' },
  { value: 'contract_breach',  label: 'Contract Breach' },
];
const STATES = ['MH','DL','GJ','KA','TN','UP','WB','RJ','HR','MP','TG','AP'];
const INDUSTRIES = [
  'textiles', 'food_processing', 'chemicals', 'engineering',
  'pharmaceuticals', 'auto_components', 'electronics', 'construction',
  'services', 'other',
];

function pretty(label) {
  return label.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function CreateCase({ onClose, onCreated }) {
  const [form, setForm] = useState({
    dispute_type: 'delayed_payment',
    claim_amount: '',
    overdue_days: '',
    description: '',
    state: 'MH',
    industry: 'textiles',
    respondent_email: '',
  });
  const [loading, setLoading] = useState(false);
  const [err, setErr]         = useState('');

  const submit = async () => {
    if (!form.claim_amount) { setErr('Claim amount is required'); return; }
    setErr(''); setLoading(true);
    try {
      await API.post('/api/cases', {
        ...form,
        claim_amount:  parseFloat(form.claim_amount),
        overdue_days:  parseInt(form.overdue_days) || 0,
        respondent_email: form.respondent_email || null,
      });
      onCreated();
    } catch (e) {
      setErr(getApiError(e, 'Failed to create case'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="modal-backdrop"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-case-title"
        style={{ padding: 28 }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginBottom: 24, paddingBottom: 16, borderBottom: '1px solid var(--border)' }}>
          <h2 id="new-case-title" style={{ fontSize: 18, fontWeight: 700, color: 'var(--on-surface)' }}>
            New Dispute Case
          </h2>
          <button
            type="button"
            className="btn btn-ghost btn-icon"
            aria-label="Close dialog"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        {err && <Alert msg={err} type="error" />}

        {/* Form */}
        <div className="grid-cols-2" style={{ display: 'grid', gap: 16 }}>
          <div>
            <label style={css.label} htmlFor="cc-dispute-type">Dispute Type</label>
            <select
              id="cc-dispute-type"
              style={css.select}
              value={form.dispute_type}
              onChange={e => setForm({ ...form, dispute_type: e.target.value })}
            >
              {DISPUTE_TYPES.map(d => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={css.label} htmlFor="cc-claim-amount">Claim Amount (₹)</label>
            <input
              id="cc-claim-amount"
              style={css.input}
              type="number"
              min="0"
              value={form.claim_amount}
              placeholder="e.g. 450,000"
              onChange={e => setForm({ ...form, claim_amount: e.target.value })}
            />
          </div>
          <div>
            <label style={css.label} htmlFor="cc-overdue-days">Overdue Days</label>
            <input
              id="cc-overdue-days"
              style={css.input}
              type="number"
              min="0"
              value={form.overdue_days}
              placeholder="e.g. 120"
              onChange={e => setForm({ ...form, overdue_days: e.target.value })}
            />
          </div>
          <div>
            <label style={css.label} htmlFor="cc-state">State (MSEFC Jurisdiction)</label>
            <select
              id="cc-state"
              style={css.select}
              value={form.state}
              onChange={e => setForm({ ...form, state: e.target.value })}
            >
              {STATES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={css.label} htmlFor="cc-industry">Industry</label>
          <select
            id="cc-industry"
            style={css.select}
            value={form.industry}
            onChange={e => setForm({ ...form, industry: e.target.value })}
          >
            {INDUSTRIES.map(i => (
              <option key={i} value={i}>{pretty(i)}</option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={css.label} htmlFor="cc-respondent-email">Respondent Email <span style={{ color: 'var(--text-secondary)' }}>(optional)</span></label>
          <input
            id="cc-respondent-email"
            style={css.input}
            type="email"
            value={form.respondent_email}
            placeholder="buyer@theircompany.com"
            onChange={e => setForm({ ...form, respondent_email: e.target.value })}
          />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={css.label} htmlFor="cc-description">Dispute Description</label>
          <textarea
            id="cc-description"
            style={{ ...css.input, minHeight: 100, resize: 'vertical',
              fontFamily: "'Inter', sans-serif" }}
            value={form.description}
            placeholder="Describe the payment dispute, key dates, and context..."
            onChange={e => setForm({ ...form, description: e.target.value })}
          />
        </div>

        {/* Info note */}
        <div style={{
          padding: '12px 14px',
          background: 'var(--surface)',
          borderRadius: 8,
          fontSize: 12,
          color: 'var(--text-secondary)',
          border: '1px solid var(--border)',
          marginBottom: 20,
          lineHeight: 1.6,
        }}>
          After creating the case you can upload documents, run outcome prediction,
          start AI-mediated negotiation, and generate a legal settlement agreement.
        </div>

        {/* Actions */}
        <div className="btn-row">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="primary" block loading={loading} onClick={submit}>
            {loading ? 'Creating…' : 'Create Case'}
          </Button>
        </div>
      </div>
    </div>
  );
}

// Modal with its own form state — no reason to re-render it when AppShell does.
export default React.memo(CreateCase);

import React, { useState } from 'react';
import API, { getApiError } from '../api';
import { css } from '../theme';
import { Spinner, Alert } from './UI';

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

export default function CreateCase({ onClose, onCreated }) {
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
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0,0,0,0.4)',
      backdropFilter: 'blur(4px)',
      zIndex: 200,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 16,
    }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div style={{
        background: 'var(--surface-container-lowest)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        padding: 28,
        width: 560,
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
        animation: 'scaleIn 0.3s ease-out both',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginBottom: 24, paddingBottom: 16, borderBottom: '1px solid var(--border)' }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--on-surface)' }}>
            New Dispute Case
          </div>
          <button
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: 24, color: 'var(--text-secondary)',
              padding: '4px 8px', borderRadius: 4,
              lineHeight: 1,
            }}
            onClick={onClose}
            onMouseEnter={e => e.target.style.color = 'var(--on-surface)'}
            onMouseLeave={e => e.target.style.color = 'var(--text-secondary)'}
          >
            ×
          </button>
        </div>

        {err && <Alert msg={err} type="error" />}

        {/* Form */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <label style={css.label}>Dispute Type</label>
            <select
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
            <label style={css.label}>Claim Amount (₹)</label>
            <input
              style={css.input}
              type="number"
              min="0"
              value={form.claim_amount}
              placeholder="e.g. 450,000"
              onChange={e => setForm({ ...form, claim_amount: e.target.value })}
            />
          </div>
          <div>
            <label style={css.label}>Overdue Days</label>
            <input
              style={css.input}
              type="number"
              min="0"
              value={form.overdue_days}
              placeholder="e.g. 120"
              onChange={e => setForm({ ...form, overdue_days: e.target.value })}
            />
          </div>
          <div>
            <label style={css.label}>State (MSEFC Jurisdiction)</label>
            <select
              style={css.select}
              value={form.state}
              onChange={e => setForm({ ...form, state: e.target.value })}
            >
              {STATES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={css.label}>Industry</label>
          <select
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
          <label style={css.label}>Respondent Email <span style={{ color: 'var(--text-secondary)' }}>(optional)</span></label>
          <input
            style={css.input}
            type="email"
            value={form.respondent_email}
            placeholder="buyer@theircompany.com"
            onChange={e => setForm({ ...form, respondent_email: e.target.value })}
          />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={css.label}>Dispute Description</label>
          <textarea
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
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            style={{
              ...css.btnGhost,
              flex: 1,
              color: 'var(--text-secondary)',
              borderColor: 'var(--border)',
            }}
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            style={{
              ...css.btn,
              flex: 2,
              background: 'var(--primary)',
              color: 'var(--on-primary)',
              boxShadow: '0 2px 8px rgba(0,102,102,0.25)',
            }}
            onClick={submit}
            disabled={loading}
          >
            {loading && <Spinner />}
            {loading ? 'Creating...' : 'Create Case'}
          </button>
        </div>
      </div>
    </div>
  );
}

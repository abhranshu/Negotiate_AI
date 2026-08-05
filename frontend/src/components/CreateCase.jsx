import React, { useState } from 'react';
import API from '../api';
import { T, css } from '../theme';
import { Spinner, Alert } from './UI';

export default function CreateCase({ onClose, onCreated }) {
  const [form, setForm] = useState({
    dispute_type: 'delayed_payment', claim_amount: '', overdue_days: '',
    description: '', state: 'MH', industry: 'textiles', respondent_email: '',
  });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  const submit = async () => {
    if (!form.claim_amount) { setErr('Claim amount is required'); return; }
    setErr(''); setLoading(true);
    try {
      await API.post('/api/cases', {
        ...form,
        claim_amount: parseFloat(form.claim_amount),
        overdue_days: parseInt(form.overdue_days) || 0,
        respondent_email: form.respondent_email || null,
      });
      onCreated();
    } catch (e) { setErr(e.response?.data?.detail || 'Failed to create case'); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 200,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{ ...css.card, width: 580, margin: 0, maxHeight: '90vh', overflowY: 'auto' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <div style={{ fontSize: 18, fontWeight: 700 }}>📋 New Dispute Case</div>
          <button style={{ ...css.btn, background: 'none', color: T.muted, fontSize: 22, padding: '2px 8px' }}
            onClick={onClose}>×</button>
        </div>

        {err && <Alert msg={err} type="error" />}

        {/* Form Grid */}
        <div style={css.grid2}>
          <div>
            <label style={css.label}>Dispute Type *</label>
            <select style={css.select} value={form.dispute_type}
              onChange={e => setForm({ ...form, dispute_type: e.target.value })}>
              {['delayed_payment','non_payment','short_payment','quality_dispute','quantity_dispute','contract_breach']
                .map(d => <option key={d} value={d}>{
                  d.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>)}
            </select>
          </div>
          <div>
            <label style={css.label}>Claim Amount (₹) *</label>
            <input style={css.input} type="number" value={form.claim_amount} placeholder="e.g. 450,000"
              onChange={e => setForm({ ...form, claim_amount: e.target.value })} />
          </div>
          <div>
            <label style={css.label}>Overdue Days</label>
            <input style={css.input} type="number" value={form.overdue_days} placeholder="e.g. 120"
              onChange={e => setForm({ ...form, overdue_days: e.target.value })} />
          </div>
          <div>
            <label style={css.label}>State (MSEFC Jurisdiction)</label>
            <select style={css.select} value={form.state} onChange={e => setForm({ ...form, state: e.target.value })}>
              {['MH','DL','GJ','KA','TN','UP','WB','RJ','HR','MP','TG','AP'].map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label style={css.label}>Industry</label>
          <select style={css.select} value={form.industry} onChange={e => setForm({ ...form, industry: e.target.value })}>
            {['textiles','food_processing','chemicals','engineering','pharmaceuticals',
              'auto_components','electronics','construction','services','other'].map(i =>
              <option key={i} value={i}>
                {i.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>)}
          </select>
        </div>

        <div>
          <label style={css.label}>Respondent Email (optional)</label>
          <input style={css.input} type="email" value={form.respondent_email} placeholder="buyer@theircompany.com"
            onChange={e => setForm({ ...form, respondent_email: e.target.value })} />
        </div>

        <div>
          <label style={css.label}>Dispute Description</label>
          <textarea style={{ ...css.input, minHeight: 90, resize: 'vertical', fontFamily: 'inherit' }}
            value={form.description} placeholder="Describe the payment dispute, key dates, and context..."
            onChange={e => setForm({ ...form, description: e.target.value })} />
        </div>

        {/* Info note */}
        <div style={{ padding: '10px 12px', background: T.bg, borderRadius: 8, fontSize: 12,
          color: T.muted, border: '1px dashed ' + T.border, marginBottom: 16 }}>
          🔍 &nbsp;After creating the case you can run Module 2 (documents), Module 3 (prediction),
          Module 4 (negotiation) and Module 5 (settlement) from the case dashboard.
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button style={{ ...css.btn, flex: 1, background: T.border, color: T.text, padding: '12px' }}
            onClick={onClose}>Cancel</button>
          <button style={{ ...css.btn, flex: 2, padding: '12px',
            background: `linear-gradient(135deg,${T.accent},${T.accent2})`, color: '#fff' }}
            onClick={submit} disabled={loading}>
            {loading && <Spinner />}Create Case →
          </button>
        </div>
      </div>
    </div>
  );
}

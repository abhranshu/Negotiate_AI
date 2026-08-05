import React, { useState } from 'react';
import API from '../api';
import { T, css } from '../theme';
import { Badge, Spinner } from './UI';

export default function AuthScreen({ onLogin, onGuestLogin }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ email: '', password: '', full_name: '', company_name: '', role: 'claimant' });
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setErr(''); setLoading(true);
    try {
      if (mode === 'register') {
        await API.post('/api/auth/register', form);
        const ld = new FormData();
        ld.append('username', form.email); ld.append('password', form.password);
        const r = await API.post('/api/auth/login', ld);
        localStorage.setItem('token', r.data.access_token);
      } else {
        const ld = new FormData();
        ld.append('username', form.email); ld.append('password', form.password);
        const r = await API.post('/api/auth/login', ld);
        localStorage.setItem('token', r.data.access_token);
      }
      onLogin();
    } catch (e) { setErr(e.response?.data?.detail || 'Something went wrong'); }
    finally { setLoading(false); }
  };

  const inp = (key, label, type = 'text', placeholder = '') => (
    <div style={{ marginBottom: 12 }}>
      <label style={css.label}>{label}</label>
      <input style={css.input} type={type} value={form[key]}
        onChange={e => setForm({ ...form, [key]: e.target.value })}
        placeholder={placeholder} />
    </div>
  );

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: `radial-gradient(ellipse at 30% 20%, #1a2540 0%, ${T.bg} 60%)` }}>
      <div style={{ width: 420 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 34, fontWeight: 800, background: `linear-gradient(135deg,${T.accent},${T.accent2})`,
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>⚖ NegotiateAI</div>
          <div style={{ color: T.muted, marginTop: 6, fontSize: 14 }}>MSME Online Dispute Resolution Platform</div>
          <div style={{ marginTop: 10, display: 'flex', gap: 8, justifyContent: 'center' }}>
            {['MSMED Act 2006', 'AI Mediated', 'Multilingual'].map(t => <Badge key={t} text={t} color={T.accent} />)}
          </div>
        </div>

        <div style={css.card}>
          <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
            {['login', 'register'].map(m => (
              <button key={m} style={{ ...css.tab, flex: 1, background: mode === m ? T.accent : T.surface,
                color: mode === m ? '#fff' : T.muted }}
                onClick={() => { setMode(m); setErr(''); }}>
                {m === 'login' ? '🔑 Sign In' : '📝 Register'}
              </button>
            ))}
          </div>

          {mode === 'register' && <>
            {inp('full_name', 'Full Name', 'text', 'Ramesh Sharma')}
            {inp('company_name', 'Company Name', 'text', 'Sharma Textiles Pvt Ltd')}
            <div style={{ marginBottom: 12 }}>
              <label style={css.label}>Role</label>
              <select style={css.select} value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
                <option value="claimant">Claimant (MSME Supplier)</option>
                <option value="respondent">Respondent (Buyer)</option>
              </select>
            </div>
          </>}

          {inp('email', 'Email Address', 'email', 'you@company.com')}
          {inp('password', 'Password', 'password', '••••••••')}

          {err && <div style={{ color: T.red, fontSize: 12, marginBottom: 12 }}>{err}</div>}

          <button style={{ ...css.btn, width: '100%', padding: '12px', fontSize: 14,
            background: `linear-gradient(135deg,${T.accent},${T.accent2})`, color: '#fff' }}
            onClick={submit} disabled={loading}>
            {loading && <Spinner />}{mode === 'login' ? 'Sign In →' : 'Create Account →'}
          </button>

          {/* ── Guest bypass ── */}
          <div style={{ textAlign: 'center', margin: '14px 0 2px', color: T.muted, fontSize: 12 }}>— or —</div>
          <button
            style={{ ...css.btn, width: '100%', padding: '11px', fontSize: 13,
              background: 'transparent', color: T.muted,
              border: '1px dashed ' + T.border }}
            onClick={onGuestLogin}>
            🚪 Continue as Guest (Demo Mode)
          </button>
        </div>

        <div style={{ textAlign: 'center', color: T.muted, fontSize: 11, marginTop: 16 }}>
          🎙 Voice &nbsp;·&nbsp; 📄 Documents &nbsp;·&nbsp; 📊 Prediction &nbsp;·&nbsp; 🤝 Negotiation &nbsp;·&nbsp; 📜 Settlement
        </div>
      </div>
    </div>
  );
}
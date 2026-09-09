import React, { useState } from 'react';
import API, { getApiError } from '../api';
import { css } from '../theme';
import { Badge, Spinner } from './UI';

export default function AuthScreen({ onLogin, onGuestLogin }) {
  const [mode, setMode]    = useState('login');
  const [form, setForm]    = useState({
    email: '', password: '', full_name: '', company_name: '', role: 'claimant'
  });
  const [err, setErr]      = useState('');
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const submit = async () => {
    setErr(''); setLoading(true);
    try {
      if (mode === 'register') {
        await API.post('/api/auth/register', form);
        const ld = new FormData();
        ld.append('username', form.email);
        ld.append('password', form.password);
        const r = await API.post('/api/auth/login', ld);
        localStorage.setItem('token', r.data.access_token);
      } else {
        const ld = new FormData();
        ld.append('username', form.email);
        ld.append('password', form.password);
        const r = await API.post('/api/auth/login', ld);
        localStorage.setItem('token', r.data.access_token);
      }
      onLogin();
    } catch (e) {
      setErr(getApiError(e, 'Something went wrong'));
    } finally {
      setLoading(false);
    }
  };

  const inp = (key, label, type = 'text', placeholder = '', options = {}) => (
    <div style={{ marginBottom: 16 }}>
      <label style={css.label}>{label}</label>
      <input
        style={{ ...css.input, ...(options.type === 'number' ? { type: 'number', min: 0 } : { type }) }}
        value={form[key]}
        onChange={e => setForm({ ...form, [key]: e.target.value })}
        placeholder={placeholder}
      />
    </div>
  );

  const selectInp = (key, label, options) => (
    <div style={{ marginBottom: 16 }}>
      <label style={css.label}>{label}</label>
      <select
        style={css.select}
        value={form[key]}
        onChange={e => setForm({ ...form, [key]: e.target.value })}
      >
        {options.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--surface)',
      padding: '24px'
    }}>
      <div style={{ width: '100%', maxWidth: 440 }}>
        {/* Logo + tagline */}
        <div style={{
          textAlign: 'center',
          marginBottom: 32,
          animation: 'fadeInDown 0.4s ease-out both'
        }}>
          <div style={{ fontSize: 36, fontWeight: 800, marginBottom: 4 }}>⚖</div>
          <div style={{
            fontSize: 24, fontWeight: 700,
            color: 'var(--primary)',
            letterSpacing: '-0.02em',
            marginBottom: 6,
            fontFamily: "'Inter', sans-serif"
          }}>
            NegotiateAI
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16 }}>
            MSME Online Dispute Resolution Platform
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
            {['MSMED Act 2006', 'AI Mediated', 'Multilingual'].map(t => (
              <Badge key={t} text={t} color="var(--primary)" />
            ))}
          </div>
        </div>

        {/* Card */}
        <div style={{
          background: 'var(--surface-container-lowest)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          padding: 28,
          boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
          animation: 'scaleIn 0.4s ease-out both'
        }}>
          {/* Mode toggle */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
            {['login', 'register'].map(m => (
              <button
                key={m}
                style={{
                  ...css.tab,
                  flex: 1,
                  height: 40,
                  background: mode === m ? 'var(--primary)' : 'var(--surface)',
                  color: mode === m ? 'var(--on-primary)' : 'var(--text-secondary)',
                  border: 'none',
                  boxShadow: mode === m ? '0 2px 8px rgba(0,102,102,0.25)' : 'none',
                }}
                onClick={() => { setMode(m); setErr(''); }}
              >
                {m === 'login' ? 'Sign In' : 'Register'}
              </button>
            ))}
          </div>

          {mode === 'register' && (
            <>
              {inp('full_name', 'Full Name', 'text', 'Ramesh Sharma')}
              {inp('company_name', 'Company Name', 'text', 'Sharma Textiles Pvt Ltd')}
              {selectInp('role', 'Role', [
                { value: 'claimant',  label: 'Claimant (MSME Supplier)' },
                { value: 'respondent', label: 'Respondent (Buyer)' },
              ])}
            </>
          )}

          {inp('email', 'Email Address', 'email', 'you@company.com')}

          <div style={{ marginBottom: 16 }}>
            <label style={css.label}>Password</label>
            <div style={{ position: 'relative' }}>
              <input
                style={{ ...css.input, paddingRight: 44, marginBottom: 0 }}
                type={showPw ? 'text' : 'password'}
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
                placeholder="Enter password"
              />
              <button
                type="button"
                aria-label={showPw ? 'Hide password' : 'Show password'}
                onClick={() => setShowPw(!showPw)}
                style={{
                  position: 'absolute', right: 12, top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer',
                  fontSize: 14, padding: 0, opacity: 0.6,
                  color: 'var(--text-secondary)',
                }}
              >
                {showPw ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          {err && (
            <div style={{
              color: 'var(--error)',
              fontSize: 13,
              marginBottom: 12,
              padding: '10px 14px',
              background: 'rgba(186,26,26,0.06)',
              border: '1px solid rgba(186,26,26,0.2)',
              borderRadius: 8,
            }}>
              {typeof err === 'string' ? err : JSON.stringify(err)}
            </div>
          )}

          <button
            style={{
              ...css.btn,
              width: '100%',
              padding: '12px',
              fontSize: 14,
              marginBottom: 16,
              boxShadow: '0 2px 8px rgba(0,102,102,0.25)',
            }}
            onClick={submit}
            disabled={loading}
          >
            {loading && <Spinner />}
            {mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>

          {/* Guest bypass */}
          <div style={{ textAlign: 'center', margin: '16px 0 4px', color: 'var(--text-secondary)', fontSize: 12 }}>
            — or —
          </div>
          <button
            className="app-btn app-ghost"
            style={{
              ...css.btnGhost,
              width: '100%',
              padding: '11px',
              fontSize: 13,
              color: 'var(--text-secondary)',
              borderColor: 'var(--border)',
            }}
            onClick={onGuestLogin}
          >
            Continue as Demo User
          </button>
        </div>

        {/* Footer */}
        <div style={{
          textAlign: 'center',
          color: 'var(--text-secondary)',
          fontSize: 11,
          marginTop: 20,
          lineHeight: 1.8
        }}>
          Voice · Documents · Prediction · Negotiation · Settlement
        </div>
      </div>
    </div>
  );
}

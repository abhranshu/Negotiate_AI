import React, { useState } from 'react';
import API, { getApiError } from '../api';
import { css } from '../theme';
import { Badge, Alert, Button } from './UI';

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

  // `name` + `autoComplete` let browsers and password managers fill these
  // correctly (they previously had neither, so sign-in never offered to save).
  const inp = (key, label, type = 'text', placeholder = '', options = {}) => (
    <div style={{ marginBottom: 16 }}>
      <label style={css.label} htmlFor={`auth-${key}`}>{label}</label>
      <input
        id={`auth-${key}`}
        name={key}
        type={type}
        style={css.input}
        value={form[key]}
        onChange={e => setForm({ ...form, [key]: e.target.value })}
        placeholder={placeholder}
        required
        autoComplete={options.autoComplete || 'off'}
        autoCapitalize={options.autoCapitalize}
        autoFocus={options.autoFocus}
        inputMode={options.inputMode}
        spellCheck={options.spellCheck}
      />
    </div>
  );

  // Real <form> semantics: Enter in any field submits, and assistive tech
  // announces this as a form rather than a stack of inputs.
  const submitForm = (e) => { e.preventDefault(); if (!loading) submit(); };

  const selectInp = (key, label, options) => (
    <div style={{ marginBottom: 16 }}>
      <label style={css.label} htmlFor={`auth-${key}`}>{label}</label>
      <select
        id={`auth-${key}`}
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

        {/* Card. The fields live in a real <form> so Enter submits; the demo
            button stays outside it because it is not a form action. */}
        <div style={{
          background: 'var(--surface-container-lowest)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          padding: 28,
          boxShadow: 'var(--shadow-sm)',
          animation: 'scaleIn 0.4s ease-out both'
        }}>
          {/* Mode toggle */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
            {['login', 'register'].map(m => (
              <button
                key={m}
                type="button"
                className={'tab' + (mode === m ? ' is-active' : '')}
                aria-pressed={mode === m}
                style={{ flex: 1 }}
                onClick={() => { setMode(m); setErr(''); }}
              >
                {m === 'login' ? 'Sign In' : 'Register'}
              </button>
            ))}
          </div>

          <form onSubmit={submitForm}>
            {mode === 'register' && (
              <>
                {inp('full_name', 'Full Name', 'text', 'Ramesh Sharma', {
                  autoComplete: 'name', autoCapitalize: 'words',
                })}
                {inp('company_name', 'Company Name', 'text', 'Sharma Textiles Pvt Ltd', {
                  autoComplete: 'organization', autoCapitalize: 'words',
                })}
                {selectInp('role', 'Role', [
                  { value: 'claimant',  label: 'Claimant (MSME Supplier)' },
                  { value: 'respondent', label: 'Respondent (Buyer)' },
                ])}
              </>
            )}

            {inp('email', 'Email Address', 'email', 'you@company.com', {
              autoComplete: 'email', inputMode: 'email', autoCapitalize: 'none',
              spellCheck: false, autoFocus: mode === 'login',
            })}

            <div style={{ marginBottom: 16 }}>
              <label style={css.label} htmlFor="auth-password">Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  id="auth-password"
                  name="password"
                  style={{ ...css.input, paddingRight: 72, marginBottom: 0 }}
                  type={showPw ? 'text' : 'password'}
                  value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  placeholder="Enter password"
                  required
                  autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                />
                <button
                  type="button"
                  className="btn btn-plain"
                  aria-label={showPw ? 'Hide password' : 'Show password'}
                  aria-pressed={showPw}
                  onClick={() => setShowPw(!showPw)}
                  style={{ position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)' }}
                >
                  {showPw ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            <Alert msg={err} type="error" />

            <Button
              type="submit"
              variant="primary"
              block
              size="lg"
              loading={loading}
              style={{ marginBottom: 16 }}
            >
              {mode === 'login' ? 'Sign In' : 'Create Account'}
            </Button>
          </form>

          {/* Guest bypass */}
          <div style={{ textAlign: 'center', margin: '16px 0 4px', color: 'var(--text-secondary)', fontSize: 12 }}>
            — or —
          </div>
          <Button variant="ghost" block onClick={onGuestLogin}>
            Continue as Demo User
          </Button>
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

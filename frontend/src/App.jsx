import React, { useState, useEffect } from 'react';
import API from './api';
import { T, css } from './theme';
import AuthScreen from './components/AuthScreen';
import CaseDashboard from './components/CaseDashboard';
import CaseDetail from './components/CaseDetail';
import CreateCase from './components/CreateCase';

export default function App() {
  const [user, setUser]               = useState(null);
  const [loading, setLoading]         = useState(true);
  const [view, setView]               = useState('dashboard'); // dashboard | case | create
  const [selectedCase, setSelectedCase] = useState(null);
  const [refreshKey, setRefreshKey]     = useState(0);

  useEffect(() => {
    injectGlobalStyles();
    checkSession();
  }, []);

  function injectGlobalStyles() {
    if (document.getElementById('negotiate-ai-global-styles')) return; // guard against duplicate injection
    const style = document.createElement('style');
    style.id = 'negotiate-ai-global-styles';
    style.innerHTML = `
      * { box-sizing: border-box; }
      body { margin: 0; background: ${T.bg}; }
      @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      ::-webkit-scrollbar { width: 6px; height: 6px; }
      ::-webkit-scrollbar-track { background: ${T.surface}; }
      ::-webkit-scrollbar-thumb { background: ${T.border}; border-radius: 3px; }
      ::placeholder { color: #475569; }
      button:hover { opacity: 0.85; transform: translateY(-1px); }
      button:active { transform: translateY(0); }
      button:disabled { opacity: 0.5 !important; cursor: not-allowed !important; transform: none !important; }
      input:focus, select:focus, textarea:focus { border-color: ${T.accent} !important; box-shadow: 0 0 0 2px ${T.accent}33; }
      a { color: ${T.accent}; }
    `;
    document.head.appendChild(style);
  }

  async function checkSession() {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const r = await API.get('/api/auth/me');
        setUser(r.data);
      } catch { localStorage.removeItem('token'); }
    }
    setLoading(false);
  }

  function handleLogin() { checkSession(); }

  function handleGuestLogin() {
    setUser({ full_name: 'Guest User', email: 'guest@demo.com', role: 'claimant', is_guest: true });
  }

  function handleLogout() {
    localStorage.removeItem('token');
    setUser(null);
    setView('dashboard');
    setSelectedCase(null);
  }

  function handleSelectCase(caseItem) {
    setSelectedCase(caseItem);
    setView('case');
  }

  function handleCaseCreated() {
    setView('dashboard');
    setRefreshKey(k => k + 1);
  }

  // ── Loading ──────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: T.bg, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 16 }}>
        <div style={{ fontSize: 48 }}>⚖️</div>
        <div style={{ color: T.muted }}>Loading NegotiateAI...</div>
      </div>
    );
  }

  // ── Auth required ────────────────────────────────────────────────────────────
  if (!user) return <AuthScreen onLogin={handleLogin} onGuestLogin={handleGuestLogin} />;

  // ── Main app ──────────────────────────────────────────────────────────────────
  return (
    <div style={css.app}>
      {/* Header */}
      <header style={css.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ ...css.logo, cursor: 'pointer' }} onClick={() => setView('dashboard')}>
            ⚖️ NegotiateAI
          </div>
          <div style={{ fontSize: 12, color: T.muted, display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: T.green, display: 'inline-block' }} />
            AI Mediation Active
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 13, fontWeight: 600 }}>{user.full_name}</div>
            <div style={{ fontSize: 11, color: T.muted }}>{user.role} · {user.email}</div>
          </div>
          <button style={{ ...css.btn, background: T.border, color: T.text, fontSize: 12 }} onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </header>

      {/* Body */}
      <main>
        {view === 'dashboard' && (
          <CaseDashboard
            user={user}
            onSelectCase={handleSelectCase}
            onCreateCase={() => setView('create')}
            refreshKey={refreshKey}
          />
        )}
        {view === 'create' && (
          <CreateCase
            onClose={() => setView('dashboard')}
            onCreated={handleCaseCreated}
          />
        )}
        {view === 'case' && selectedCase && (
          <CaseDetail
            caseData={selectedCase}
            onBack={() => setView('dashboard')}
            onUpdate={setSelectedCase}
          />
        )}
      </main>
    </div>
  );
}
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../api';
import AuthScreen from './AuthScreen';
import CaseDashboard from './CaseDashboard';
import CaseDetail from './CaseDetail';
import CreateCase from './CreateCase';
import { css } from '../theme';

function AppShell() {
  const [user, setUser]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [view, setView]     = useState('dashboard');
  const [selectedCase, setSelectedCase] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const navigate = useNavigate();

  useEffect(() => { checkSession(); }, []);

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
    setUser({ full_name: 'Demo User', email: 'demo@negotiate.ai', role: 'claimant', is_guest: true });
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
    navigate('/app/case');
  }

  function handleCaseCreated() {
    setView('dashboard');
    setRefreshKey(k => k + 1);
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--surface)', display: 'flex',
        flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
        <div style={{ width: 40, height: 40, border: '3px solid var(--border)',
          borderTopColor: 'var(--primary)', borderRadius: '50%',
          animation: 'spin 0.7s linear infinite' }} />
        <div style={{ color: 'var(--text-secondary)', fontSize: 14, fontWeight: 500 }}>
          Loading NegotiateAI...
        </div>
      </div>
    );
  }

  if (!user) return <AuthScreen onLogin={handleLogin} onGuestLogin={handleGuestLogin} />;

  return (
    <div style={{ minHeight: '100vh', background: 'var(--surface)', color: 'var(--on-surface)',
      fontFamily: "'Inter', sans-serif" }}>
      {/* ── Top Bar (DESIGN.md: clean top-bar, white bg, subtle bottom border) ── */}
      <header style={css.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ cursor: 'pointer' }}
            onClick={() => { setView('dashboard'); navigate('/app'); setSelectedCase(null); }}>
            <span style={{ fontSize: 22 }}>⚖</span>
            <span style={css.logo}>NegotiateAI</span>
          </div>
          <div style={{ marginLeft: 8, padding: '4px 12px', borderRadius: 100,
            background: 'rgba(0,102,102,0.08)', border: '1px solid rgba(0,102,102,0.2)',
            fontSize: 11, fontWeight: 600, color: 'var(--primary)' }}>
            AI Mediation Active
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--on-surface)' }}>
              {user.full_name}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 1 }}>
              {user.role} · {user.email}
            </div>
          </div>
          {user.is_guest && (
            <div style={{ padding: '4px 10px', borderRadius: 100,
              background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)',
              fontSize: 11, fontWeight: 600, color: '#D97706' }}>
              Demo Mode
            </div>
          )}
          <button className="app-btn app-ghost"
            style={{ ...css.btnGhost, color: 'var(--text-secondary)',
              borderColor: 'var(--border)' }}
            onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main style={{ maxWidth: 1280, margin: '0 auto', padding: '24px 24px 48px' }}>
        {view === 'dashboard' && (
          <CaseDashboard
            user={user}
            onSelectCase={handleSelectCase}
            onCreateCase={() => setView('create')}
            refreshKey={refreshKey}
          />
        )}
        {view === 'create' && (
          <CreateCase onClose={() => setView('dashboard')} onCreated={handleCaseCreated} />
        )}
        {view === 'case' && selectedCase && (
          <CaseDetail
            caseData={selectedCase}
            onBack={() => { setView('dashboard'); navigate('/app'); setSelectedCase(null); }}
            onUpdate={setSelectedCase}
          />
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border)',
        padding: '20px 24px',
        textAlign: 'center',
        fontSize: 12,
        color: 'var(--text-secondary)'
      }}>
        NegotiateAI — MSME Online Dispute Resolution Platform ·
        Powered by MSMED Act 2006 · AI-mediated negotiation
      </footer>
    </div>
  );
}

export default AppShell;

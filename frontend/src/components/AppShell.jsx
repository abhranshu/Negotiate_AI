import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../api';
import AuthScreen from './AuthScreen';
import CaseDashboard from './CaseDashboard';
import CaseDetail from './CaseDetail';
import CreateCase from './CreateCase';
import { Button } from './UI';

function AppShell() {
  const [user, setUser]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [view, setView]     = useState('dashboard');
  const [selectedCase, setSelectedCase] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const navigate = useNavigate();

  useEffect(() => { checkSession(); }, []);

  // Start every view at the top. Opening a case from halfway down the dashboard
  // otherwise kept the old scroll offset and left the case header off-screen.
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [view, selectedCase?.id]);

  // Per-view document title, so browser tabs and history entries are
  // distinguishable instead of all reading "NegotiateAI".
  useEffect(() => {
    document.title =
      view === 'case' && selectedCase?.case_number ? selectedCase.case_number + ' · NegotiateAI'
      : view === 'create' ? 'New Case · NegotiateAI'
      : 'Dashboard · NegotiateAI';
  }, [view, selectedCase]);

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

  const handleLogin = useCallback(() => { checkSession(); }, []);

  const handleGuestLogin = useCallback(() => {
    setUser({ full_name: 'Demo User', email: 'demo@negotiate.ai', role: 'claimant', is_guest: true });
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('token');
    setUser(null);
    setView('dashboard');
    setSelectedCase(null);
  }, []);

  const handleSelectCase = useCallback((caseItem) => {
    setSelectedCase(caseItem);
    setView('case');
    navigate('/app/case');
  }, [navigate]);

  const handleCaseCreated = useCallback(() => {
    setView('dashboard');
    setRefreshKey(k => k + 1);
  }, []);

  // Stable handlers: inline arrows here would hand the memoized children a new
  // prop identity on every AppShell render and defeat React.memo.
  const goToDashboard = useCallback(() => {
    setView('dashboard');
    setSelectedCase(null);
    navigate('/app');
  }, [navigate]);

  const openCreateCase = useCallback(() => setView('create'), []);
  const closeCreateCase = useCallback(() => setView('dashboard'), []);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--surface)', display: 'flex',
        flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
        <div style={{ width: 40, height: 40, border: '3px solid var(--border)',
          borderTopColor: 'var(--primary)', borderRadius: '50%',
          animation: 'spin 0.7s linear infinite' }} />
        <div style={{ color: 'var(--text-secondary)', fontSize: 14, fontWeight: 500 }}>
          Loading NegotiateAI…
        </div>
      </div>
    );
  }

  if (!user) return <AuthScreen onLogin={handleLogin} onGuestLogin={handleGuestLogin} />;

  return (
    <div style={{ minHeight: '100vh', background: 'var(--surface)', color: 'var(--on-surface)' }}>
      <a href="#main" className="skip-link">Skip to content</a>

      {/* ── Top Bar ── */}
      <header className="app-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}>
          <div
            className="app-brand"
            role="button"
            tabIndex={0}
            aria-label="Go to dashboard"
            onClick={goToDashboard}
            onKeyDown={e => {
              if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); goToDashboard(); }
            }}
          >
            <span aria-hidden="true" style={{ fontSize: 22, marginRight: 8 }}>⚖</span>
            <span className="app-logo-text">NegotiateAI</span>
          </div>
          <div className="app-pill">AI Mediation Active</div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}>
          <div style={{ textAlign: 'right', minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--on-surface)',
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user.full_name}
            </div>
            <div className="app-header-meta" style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 1 }}>
              {user.role} · {user.email}
            </div>
          </div>
          {user.is_guest && (
            <span style={{ padding: '4px 10px', borderRadius: 'var(--r-pill)', whiteSpace: 'nowrap',
              background: 'rgba(180,83,9,0.09)', border: '1px solid rgba(180,83,9,0.25)',
              fontSize: 11, fontWeight: 600, color: 'var(--warning)' }}>
              Demo Mode
            </span>
          )}
          <Button variant="ghost" size="sm" onClick={handleLogout}>Sign Out</Button>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main id="main" className="page-container">
        {view === 'dashboard' && (
          <CaseDashboard
            user={user}
            onSelectCase={handleSelectCase}
            onCreateCase={openCreateCase}
            refreshKey={refreshKey}
          />
        )}
        {view === 'create' && (
          <CreateCase onClose={closeCreateCase} onCreated={handleCaseCreated} />
        )}
        {view === 'case' && selectedCase && (
          <CaseDetail
            caseData={selectedCase}
            onBack={goToDashboard}
            onUpdate={setSelectedCase}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        NegotiateAI — MSME Online Dispute Resolution Platform ·
        Powered by MSMED Act 2006 · AI-mediated negotiation
      </footer>
    </div>
  );
}

export default AppShell;

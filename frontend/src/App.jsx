import React, { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

// ── Route-level code splitting ────────────────────────────────────────────────
// These two bundles share almost nothing: the landing page is a static marketing
// page (animations, copy, no app logic) while AppShell pulls in the whole
// five-module app. Lazy-loading them means a visitor to /app never downloads
// the landing page's code, and vice versa.
const LandingPage = lazy(() => import('./components/LandingPage'));
const AppShell    = lazy(() => import('./components/AppShell'));

function RouteFallback() {
  return (
    <div style={{
      minHeight: '100vh', background: 'var(--surface)', display: 'flex',
      flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16,
    }}>
      <div style={{
        width: 40, height: 40, border: '3px solid var(--border)',
        borderTopColor: 'var(--primary)', borderRadius: '50%',
        animation: 'spin 0.7s linear infinite',
      }} />
      <div style={{ color: 'var(--text-secondary)', fontSize: 14, fontWeight: 500 }}>
        Loading…
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<AppShell />} />
        <Route path="/app/*" element={<AppShell />} />
        <Route path="*" element={<LandingPage />} />
      </Routes>
    </Suspense>
  );
}

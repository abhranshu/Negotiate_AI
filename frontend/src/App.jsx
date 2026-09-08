import React from 'react';
import { Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import AppShell from './components/AppShell';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/app" element={<AppShell />} />
      <Route path="/app/*" element={<AppShell />} />
      <Route path="*" element={<LandingPage />} />
    </Routes>
  );
}

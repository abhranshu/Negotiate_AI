import React, { useState, useEffect, useCallback, useRef, lazy, Suspense } from 'react';
import API, { getApiError } from '../api';
import { css, fmt } from '../theme';
import { Badge, Spinner, Alert, Tab, Button, Skeleton, SkeletonCard } from './UI';
import { useDebouncedCallback } from '../hooks/useDebouncedCallback';

// ── Tab-level code splitting ──────────────────────────────────────────────────
// The three heavy panels (ML prediction + SHAP charts, the negotiation room with
// its WebSocket, the settlement generator) are each their own chunk. A user who
// only reads the overview never downloads any of them.
const PredictionPanel = lazy(() => import('./PredictionPanel'));
const NegotiationChat = lazy(() => import('./NegotiationChat'));
const SettlementPanel = lazy(() => import('./SettlementPanel'));

function PanelFallback() {
  return (
    <div style={{ textAlign: 'center', padding: 60 }}>
      <div style={{
        width: 24, height: 24, margin: '0 auto 12px',
        border: '3px solid var(--border)',
        borderTopColor: 'var(--primary)',
        borderRadius: '50%',
        animation: 'spin 0.7s linear infinite',
      }} />
      <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
        Loading module…
      </div>
    </div>
  );
}

// Pause length before the dispute description is autosaved while typing.
const TRANSCRIPT_AUTOSAVE_MS = 800;

const STATUS_COLORS = {
  draft:       '#6F7979',
  submitted:   '#3B82F6',
  in_progress: '#F59E0B',
  agreement:   '#10B981',
  closed:      '#006666',
  escalated:   '#BA1A1A',
};
const DISPUTE_ICONS = {
  delayed_payment: '⏰', non_payment: '🚫', short_payment: '📉',
  quality_dispute: '🔍', quantity_dispute: '📦', contract_breach: '📋',
};
const STATUS_LABELS = {
  draft: 'Draft', submitted: 'Submitted', in_progress: 'In Progress',
  agreement: 'Agreement', closed: 'Closed', escalated: 'Escalated',
};

const InfoCard = React.memo(function InfoCard({ icon, label, value, color }) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 8,
      padding: '16px 18px',
    }}>
      <div style={{
        fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)',
        marginBottom: 6, letterSpacing: '0.03em'
      }}>
        <span style={{ marginRight: 6 }}>{icon}</span> {label}
      </div>
      <div style={{
        fontSize: 18, fontWeight: 700,
        color: color || 'var(--on-surface)',
        fontFamily: "'Inter', sans-serif",
      }}>
        {value || '—'}
      </div>
    </div>
  );
});

/* ─── Overview Tab ── */
const OverviewTab = React.memo(function OverviewTab({ c, docs, onRefresh }) {
  const stats = [
    { icon: '💰', label: 'Claim Amount',   value: fmt(c.claim_amount),          color: 'var(--primary)' },
    { icon: '⏱️', label: 'Overdue Days',   value: c.overdue_days ? c.overdue_days + ' days' : '—', color: '#F59E0B' },
    { icon: '📄', label: 'Documents',      value: docs.length + ' uploaded',   color: '#3B82F6' },
    { icon: '🏛️', label: 'State',          value: c.state || '—',              color: '#8B5CF6' },
    { icon: '🏭', label: 'Industry',       value: c.industry?.replace(/_/g, ' ') || '—', color: '#10B981' },
    { icon: '⚖️', label: 'Dispute Type',   value: c.dispute_type?.replace(/_/g, ' ') || '—', color: '#F59E0B' },
  ];

  const pipelineSteps = [
    { icon: '🎙️', label: 'Voice Processing',   done: false },
    { icon: '📄', label: 'Document Analysis',   done: docs.length > 0 },
    { icon: '📊', label: 'Outcome Prediction',  done: !!c.settlement_probability },
    { icon: '🤝', label: 'Negotiation',         done: !!c.agreement_amount },
    { icon: '📜', label: 'Settlement',          done: !!c.agreement_text },
  ];

  return (
    <div>
      {/* Stat cards */}
      <div className="grid-cols-3" style={{ display: 'grid', gap: 12, marginBottom: 20 }}>
        {stats.map(s => <InfoCard key={s.label} {...s} />)}
      </div>

      {/* Description */}
      {c.description && (
        <div style={{
          background: 'var(--surface-container-lowest)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          padding: 20,
          marginBottom: 16,
        }}>
          <div style={{
            fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)',
            marginBottom: 8, letterSpacing: '0.03em'
          }}>
            DESCRIPTION
          </div>
          <p style={{
            fontSize: 13, margin: 0, lineHeight: 1.7,
            color: 'var(--on-surface-variant)'
          }}>{c.description}</p>
        </div>
      )}

      {/* Pipeline status */}
      <div style={{
        background: 'var(--surface-container-lowest)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        padding: 20,
      }}>
        <div style={{
          fontSize: 13, fontWeight: 700, marginBottom: 16,
          color: 'var(--on-surface)'
        }}>
          ML Pipeline Status
        </div>
        {pipelineSteps.map((step, i) => (
          <div key={step.label} style={{
            display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%',
              background: step.done ? 'rgba(16,185,129,0.1)' : 'var(--surface)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: '1px solid ' + (step.done ? '#10B981' : 'var(--border)'),
              flexShrink: 0,
              fontSize: 14, fontWeight: 700,
              color: step.done ? '#10B981' : 'var(--text-secondary)',
            }}>
              {step.done ? '✓' : step.icon}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{
                fontSize: 13, fontWeight: 600,
                color: step.done ? '#10B981' : 'var(--text-secondary)',
              }}>{step.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 1 }}>
                {step.done ? 'Complete' : 'Pending'}
              </div>
            </div>
            <span style={{
              padding: '4px 10px', borderRadius: 100, fontSize: 11, fontWeight: 600,
              background: step.done ? 'rgba(16,185,129,0.1)' : 'var(--surface)',
              color: step.done ? '#10B981' : 'var(--text-secondary)',
              border: '1px solid ' + (step.done ? '#10B981' : 'var(--border)'),
            }}>
              {step.done ? 'Done' : 'Pending'}
            </span>
          </div>
        ))}
      </div>

      {/* Quick prediction summary */}
      {c.settlement_probability && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(0,102,102,0.06), rgba(6,182,212,0.06))',
          border: '1px solid rgba(0,102,102,0.2)',
          borderRadius: 8,
          padding: 20,
          marginTop: 16,
        }}>
          <div style={{
            fontSize: 13, fontWeight: 700, marginBottom: 14,
            color: 'var(--on-surface)'
          }}>
            Quick Prediction Summary
          </div>
          <div className="grid-cols-3" style={{ display: 'grid', gap: 12 }}>
            <div style={{
              textAlign: 'center', padding: '12px 8px',
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 8,
            }}>
              <div style={{
                fontSize: 11, color: 'var(--text-secondary)',
                marginBottom: 4, fontWeight: 500
              }}>Settlement Probability</div>
              <div style={{
                fontSize: 24, fontWeight: 800, color: '#10B981',
                fontFamily: "'Inter', sans-serif"
              }}>
                {(c.settlement_probability * 100).toFixed(1)}%
              </div>
            </div>
            <div style={{
              textAlign: 'center', padding: '12px 8px',
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 8,
            }}>
              <div style={{
                fontSize: 11, color: 'var(--text-secondary)',
                marginBottom: 4, fontWeight: 500
              }}>Range Low</div>
              <div style={{
                fontSize: 24, fontWeight: 800, color: '#006666',
                fontFamily: "'Inter', sans-serif"
              }}>
                {fmt(c.settlement_range_low)}
              </div>
            </div>
            <div style={{
              textAlign: 'center', padding: '12px 8px',
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 8,
            }}>
              <div style={{
                fontSize: 11, color: 'var(--text-secondary)',
                marginBottom: 4, fontWeight: 500
              }}>Range High</div>
              <div style={{
                fontSize: 24, fontWeight: 800, color: '#06B6D4',
                fontFamily: "'Inter', sans-serif"
              }}>
                {fmt(c.settlement_range_high)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

/* ─── Documents & Voice Tab ── */
const DocsVoiceTab = React.memo(function DocsVoiceTab({ c, docs, onRefresh }) {
  const [voiceFile, setVoiceFile]     = useState(null);
  const [docFiles, setDocFiles]       = useState([]);
  const [voiceResult, setVoiceResult] = useState(null);
  const [loadingV, setLoadingV]       = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState(c.description || '');
  const [listening, setListening]     = useState(false);
  const [savingDesc, setSavingDesc]   = useState(false);
  const [loadingD, setLoadingD]       = useState(false);
  const [err, setErr]                 = useState('');
  const recognitionRef = useRef(null);
  // Set while the textarea has focus: the save refreshes the case, and that
  // refresh must not overwrite what is currently being typed.
  const transcriptEditingRef = useRef(false);

  useEffect(() => {
    if (!transcriptEditingRef.current) setVoiceTranscript(c.description || '');
  }, [c.description]);

  const saveTranscript = useCallback(async (text, { silent = false } = {}) => {
    const cleaned = text.trim();
    if (!cleaned) return;
    setSavingDesc(true);
    try {
      await API.patch('/api/cases/' + c.id + '/description', { description: cleaned });
      // Silent: a background autosave shouldn't flip CaseDetail into its
      // loading state, which would tear this tab down mid-edit.
      onRefresh({ silent });
    } catch (e) {
      setErr(getApiError(e, 'Could not save transcript'));
    } finally {
      setSavingDesc(false);
    }
  }, [c.id, onRefresh]);

  const { debounced: autosaveTranscript, flush: flushTranscript } =
    useDebouncedCallback((text) => saveTranscript(text, { silent: true }), TRANSCRIPT_AUTOSAVE_MS);

  const toggleDictation = () => {
    setErr('');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setErr('Speech dictation is not supported in this browser');
      return;
    }
    if (listening && recognitionRef.current) {
      recognitionRef.current.stop();
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.interimResults = true;
    recognition.continuous = true;
    let finalText = '';
    recognition.onresult = (event) => {
      let interimText = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += transcript + ' ';
        else interimText += transcript;
      }
      setVoiceTranscript((finalText + interimText).trim());
    };
    recognition.onerror = (event) => {
      setErr(event.error || 'Could not access microphone');
      setListening(false);
    };
    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
      if (finalText.trim()) saveTranscript(finalText);
    };
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  };

  const uploadVoice = async () => {
    if (!voiceFile) return;
    setErr(''); setLoadingV(true);
    try {
      const fd = new FormData();
      fd.append('file', voiceFile);
      const r = await API.post('/api/cases/' + c.id + '/voice', fd);
      setVoiceResult(r.data);
      if (r.data?.description) setVoiceTranscript(r.data.description);
    } catch (e) {
      setErr(getApiError(e, 'Voice processing failed'));
    } finally {
      setLoadingV(false);
    }
  };

  const uploadDocs = async () => {
    if (!docFiles.length) return;
    setErr(''); setLoadingD(true);
    try {
      const fd = new FormData();
      docFiles.forEach(f => fd.append('files', f));
      await API.post('/api/cases/' + c.id + '/documents', fd);
      onRefresh();
      setDocFiles([]);
    } catch (e) {
      setErr(getApiError(e, 'Document upload failed'));
    } finally {
      setLoadingD(false);
    }
  };

  return (
    <div>
      {err && <Alert msg={err} type="error" />}

      {/* Module 1: Voice */}
      <div style={{
        background: 'var(--surface-container-lowest)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        padding: 20,
        marginBottom: 16,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: 18 }}>🎙️</span>
          <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--on-surface)' }}>
            Module 1 — Voice Dispute Intake
          </span>
          <Badge text="Module 1" color="var(--primary)" />
        </div>
        <p style={{
          fontSize: 12, color: 'var(--text-secondary)',
          margin: 0, marginBottom: 16, lineHeight: 1.6
        }}>
          Upload a voice note or record one from your microphone in any Indian language.
          Whisper ASR + NER will auto-fill the dispute form.
        </p>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
            {voiceFile ? '✓ ' + voiceFile.name : 'Choose Audio File'}
            <input type="file" accept="audio/*" className="visually-hidden"
              onChange={e => setVoiceFile(e.target.files[0])} />
          </label>
          <button
            type="button"
            className={listening ? 'btn btn-secondary' : 'btn btn-ghost'}
            aria-pressed={listening}
            style={listening ? { borderColor: 'var(--warning)', color: 'var(--warning)' } : undefined}
            onClick={toggleDictation}
          >
            {listening ? '⏹ Stop Dictation' : '🎙️ Dictate Description'}
          </button>
          <Button variant="primary" onClick={uploadVoice} loading={loadingV} disabled={!voiceFile}>
            {loadingV ? 'Processing…' : 'Process Voice'}
          </Button>
        </div>

        <div style={{ marginTop: 16 }}>
          <label style={css.label}>Description from Voice</label>
          <textarea
            style={{
              ...css.input,
              minHeight: 120,
              resize: 'vertical',
              fontFamily: "'Inter', sans-serif",
            }}
            value={voiceTranscript}
            placeholder="Speak into the mic and the description will appear here..."
            onChange={e => {
              setVoiceTranscript(e.target.value);
              autosaveTranscript(e.target.value);
            }}
            onFocus={() => { transcriptEditingRef.current = true; }}
            onBlur={() => {
              transcriptEditingRef.current = false;
              flushTranscript();
            }}
          />
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            marginTop: 8,
          }}>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              {savingDesc ? 'Saving transcript...' : 'Edit the transcript before saving.'}
            </div>
            <Button
              variant="ghost"
              size="sm"
              loading={savingDesc}
              onClick={() => saveTranscript(voiceTranscript)}
            >
              {savingDesc ? 'Saving…' : 'Save Description'}
            </Button>
          </div>
        </div>

        {voiceResult && (
          <div style={{ marginTop: 16 }}>
            <div style={{
              fontSize: 12, fontWeight: 600, color: '#10B981', marginBottom: 10,
            }}>
              ✓ Voice Processing Complete
            </div>
            <div className="grid-cols-2" style={{ display: 'grid', gap: 8 }}>
              {Object.entries(voiceResult).map(([k, v]) => (
                v && v !== '' && (
                  <div key={k} style={{
                    background: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 8,
                    padding: '10px 12px',
                    fontSize: 12,
                  }}>
                    <div style={{
                      color: 'var(--text-secondary)',
                      marginBottom: 2, fontWeight: 500,
                      textTransform: 'capitalize',
                    }}>
                      {k.replace(/_/g, ' ')}
                    </div>
                    <div style={{ fontWeight: 600, color: 'var(--on-surface)' }}>
                      {String(v)}
                    </div>
                  </div>
                )
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Module 2: Documents */}
      <div style={{
        background: 'var(--surface-container-lowest)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        padding: 20,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: 18 }}>📄</span>
          <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--on-surface)' }}>
            Module 2 — Document Intelligence
          </span>
          <Badge text="Module 2" color="#3B82F6" />
        </div>
        <p style={{
          fontSize: 12, color: 'var(--text-secondary)',
          margin: 0, marginBottom: 16, lineHeight: 1.6
        }}>
          Upload invoices, purchase orders, contracts. OCR + DistilBERT classifies
          and extracts key fields.
        </p>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
            {docFiles.length ? '✓ ' + docFiles.length + ' file(s) selected' : 'Choose Documents'}
            <input type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
              className="visually-hidden"
              onChange={e => setDocFiles(Array.from(e.target.files))} />
          </label>
          <Button variant="accent" onClick={uploadDocs} loading={loadingD} disabled={!docFiles.length}>
            {loadingD ? 'Uploading…' : 'Upload & Analyse'}
          </Button>
        </div>

        {docs.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div style={{
              fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)',
              marginBottom: 10, letterSpacing: '0.03em'
            }}>
              ANALYSED DOCUMENTS ({docs.length})
            </div>
            {docs.map(d => (
              <div key={d.id} style={{
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                padding: '12px 14px',
                marginBottom: 8,
              }}>
                <div style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--on-surface)' }}>
                      {d.filename}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <span style={{
                      padding: '2px 8px', borderRadius: 100, fontSize: 10,
                      fontWeight: 600, background: 'rgba(59,130,246,0.1)',
                      color: '#3B82F6', border: '1px solid rgba(59,130,246,0.25)',
                    }}>
                      {d.doc_type}
                    </span>
                    <span style={{
                      padding: '2px 8px', borderRadius: 100, fontSize: 10,
                      fontWeight: 600,
                      background: d.confidence > 0.7 ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)',
                      color: d.confidence > 0.7 ? '#10B981' : '#D97706',
                      border: '1px solid ' + (d.confidence > 0.7 ? '#10B981' : '#D97706') + '44',
                    }}>
                      {(d.confidence * 100).toFixed(0)}% conf
                    </span>
                    <span style={{
                      padding: '2px 8px', borderRadius: 100, fontSize: 10,
                      fontWeight: 600,
                      background: d.is_valid ? 'rgba(16,185,129,0.1)' : 'rgba(186,26,26,0.1)',
                      color: d.is_valid ? '#10B981' : '#BA1A1A',
                      border: '1px solid ' + (d.is_valid ? '#10B981' : '#BA1A1A') + '44',
                    }}>
                      {d.is_valid ? 'Valid' : 'Review'}
                    </span>
                  </div>
                </div>
                {d.issues?.length > 0 && (
                  <div style={{
                    color: '#D97706', fontSize: 11, marginTop: 6,
                    padding: '6px 8px', background: 'rgba(245,158,11,0.06)',
                    borderRadius: 4, border: '1px solid rgba(245,158,11,0.15)',
                  }}>
                    ⚠️ {d.issues.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
});

const CASE_TABS = [
  { key: 'overview',    label: 'Overview' },
  { key: 'docs',        label: 'Documents & Voice' },
  { key: 'prediction',  label: 'AI Prediction' },
  { key: 'negotiate',   label: 'Negotiate' },
  { key: 'settlement',  label: 'Settlement' },
];

/* ─── Main CaseDetail ── */
function CaseDetail({ caseData, onBack, onUpdate }) {
  const [c, setC]         = useState(caseData);
  const [docs, setDocs]   = useState([]);
  const [tab, setTab]     = useState('overview');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const onUpdateRef        = useRef(onUpdate);
  onUpdateRef.current = onUpdate;
  // Mirror of `c`, readable outside a setState updater.
  const cRef               = useRef(caseData);
  const loadedOnceRef      = useRef(false);

  // Tabs are mounted when first opened and then kept mounted, so tabbing away
  // and back no longer rebuilds the panel or throws away its state (chat
  // history, uploaded files, prediction result). Inactive panels stay in the
  // DOM but are hidden — for the negotiation room that also keeps its
  // WebSocket alive while the user looks at another tab.
  const [visitedTabs, setVisitedTabs] = useState(() => new Set([tab]));

  useEffect(() => {
    setVisitedTabs(prev => (prev.has(tab) ? prev : new Set(prev).add(tab)));
  }, [tab]);

  // The active tab is mounted in the same pass it is selected (no blank frame
  // before the effect above commits).
  const isTabMounted = (key) => key === tab || visitedTabs.has(key);

  // Inactive panels are display:none'd rather than unmounted. The fade-in is
  // re-added on each switch because the element itself never remounts, so a
  // changing `key` can no longer replay it.
  const panelStyle = (key) => ({
    display: tab === key ? 'block' : 'none',
    animation: tab === key ? 'fadeInUp 0.3s ease-out both' : 'none',
  });

  // When local c state changes, notify parent so AppShell's selectedCase stays in sync.
  // Computed outside the updater so the updater stays pure (React may call it twice
  // in StrictMode) and so the parent only re-renders once per change.
  const setCAndNotify = useCallback((patch) => {
    const prev = cRef.current;
    const next = typeof patch === 'function' ? patch(prev) : { ...prev, ...patch };
    cRef.current = next;
    setC(next);
    onUpdateRef.current(prev => ({ ...prev, ...next }));
  }, []);

  const refreshCase = useCallback(async ({ silent = false } = {}) => {
    // Only the very first load blocks the view — it has nothing to show yet.
    // Every later refresh updates the data in place: swapping the tab area for
    // a spinner would unmount all the mounted panels above and defeat the
    // whole point of keeping them alive.
    const blocking = !silent && !loadedOnceRef.current;
    if (blocking) setLoading(true);
    else if (!silent) setRefreshing(true);
    try {
      const [cr, dr] = await Promise.all([
        API.get('/api/cases/' + caseData.id),
        API.get('/api/cases/' + caseData.id + '/documents'),
      ]);
      cRef.current = cr.data;
      setC(cr.data);
      setDocs(dr.data);
      onUpdateRef.current(prev => ({ ...prev, ...cr.data }));
      loadedOnceRef.current = true;
    } catch { /* silent */ }
    finally {
      if (blocking) setLoading(false);
      if (!silent) setRefreshing(false);
    }
  }, [caseData.id]);

  useEffect(() => { refreshCase(); }, [refreshCase]);

  const handleTabSelect = useCallback((key) => setTab(key), []);
  const handleGoToNegotiate = useCallback(() => setTab('negotiate'), []);

  // Arrow keys move between tabs (WAI-ARIA tabs pattern). Home/End jump to the
  // first/last tab. Focus follows selection so the keyboard lands on the tab
  // that is now showing.
  const handleTabKeys = useCallback((e) => {
    const i = CASE_TABS.findIndex(t => t.key === tab);
    let next = null;
    if (e.key === 'ArrowRight') next = (i + 1) % CASE_TABS.length;
    else if (e.key === 'ArrowLeft') next = (i - 1 + CASE_TABS.length) % CASE_TABS.length;
    else if (e.key === 'Home') next = 0;
    else if (e.key === 'End') next = CASE_TABS.length - 1;
    if (next === null) return;
    e.preventDefault();
    const key = CASE_TABS[next].key;
    setTab(key);
    requestAnimationFrame(() => {
      const el = document.getElementById('case-tab-' + key);
      if (el) el.focus();
    });
  }, [tab]);

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease-out both' }}>
      {/* Back + Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16,
        marginBottom: 20, flexWrap: 'wrap',
      }}>
        <Button variant="ghost" onClick={onBack} className="no-print">
          ← Back to Dashboard
        </Button>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            flexWrap: 'wrap',
          }}>
            <div style={{
              fontSize: 18, fontWeight: 700, color: 'var(--on-surface)',
              fontFamily: "'Inter', sans-serif",
            }}>
              {DISPUTE_ICONS[c.dispute_type] || '📋'} {c.case_number}
            </div>
            <span style={{
              padding: '4px 10px', borderRadius: 100, fontSize: 11,
              fontWeight: 600,
              background: (STATUS_COLORS[c.status] || '#6F7979') + '18',
              color: STATUS_COLORS[c.status] || '#6F7979',
              border: '1px solid ' + (STATUS_COLORS[c.status] || '#6F7979') + '44',
            }}>
              {STATUS_LABELS[c.status] || c.status}
            </span>
          </div>
          <div style={{
            fontSize: 12, color: 'var(--text-secondary)',
            marginTop: 4,
          }}>
            Created {new Date(c.created_at).toLocaleDateString('en-IN', {
              dateStyle: 'medium'
            })}
            {' · '}
            {c.dispute_type?.replace(/_/g, ' ')}
            {' · '}
            {fmt(c.claim_amount)} claimed
          </div>
        </div>
        <Button variant="ghost" onClick={() => window.print()} className="no-print">
          🖨️ Print
        </Button>
      </div>

      {/* Tab bar */}
      <div
        role="tablist"
        aria-label="Case sections"
        onKeyDown={handleTabKeys}
        className="case-tabbar no-print"
        style={{
          display: 'flex', gap: 4, marginBottom: 20,
          background: 'var(--surface-container-low)',
          borderRadius: 8, padding: 4,
          border: '1px solid var(--border)',
          overflowX: 'auto',
        }}
      >
        {CASE_TABS.map(t => (
          <Tab
            key={t.key}
            id={'case-tab-' + t.key}
            panelId={'case-panel-' + t.key}
            active={tab === t.key}
            value={t.key}
            onSelect={handleTabSelect}
            label={t.label}
          />
        ))}
        {refreshing && (
          <span style={{
            marginLeft: 'auto', alignSelf: 'center', paddingRight: 8,
            fontSize: 11, color: 'var(--text-secondary)', whiteSpace: 'nowrap',
          }}>
            Refreshing…
          </span>
        )}
      </div>

      {/* Tab content */}
      {loading ? (
        /* First load only — later refreshes update in place (see refreshCase),
           so this skeleton never replaces panels that are already open. */
        <div aria-busy="true">
          <div className="grid-cols-3" style={{ display: 'grid', gap: 12, marginBottom: 20 }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="card" style={{ padding: '16px 18px' }}>
                <Skeleton width="45%" height={10} style={{ marginBottom: 10 }} />
                <Skeleton width="70%" height={19} />
              </div>
            ))}
          </div>
          <SkeletonCard lines={3} />
        </div>
      ) : (
        <>
          {isTabMounted('overview') && (
            <div
              role="tabpanel"
              id="case-panel-overview"
              aria-labelledby="case-tab-overview"
              style={panelStyle('overview')}
            >
              <OverviewTab c={c} docs={docs} onRefresh={refreshCase} />
            </div>
          )}
          {isTabMounted('docs') && (
            <div
              role="tabpanel"
              id="case-panel-docs"
              aria-labelledby="case-tab-docs"
              style={panelStyle('docs')}
            >
              <DocsVoiceTab c={c} docs={docs} onRefresh={refreshCase} />
            </div>
          )}
          {/* Each lazy panel gets its own Suspense boundary: a shared one would
              swap the already-visible tab out for a spinner while a newly
              opened tab's chunk downloads. */}
          {isTabMounted('prediction') && (
            <div
              role="tabpanel"
              id="case-panel-prediction"
              aria-labelledby="case-tab-prediction"
              style={panelStyle('prediction')}
            >
              <Suspense fallback={<PanelFallback />}>
                <PredictionPanel
                  caseData={c} onUpdate={setCAndNotify}
                  onNavigateToNegotiate={handleGoToNegotiate}
                />
              </Suspense>
            </div>
          )}
          {isTabMounted('negotiate') && (
            <div
              role="tabpanel"
              id="case-panel-negotiate"
              aria-labelledby="case-tab-negotiate"
              style={panelStyle('negotiate')}
            >
              <Suspense fallback={<PanelFallback />}>
                <NegotiationChat caseData={c} onUpdate={setCAndNotify} />
              </Suspense>
            </div>
          )}
          {isTabMounted('settlement') && (
            <div
              role="tabpanel"
              id="case-panel-settlement"
              aria-labelledby="case-tab-settlement"
              style={panelStyle('settlement')}
            >
              <Suspense fallback={<PanelFallback />}>
                <SettlementPanel caseData={c} onUpdate={setCAndNotify} />
              </Suspense>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// CaseDetail only draws the active tab, but it still re-renders whenever AppShell
// re-renders (view changes, refreshKey bumps). Memo keeps those out.
export default React.memo(CaseDetail);

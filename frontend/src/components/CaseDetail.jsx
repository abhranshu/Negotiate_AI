import React, { useState, useEffect, useCallback, useRef } from 'react';
import API from '../api';
import { css, fmt } from '../theme';
import { Badge, Spinner, Alert, EmptyState, Tab } from './UI';
import PredictionPanel from './PredictionPanel';
import NegotiationChat from './NegotiationChat';
import SettlementPanel from './SettlementPanel';

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

function InfoCard({ icon, label, value, color }) {
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
}

/* ─── Overview Tab ── */
function OverviewTab({ c, docs, onRefresh }) {
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
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
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
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
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
}

/* ─── Documents & Voice Tab ── */
function DocsVoiceTab({ c, docs, onRefresh }) {
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

  useEffect(() => { setVoiceTranscript(c.description || ''); }, [c.description]);

  const saveTranscript = useCallback(async (text) => {
    const cleaned = text.trim();
    if (!cleaned) return;
    setSavingDesc(true);
    try {
      await API.patch('/api/cases/' + c.id + '/description', { description: cleaned });
      onRefresh();
    } catch (e) {
      setErr(e.response?.data?.detail || 'Could not save transcript');
    } finally {
      setSavingDesc(false);
    }
  }, [c.id, onRefresh]);

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
      setErr(e.response?.data?.detail || 'Voice processing failed');
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
      setErr(e.response?.data?.detail || 'Document upload failed');
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
          <label style={{
            ...css.btnGhost,
            color: 'var(--text-secondary)',
            borderColor: 'var(--border)',
          }}>
            {voiceFile ? '✓ ' + voiceFile.name : 'Choose Audio File'}
            <input type="file" accept="audio/*" style={{ display: 'none' }}
              onChange={e => setVoiceFile(e.target.files[0])} />
          </label>
          <button
            style={{
              ...css.btnGhost,
              background: listening ? 'rgba(245,158,11,0.1)' : 'var(--surface)',
              color: listening ? '#D97706' : 'var(--text-secondary)',
              borderColor: listening ? '#D97706' : 'var(--border)',
            }}
            onClick={toggleDictation}
          >
            {listening ? '⏹ Stop Dictation' : '🎙️ Dictate Description'}
          </button>
          <button
            style={{
              ...css.btn,
              background: 'var(--primary)',
              color: 'var(--on-primary)',
              boxShadow: '0 2px 8px rgba(0,102,102,0.25)',
            }}
            onClick={uploadVoice}
            disabled={!voiceFile || loadingV}
          >
            {loadingV && <Spinner />}
            {loadingV ? 'Processing...' : 'Process Voice'}
          </button>
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
            onChange={e => setVoiceTranscript(e.target.value)}
            onBlur={() => saveTranscript(voiceTranscript)}
          />
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            marginTop: 8,
          }}>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              {savingDesc ? 'Saving transcript...' : 'Edit the transcript before saving.'}
            </div>
            <button
              style={{
                ...css.btnGhost,
                background: 'var(--surface)',
                color: 'var(--primary)',
                borderColor: 'var(--primary)',
                fontSize: 12,
                padding: '8px 14px',
              }}
              onClick={() => saveTranscript(voiceTranscript)}
              disabled={savingDesc}
            >
              {savingDesc ? 'Saving...' : 'Save Description'}
            </button>
          </div>
        </div>

        {voiceResult && (
          <div style={{ marginTop: 16 }}>
            <div style={{
              fontSize: 12, fontWeight: 600, color: '#10B981', marginBottom: 10,
            }}>
              ✓ Voice Processing Complete
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: 8,
            }}>
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
          <label style={{
            ...css.btnGhost,
            color: 'var(--text-secondary)',
            borderColor: 'var(--border)',
          }}>
            {docFiles.length ? '✓ ' + docFiles.length + ' file(s) selected' : 'Choose Documents'}
            <input type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
              style={{ display: 'none' }}
              onChange={e => setDocFiles(Array.from(e.target.files))} />
          </label>
          <button
            style={{
              ...css.btn,
              background: '#3B82F6',
              color: '#fff',
              boxShadow: '0 2px 8px rgba(59,130,246,0.25)',
            }}
            onClick={uploadDocs}
            disabled={!docFiles.length || loadingD}
          >
            {loadingD && <Spinner />}
            {loadingD ? 'Uploading...' : 'Upload & Analyse'}
          </button>
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
}

/* ─── Main CaseDetail ── */
export default function CaseDetail({ caseData, onBack, onUpdate }) {
  const [c, setC]         = useState(caseData);
  const [docs, setDocs]   = useState([]);
  const [tab, setTab]     = useState('overview');
  const [loading, setLoading] = useState(false);
  const onUpdateRef        = useRef(onUpdate);
  onUpdateRef.current = onUpdate;

  // When local c state changes, notify parent so AppShell's selectedCase stays in sync.
  const setCAndNotify = useCallback((patch) => {
    setC(prev => {
      const next = typeof patch === 'function' ? patch(prev) : { ...prev, ...patch };
      onUpdateRef.current(prev => ({ ...prev, ...next }));
      return next;
    });
  }, []);

  const refreshCase = useCallback(async () => {
    setLoading(true);
    try {
      const [cr, dr] = await Promise.all([
        API.get('/api/cases/' + c.id),
        API.get('/api/cases/' + c.id + '/documents'),
      ]);
      setC(cr.data);
      setDocs(dr.data);
      onUpdateRef.current(prev => ({ ...prev, ...cr.data }));
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [c.id]);

  useEffect(() => { refreshCase(); }, [refreshCase]);

  const TABS = [
    { key: 'overview',    label: 'Overview' },
    { key: 'docs',        label: 'Documents & Voice' },
    { key: 'prediction',  label: 'AI Prediction' },
    { key: 'negotiate',   label: 'Negotiate' },
    { key: 'settlement',  label: 'Settlement' },
  ];

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease-out both' }}>
      {/* Back + Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16,
        marginBottom: 20, flexWrap: 'wrap',
      }}>
        <button
          style={{
            ...css.btnGhost,
            color: 'var(--text-secondary)',
            borderColor: 'var(--border)',
          }}
          onClick={onBack}
        >
          ← Back to Dashboard
        </button>
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
        <button
          style={{
            ...css.btnGhost,
            color: 'var(--text-secondary)',
            borderColor: 'var(--border)',
          }}
          onClick={() => window.print()}
        >
          🖨️ Print
        </button>
      </div>

      {/* Tab bar */}
      <div style={{
        display: 'flex', gap: 4, marginBottom: 20,
        background: 'var(--surface)',
        borderRadius: 8, padding: 4,
        border: '1px solid var(--border)',
        overflowX: 'auto',
      }}>
        {TABS.map(t => (
          <Tab
            key={t.key}
            active={tab === t.key}
            onClick={() => setTab(t.key)}
            label={t.label}
          />
        ))}
      </div>

      {/* Tab content */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{
            width: 24, height: 24, margin: '0 auto 12px',
            border: '3px solid var(--border)',
            borderTopColor: 'var(--primary)',
            borderRadius: '50%',
            animation: 'spin 0.7s linear infinite',
          }} />
          <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
            Loading...
          </div>
        </div>
      ) : (
        <div key={tab} style={{ animation: 'fadeInUp 0.3s ease-out both' }}>
          {tab === 'overview'   && <OverviewTab c={c} docs={docs} onRefresh={refreshCase} />}
          {tab === 'docs'       && <DocsVoiceTab c={c} docs={docs} onRefresh={refreshCase} />}
          {tab === 'prediction' && (
            <PredictionPanel
              caseData={c} onUpdate={setCAndNotify}
              onNavigateToNegotiate={() => setTab('negotiate')}
            />
          )}
          {tab === 'negotiate'  && <NegotiationChat caseData={c} onUpdate={setCAndNotify} />}
          {tab === 'settlement' && <SettlementPanel caseData={c} onUpdate={setCAndNotify} />}
        </div>
      )}
    </div>
  );
}

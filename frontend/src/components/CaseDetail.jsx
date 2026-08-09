import React, { useState, useEffect, useCallback, useRef } from 'react';
import API from '../api';
import { T, css, fmt, pct, confColor } from '../theme';
import { Badge, Spinner, Stat, ProgressBar, Alert, EmptyState, Tab } from './UI';
import PredictionPanel from './PredictionPanel';
import NegotiationChat from './NegotiationChat';
import SettlementPanel from './SettlementPanel';

const STATUS_COLORS = {
  draft: '#64748b', submitted: '#3b82f6', in_progress: '#f59e0b',
  agreement: '#10b981', closed: '#06b6d4', escalated: '#ef4444',
};
const DISPUTE_ICONS = {
  delayed_payment: '⏰', non_payment: '🚫', short_payment: '📉',
  quality_dispute: '🔍', quantity_dispute: '📦', contract_breach: '📋',
};

function InfoCard({ icon, label, value, sub, color }) {
  return (
    <div style={{ background: T.bg, borderRadius: 10, padding: '14px 16px', border: '1px solid ' + T.border }}>
      <div style={{ fontSize: 12, color: T.muted, marginBottom: 4 }}>{icon} {label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: color || T.text }}>{value || '—'}</div>
      {sub && <div style={{ fontSize: 11, color: T.muted, marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

// ─── Tab 1: Overview ─────────────────────────────────────────────────────────
function OverviewTab({ c, docs, onRefresh }) {
  const stats = [
    { icon: '💰', label: 'Claim Amount',  value: fmt(c.claim_amount),         color: T.accent2 },
    { icon: '⏱️', label: 'Overdue Days',  value: c.overdue_days ? c.overdue_days + ' days' : '—', color: T.yellow },
    { icon: '📄', label: 'Documents',    value: docs.length + ' uploaded',    color: T.accent },
    { icon: '🏛️', label: 'State',         value: c.state,                     color: T.purple },
    { icon: '🏭', label: 'Industry',      value: c.industry?.replace(/_/g, ' '), color: T.accent2 },
    { icon: '⚖️', label: 'Dispute Type',  value: c.dispute_type?.replace(/_/g, ' '), color: T.yellow },
  ];

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginBottom: 20 }}>
        {stats.map(s => <InfoCard key={s.label} {...s} />)}
      </div>

      {c.description && (
        <div style={{ ...css.card, marginBottom: 16 }}>
          <div style={{ fontSize: 12, color: T.muted, marginBottom: 6 }}>📝 DESCRIPTION</div>
          <p style={{ fontSize: 13, margin: 0, lineHeight: 1.7 }}>{c.description}</p>
        </div>
      )}

      {/* Module Pipeline Status */}
      <div style={css.card}>
        <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 14 }}>🔬 ML Pipeline Status</div>
        {[
          { icon: '🎙️', label: 'Voice Processing',   done: false },
          { icon: '📄', label: 'Document Analysis',   done: docs.length > 0 },
          { icon: '📊', label: 'Outcome Prediction',  done: !!c.settlement_probability },
          { icon: '🤝', label: 'Negotiation',         done: !!c.agreement_amount },
          { icon: '📜', label: 'Settlement',          done: !!c.agreement_text },
        ].map((step, i) => (
          <div key={step.label} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%',
              background: step.done ? T.green + '22' : T.border,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: '1px solid ' + (step.done ? T.green : T.border),
              flexShrink: 0 }}>
              {step.done ? '✓' : step.icon}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: step.done ? T.green : T.muted }}>{step.label}</div>
              <div style={{ fontSize: 11, color: T.muted }}>{step.done ? 'Complete' : 'Pending'}</div>
            </div>
            {step.done && <Badge text="Done" color={T.green} />}
            {!step.done && <Badge text="Pending" color={T.muted} />}
          </div>
        ))}
      </div>

      {/* Quick Results if prediction done */}
      {c.settlement_probability && (
        <div style={{ ...css.card, background: `linear-gradient(135deg, ${T.accent}11, ${T.accent2}11)`,
          border: '1px solid ' + T.accent + '33' }}>
          <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12 }}>⚡ Quick Prediction Summary</div>
          <div style={css.grid3}>
            <Stat label='Settlement Probability' value={pct(c.settlement_probability)} color={confColor[c.prediction_confidence] || T.accent} />
            <Stat label='Settlement Range Low'  value={fmt(c.settlement_range_low)}  color={T.accent2} />
            <Stat label='Settlement Range High' value={fmt(c.settlement_range_high)} color={T.accent2} />
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Tab 2: Documents & Voice ─────────────────────────────────────────────────
function DocsVoiceTab({ c, docs, onRefresh }) {
  const [voiceFile, setVoiceFile]   = useState(null);
  const [docFiles, setDocFiles]     = useState([]);
  const [voiceResult, setVoiceResult] = useState(null);
  const [loadingV, setLoadingV]     = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState(c.description || '');
  const [listening, setListening]   = useState(false);
  const [savingDesc, setSavingDesc] = useState(false);
  const [loadingD, setLoadingD]     = useState(false);
  const [err, setErr]               = useState('');
  const recognitionRef = useRef(null);

  useEffect(() => {
    setVoiceTranscript(c.description || '');
  }, [c.description]);

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
      const fd = new FormData(); fd.append('file', voiceFile);
      const r = await API.post('/api/cases/' + c.id + '/voice', fd);
      setVoiceResult(r.data);
      if (r.data?.description) setVoiceTranscript(r.data.description);
    } catch (e) { setErr(e.response?.data?.detail || 'Voice processing failed'); }
    finally { setLoadingV(false); }
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
    } catch (e) { setErr(e.response?.data?.detail || 'Document upload failed'); }
    finally { setLoadingD(false); }
  };

  return (
    <div>
      {err && <Alert msg={err} type='error' />}

      {/* Module 1: Voice */}
      <div style={css.card}>
        <div style={css.title}>🎙️ Module 1 — Voice Dispute Intake</div>
        <p style={{ fontSize: 12, color: T.muted, marginBottom: 14 }}>
          Upload a voice note or record one from your microphone in any Indian language. Whisper ASR + NER will auto-fill the dispute form.
        </p>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <label style={{ ...css.btn, background: T.border, color: T.text, cursor: 'pointer', fontSize: 12 }}>
            {voiceFile ? '✓ ' + voiceFile.name : '🎧 Choose Audio File'}
            <input type='file' accept='audio/*' style={{ display: 'none' }}
              onChange={e => setVoiceFile(e.target.files[0])} />
          </label>
          <button
            style={{ ...css.btn, background: listening ? T.yellow : T.border, color: listening ? '#111' : T.text, fontSize: 12 }}
            onClick={toggleDictation}
          >
            {listening ? '⏹ Stop Dictation' : '🎙️ Dictate Description'}
          </button>
          <button style={{ ...css.btn, background: `linear-gradient(135deg,${T.accent},${T.accent2})`, color: '#fff' }}
            onClick={uploadVoice} disabled={!voiceFile || loadingV}>
            {loadingV && <Spinner />}🚀 Process Voice
          </button>
        </div>

        <div style={{ marginTop: 14 }}>
          <label style={css.label}>Description from Voice</label>
          <textarea
            style={{ ...css.input, minHeight: 110, resize: 'vertical', fontFamily: 'inherit' }}
            value={voiceTranscript}
            placeholder="Speak into the mic and the description will appear here..."
            onChange={e => setVoiceTranscript(e.target.value)}
            onBlur={() => saveTranscript(voiceTranscript)}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
            <div style={{ fontSize: 11, color: T.muted }}>
              {savingDesc ? 'Saving transcript...' : 'You can edit the transcript before saving.'}
            </div>
            <button
              style={{ ...css.btn, background: T.surface, border: '1px solid ' + T.border, color: T.accent, fontSize: 12, padding: '8px 12px' }}
              onClick={() => saveTranscript(voiceTranscript)}
              disabled={savingDesc}
            >
              Save Description
            </button>
          </div>
        </div>

        {voiceResult && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: T.green, marginBottom: 10 }}>✓ Voice Processing Complete</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {Object.entries(voiceResult).map(([k, v]) => (
                v && v !== '' && (
                  <div key={k} style={{ background: T.bg, borderRadius: 8, padding: '10px 12px',
                    border: '1px solid ' + T.border, fontSize: 12 }}>
                    <div style={{ color: T.muted, marginBottom: 2 }}>{k.replace(/_/g, ' ')}</div>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{String(v)}</div>
                  </div>
                )
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Module 2: Documents */}
      <div style={css.card}>
        <div style={css.title}>📄 Module 2 — Document Intelligence</div>
        <p style={{ fontSize: 12, color: T.muted, marginBottom: 14 }}>
          Upload invoices, POs, contracts. OCR + DistilBERT classifies and extracts key fields.
        </p>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <label style={{ ...css.btn, background: T.border, color: T.text, cursor: 'pointer', fontSize: 12 }}>
            {docFiles.length ? '✓ ' + docFiles.length + ' file(s) selected' : '📎 Choose Documents'}
            <input type='file' multiple accept='.pdf,.png,.jpg,.jpeg,.doc,.docx'
              style={{ display: 'none' }} onChange={e => setDocFiles(Array.from(e.target.files))} />
          </label>
          <button style={{ ...css.btn, background: `linear-gradient(135deg,${T.purple},${T.accent})`, color: '#fff' }}
            onClick={uploadDocs} disabled={!docFiles.length || loadingD}>
            {loadingD && <Spinner />}🚀 Upload & Analyse
          </button>
        </div>

        {docs.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 10, color: T.muted }}>
              ANALYSED DOCUMENTS ({docs.length})
            </div>
            {docs.map(d => (
              <div key={d.id} style={{ background: T.bg, borderRadius: 8, padding: '12px 14px',
                border: '1px solid ' + T.border, marginBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{d.filename}</div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <Badge text={d.doc_type} color={T.accent2} />
                    <Badge text={(d.confidence * 100).toFixed(0) + '% conf'}
                      color={d.confidence > 0.7 ? T.green : T.yellow} />
                    <Badge text={d.is_valid ? 'Valid' : 'Review'} color={d.is_valid ? T.green : T.red} />
                  </div>
                </div>
                {d.issues?.length > 0 && (
                  <div style={{ color: T.yellow, fontSize: 11, marginTop: 6 }}>⚠️ {d.issues.join(', ')}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main CaseDetail ──────────────────────────────────────────────────────────
export default function CaseDetail({ caseData, onBack, onUpdate }) {
  const [c, setC]         = useState(caseData);
  const [docs, setDocs]   = useState([]);
  const [tab, setTab]     = useState('overview');
  const [loading, setLoading] = useState(false);

  const refreshCase = useCallback(async () => {
    setLoading(true);
    try {
      const [cr, dr] = await Promise.all([
        API.get('/api/cases/' + c.id),
        API.get('/api/cases/' + c.id + '/documents'),
      ]);
      setC(cr.data);
      setDocs(dr.data);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [c.id]);

  useEffect(() => { refreshCase(); }, [refreshCase]);

  const TABS = [
    { key: 'overview',    label: '📊 Overview' },
    { key: 'docs',        label: `📄 Documents (${docs.length})` },
    { key: 'prediction',  label: '📈 AI Prediction' },
    { key: 'negotiate',   label: '🤝 Negotiate' },
    { key: 'settlement',  label: '📜 Settlement' },
  ];

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 16px' }}>
      {/* Back + Case Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
        <button style={{ ...css.btn, background: T.surface, color: T.muted, padding: '8px 14px' }} onClick={onBack}>
          ← Back
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ fontSize: 20, fontWeight: 700 }}>
              {DISPUTE_ICONS[c.dispute_type] || '📋'} {c.case_number}
            </div>
            <Badge text={c.status?.replace(/_/g, ' ')} color={STATUS_COLORS[c.status] || T.muted} />
          </div>
          <div style={{ fontSize: 12, color: T.muted, marginTop: 2 }}>
            Created {new Date(c.created_at).toLocaleDateString('en-IN', { dateStyle: 'medium' })}
            &nbsp;·&nbsp;{c.dispute_type?.replace(/_/g, ' ')}
            &nbsp;·&nbsp;{fmt(c.claim_amount)} claimed
          </div>
        </div>
        <button
          style={{ ...css.btn, background: T.surface, border: '1px solid ' + T.border, color: T.accent, fontSize: 12, padding: '8px 14px' }}
          onClick={() => window.print()}
        >
          🖨️ Print
        </button>
      </div>

      {/* Tab Bar */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: T.surface,
        borderRadius: 10, padding: 4, border: '1px solid ' + T.border }}>
        {TABS.map(t => <Tab key={t.key} active={tab === t.key} onClick={() => setTab(t.key)} label={t.label} />)}
      </div>

      {/* Tab Content */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}><Spinner /> Loading...</div>
      ) : (
        <>
          {tab === 'overview'   && <OverviewTab c={c} docs={docs} onRefresh={refreshCase} />}
          {tab === 'docs'       && <DocsVoiceTab c={c} docs={docs} onRefresh={refreshCase} />}
          {tab === 'prediction' && <PredictionPanel caseData={c} onUpdate={setC} onNavigateToNegotiate={() => setTab('negotiate')} />}
          {tab === 'negotiate'  && <NegotiationChat caseData={c} onUpdate={setC} />}
          {tab === 'settlement' && <SettlementPanel caseData={c} onUpdate={setC} />}
        </>
      )}
    </div>
  );
}
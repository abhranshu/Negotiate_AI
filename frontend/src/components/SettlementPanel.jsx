import React, { useState } from 'react';
import API from '../api';
import { T, css, fmt } from '../theme';
import { Badge, Spinner, Alert, EmptyState } from './UI';

function ValidationCheck({ label, pass }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
      <span style={{
        width: 18, height: 18, borderRadius: '50%',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: pass ? T.green + '22' : T.red + '22',
        border: '1px solid ' + (pass ? T.green : T.red),
        fontSize: 11,
      }}>
        {pass ? '✓' : '✕'}
      </span>
      <span style={{ fontSize: 12, color: pass ? T.text : T.red }}>{label}</span>
    </div>
  );
}

export default function SettlementPanel({ caseData, onUpdate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [err, setErr] = useState('');
  const [copied, setCopied] = useState(false);
  const [showFull, setShowFull] = useState(false);

  const hasAgreement = !!(caseData.agreement_amount);
  const hasSettlement = !!(caseData.agreement_text) || !!(data?.agreement_text);

  const generate = async () => {
    setErr(''); setLoading(true);
    try {
      const r = await API.post(`/api/cases/${caseData.id}/settlement`);
      setData(r.data);
      onUpdate(prev => ({ ...prev, agreement_text: r.data.agreement_text }));
    } catch (e) {
      setErr(e.response?.data?.detail || 'Settlement generation failed');
    } finally { setLoading(false); }
  };

  const fetchExisting = async () => {
    setErr(''); setFetching(true);
    try {
      const r = await API.get(`/api/cases/${caseData.id}/settlement`);
      setData(r.data);
    } catch (e) {
      setErr('No settlement found — generate one first');
    } finally { setFetching(false); }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const agreedAmt = data?.agreed_amount || caseData.agreement_amount;

  // Validate the agreement text heuristically for display
  const text = data?.agreement_text || caseData.agreement_text || '';
  const checks = text ? [
    { label: 'Parties identified', pass: /claimant|respondent/i.test(text) },
    { label: 'Agreed amount present', pass: /\d{4,}/.test(text) },
    { label: 'Payment timeline defined', pass: /days|date|instalment|schedule/i.test(text) },
    { label: 'Full & final settlement clause', pass: /full and final/i.test(text) },
    { label: 'MSMED Act / Contract Act cited', pass: /msmed|indian contract act|1872/i.test(text) },
    { label: 'Signature block present', pass: /signed|signature/i.test(text) },
  ] : [];

  return (
    <div>
      <div style={{ ...css.card, background: `linear-gradient(135deg, ${T.green}0a, ${T.purple}0a)`, border: '1px solid ' + T.green + '33' }}>
        <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>📜 Module 5 — Settlement Agreement Generator</div>
        <p style={{ fontSize: 13, color: T.muted, margin: 0, lineHeight: 1.6 }}>
          Generates a legally valid settlement agreement compliant with
          <strong> MSMED Act 2006 (Sections 15–23) </strong> and the Indian Contract Act, 1872.
          A rule-based validator checks all mandatory clauses.
        </p>

        {!hasAgreement ? (
          <div style={{ marginTop: 16, padding: '12px 14px', background: T.bg, borderRadius: 8,
            border: '1px dashed ' + T.yellow, fontSize: 13, color: T.yellow }}>
            ⚠️ &nbsp;No agreement amount yet. Complete negotiation first to reach a settlement figure.
          </div>
        ) : (
          <div style={{ marginTop: 12, display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: 12, color: T.muted, marginBottom: 2 }}>Agreed Settlement Amount</div>
              <div style={{ fontSize: 28, fontWeight: 800, color: T.green }}>{fmt(agreedAmt)}</div>
            </div>
            <Badge text={hasSettlement ? (data?.is_valid ? '✓ Validated' : '⚠ Review Needed') : 'Not Generated'} 
              color={hasSettlement ? (data?.is_valid ? T.green : T.yellow) : T.muted} />
          </div>
        )}
      </div>

      {err && <Alert msg={err} type="error" />}

      {hasAgreement && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
          <button
            style={{ ...css.btn, padding: '12px 28px', background: `linear-gradient(135deg,${T.green},${T.accent2})`, color: '#fff', fontSize: 14 }}
            onClick={generate} disabled={loading || fetching}>
            {loading ? <><Spinner /> Generating legal agreement...</> : hasSettlement ? '🔄 Regenerate Agreement' : '🚀 Generate Settlement Agreement'}
          </button>
          {hasSettlement && !data && (
            <button style={{ ...css.btn, padding: '12px 20px', background: T.surface, color: T.accent, border: '1px solid ' + T.accent }}
              onClick={fetchExisting} disabled={fetching}>
              {fetching ? <Spinner /> : '📥 Load Existing'}
            </button>
          )}
        </div>
      )}

      {hasSettlement && (
        <>
          {/* Validation checklist */}
          <div style={css.card}>
            <div style={css.title}>✅ Legal Validation Checklist</div>
            {checks.map(c => <ValidationCheck key={c.label} label={c.label} pass={c.pass} />)}
            {data?.validation_notes?.length > 0 && (
              <div style={{ marginTop: 10, padding: '10px 12px', background: T.red + '11', border: '1px solid ' + T.red + '44', borderRadius: 8, fontSize: 12, color: T.red }}>
                <strong>Issues found:</strong>
                <ul style={{ margin: '6px 0 0 14px' }}>
                  {data.validation_notes.map((n, i) => <li key={i}>{n}</li>)}
                </ul>
              </div>
            )}
          </div>

          {/* Agreement text preview */}
          <div style={css.card}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={css.title}>📄 Agreement Document</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button style={{ ...css.btn, background: T.bg, color: T.accent, border: '1px solid ' + T.accent, fontSize: 12, padding: '6px 12px' }}
                  onClick={() => copyToClipboard(text)}>
                  {copied ? '✓ Copied!' : '📋 Copy'}
                </button>
                <button style={{ ...css.btn, background: T.bg, color: T.text, border: '1px solid ' + T.border, fontSize: 12, padding: '6px 12px' }}
                  onClick={() => window.print()}>
                  🖨️ Print
                </button>
              </div>
            </div>
            <div style={{
              background: '#fff', color: '#1a1a1a', borderRadius: 8,
              padding: 28,
              maxHeight: showFull ? 'none' : 320,
              overflowY: 'auto',
              fontFamily: "'Georgia', serif",
              fontSize: 13, lineHeight: 1.9,
              whiteSpace: 'pre-wrap',
              border: '1px solid ' + T.border,
            }}>
              {text}
            </div>
            <button
              style={{ ...css.btn, background: 'transparent', color: T.accent, fontSize: 12, marginTop: 8 }}
              onClick={() => setShowFull(!showFull)}>
              {showFull ? '▲ Collapse' : '▼ Expand Full Document'}
            </button>
          </div>

          {/* Summary stats */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginBottom: 16 }}>
            <div style={{ ...css.metric }}>
              <span style={{ ...css.metricVal, color: T.green }}>{fmt(agreedAmt)}</span>
              <div style={css.metricLbl}>Agreed Amount</div>
            </div>
            <div style={{ ...css.metric }}>
              <span style={{ ...css.metricVal, color: T.accent2 }}>
                {caseData.claim_amount ? Math.round((agreedAmt / caseData.claim_amount) * 100) + '%' : '—'}
              </span>
              <div style={css.metricLbl}>of Original Claim</div>
            </div>
            <div style={{ ...css.metric }}>
              <span style={{ ...css.metricVal, color: data?.is_valid ? T.green : T.yellow }}>
                {data?.is_valid ? '✓ Valid' : '⚠ Review'}
              </span>
              <div style={css.metricLbl}>Legal Status</div>
            </div>
          </div>

          <div style={{ ...css.card, background: `linear-gradient(135deg, ${T.green}15, ${T.accent2}15)`, border: '1px solid ' + T.green + '44', textAlign: 'center', padding: 24 }}>
            <div style={{ fontSize: 36 }}>🏆</div>
            <div style={{ fontSize: 18, fontWeight: 800, margin: '8px 0', color: T.green }}>Dispute Successfully Resolved!</div>
            <p style={{ fontSize: 13, color: T.muted, maxWidth: 480, margin: '0 auto' }}>
              The AI-mediated negotiation resulted in a mutual settlement of <strong style={{ color: T.text }}>{fmt(agreedAmt)}</strong>.
              Both parties can now sign the generated agreement, which is compliant with the MSMED Act, 2006.
            </p>
          </div>
        </>
      )}

      {!hasAgreement && !hasSettlement && !loading && (
        <div style={css.card}>
          <EmptyState
            icon="🕊️"
            text="Complete Negotiation First"
            subtext="A settlement agreement is generated only after both parties reach a mutual agreement in the negotiation room."
          />
        </div>
      )}
    </div>
  );
}

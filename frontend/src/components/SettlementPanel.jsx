import React, { useState, useMemo } from 'react';
import API, { getApiError } from '../api';
import { css, fmt } from '../theme';
import { Badge, Alert, EmptyState, Button } from './UI';

const ValidationCheck = React.memo(function ValidationCheck({ label, pass }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      marginBottom: 6,
    }}>
      <span style={{
        width: 18, height: 18,
        borderRadius: '50%',
        display: 'flex', alignItems: 'center',
        justifyContent: 'center',
        background: pass ? 'rgba(16,185,129,0.1)' : 'rgba(186,26,26,0.1)',
        border: '1px solid ' + (pass ? '#10B981' : '#BA1A1A'),
        fontSize: 10, fontWeight: 700,
        color: pass ? '#10B981' : '#BA1A1A',
        flexShrink: 0,
      }}>
        {pass ? '✓' : '✕'}
      </span>
      <span style={{
        fontSize: 12,
        color: pass ? 'var(--on-surface)' : '#BA1A1A',
      }}>
        {label}
      </span>
    </div>
  );
});

export default function SettlementPanel({ caseData, onUpdate }) {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [err, setErr]       = useState('');
  const [copied, setCopied] = useState(false);
  const [showFull, setShowFull] = useState(false);

  const hasAgreement  = !!(caseData.agreement_amount);
  const hasSettlement = !!(caseData.agreement_text) || !!(data?.agreement_text);

  const generate = async () => {
    setErr(''); setLoading(true);
    try {
      const r = await API.post(`/api/cases/${caseData.id}/settlement`);
      setData(r.data);
      onUpdate(prev => ({ ...prev, agreement_text: r.data.agreement_text }));
    } catch (e) {
      setErr(getApiError(e, 'Settlement generation failed'));
    } finally {
      setLoading(false);
    }
  };

  const fetchExisting = async () => {
    setErr(''); setFetching(true);
    try {
      const r = await API.get(`/api/cases/${caseData.id}/settlement`);
      setData(r.data);
    } catch (e) {
      setErr('No settlement found — generate one first');
    } finally {
      setFetching(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const agreedAmt = data?.agreed_amount || caseData.agreement_amount;
  const text      = data?.agreement_text || caseData.agreement_text || '';

  const checks = useMemo(() => text ? [
    { label: 'Parties identified',           pass: /claimant|respondent/i.test(text) },
    { label: 'Agreed amount present',       pass: /\d{4,}/.test(text) },
    { label: 'Payment timeline defined',    pass: /days|date|instalment|schedule/i.test(text) },
    { label: 'Full & final settlement',     pass: /full and final/i.test(text) },
    { label: 'MSMED Act / Contract Act cited', pass: /msmed|indian contract act|1872/i.test(text) },
    { label: 'Signature block present',     pass: /signed|signature/i.test(text) },
  ] : [], [text]);

  return (
    <div>
      {/* Header card */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(16,185,129,0.06), rgba(59,130,246,0.06))',
        border: '1px solid rgba(16,185,129,0.2)',
        borderRadius: 8,
        padding: 20,
        marginBottom: 16,
      }}>
        <div style={{
          fontSize: 15, fontWeight: 700,
          marginBottom: 6, color: 'var(--on-surface)',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span>📜</span>
          Module 5 — Settlement Agreement Generator
        </div>
        <p style={{
          fontSize: 12, color: 'var(--text-secondary)',
          margin: 0, lineHeight: 1.6,
        }}>
          Generates a legally valid settlement agreement compliant with{' '}
          <strong>MSMED Act 2006 (Sections 15–23)</strong> and the Indian Contract Act, 1872.
          A rule-based validator checks all mandatory clauses.
        </p>

        {!hasAgreement ? (
          <div style={{
            marginTop: 14, padding: '10px 14px',
            background: 'rgba(245,158,11,0.06)',
            border: '1px dashed rgba(245,158,11,0.3)',
            borderRadius: 6,
            fontSize: 12, color: '#D97706',
          }}>
            ⚠️ No agreement amount yet. Complete negotiation first to reach a settlement figure.
          </div>
        ) : (
          <div style={{
            marginTop: 12, display: 'flex', gap: 20,
            alignItems: 'center', flexWrap: 'wrap',
          }}>
            <div>
              <div style={{
                fontSize: 11, color: 'var(--text-secondary)',
                marginBottom: 2, fontWeight: 500,
              }}>
                Agreed Settlement Amount
              </div>
              <div style={{
                fontSize: 28, fontWeight: 800,
                color: '#10B981',
                fontFamily: "'Inter', sans-serif",
              }}>
                {fmt(agreedAmt)}
              </div>
            </div>
            <Badge
              text={hasSettlement
                ? (data?.is_valid ? 'Validated' : 'Review Needed')
                : 'Not Generated'}
              color={hasSettlement
                ? (data?.is_valid ? '#10B981' : '#D97706')
                : 'var(--text-secondary)'}
            />
          </div>
        )}
      </div>

      {err && <Alert msg={err} type="error" />}

      {hasAgreement && (
        <div style={{
          display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap',
        }}>
          <Button
            variant="success"
            loading={loading}
            disabled={fetching}
            onClick={generate}
          >
            {loading
              ? 'Generating legal agreement…'
              : hasSettlement
                ? 'Regenerate Agreement'
                : 'Generate Settlement Agreement'}
          </Button>
          {hasSettlement && !data && (
            <Button variant="ghost" loading={fetching} onClick={fetchExisting}>
              Load Existing
            </Button>
          )}
        </div>
      )}

      {hasSettlement && (
        <>
          {/* Validation checklist */}
          <div style={{
            background: 'var(--surface-container-lowest)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: 20,
            marginBottom: 16,
          }}>
            <div style={{
              fontSize: 13, fontWeight: 700, marginBottom: 12,
              color: 'var(--on-surface)',
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <span>✅</span>
              Legal Validation Checklist
            </div>
            {checks.map(c => (
              <ValidationCheck key={c.label} label={c.label} pass={c.pass} />
            ))}
            {data?.validation_notes?.length > 0 && (
              <div style={{
                marginTop: 10, padding: '10px 12px',
                background: 'rgba(186,26,26,0.06)',
                border: '1px solid rgba(186,26,26,0.2)',
                borderRadius: 6,
                fontSize: 12, color: '#BA1A1A',
              }}>
                <strong style={{ display: 'block', marginBottom: 4 }}>
                  Issues found:
                </strong>
                <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                  {data.validation_notes.map((n, i) => (
                    <li key={i} style={{ fontSize: 12 }}>{n}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Agreement text preview */}
          <div style={{
            background: 'var(--surface-container-lowest)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: 20,
            marginBottom: 16,
          }}>
            <div style={{
              display: 'flex', justifyContent: 'space-between',
              alignItems: 'center', marginBottom: 12,
            }}>
              <div style={{
                fontSize: 13, fontWeight: 700,
                color: 'var(--on-surface)',
                display: 'flex', alignItems: 'center', gap: 8,
              }}>
                <span>📄</span>
                Agreement Document
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <Button variant="ghost" size="sm" onClick={() => copyToClipboard(text)}>
                  {copied ? '✓ Copied!' : 'Copy'}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => window.print()}>
                  🖨️ Print
                </Button>
              </div>
            </div>
            <div style={{
              background: '#fff',
              color: '#1a1a1a',
              borderRadius: 6,
              padding: 24,
              maxHeight: showFull ? 'none' : 320,
              overflowY: 'auto',
              fontFamily: "'Georgia', serif",
              fontSize: 12,
              lineHeight: 1.8,
              whiteSpace: 'pre-wrap',
              border: '1px solid var(--border)',
            }}>
              {text}
            </div>
            <Button
              variant="plain"
              onClick={() => setShowFull(!showFull)}
              aria-expanded={showFull}
              style={{ marginTop: 8 }}
            >
              {showFull ? '▲ Collapse' : '▼ Expand Full Document'}
            </Button>
          </div>

          {/* Summary stats */}
          <div className="grid-cols-3" style={{ display: 'grid', gap: 12, marginBottom: 16 }}>
            {[
              { label: 'Agreed Amount',  value: fmt(agreedAmt),   color: '#10B981' },
              { label: 'of Original Claim', value: caseData.claim_amount
                  ? Math.round((agreedAmt / caseData.claim_amount) * 100) + '%'
                  : '—', color: '#06B6D4' },
              { label: 'Legal Status',   value: data?.is_valid ? '✓ Valid' : '⚠ Review',
                color: data?.is_valid ? '#10B981' : '#D97706' },
            ].map(s => (
              <div key={s.label} style={{
                textAlign: 'center',
                padding: '16px 8px',
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 8,
              }}>
                <div style={{
                  fontSize: 22, fontWeight: 800,
                  color: s.color,
                  fontFamily: "'Inter', sans-serif",
                }}>
                  {s.value}
                </div>
                <div style={{
                  fontSize: 11, color: 'var(--text-secondary)',
                  marginTop: 4, fontWeight: 500,
                }}>
                  {s.label}
                </div>
              </div>
            ))}
          </div>

          {/* Success banner */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(16,185,129,0.08), rgba(6,182,212,0.08))',
            border: '1px solid rgba(16,185,129,0.3)',
            borderRadius: 8,
            textAlign: 'center',
            padding: 28,
            animation: 'scaleIn 0.4s ease-out both',
          }}>
            <div style={{ fontSize: 36, marginBottom: 8 }}>🏆</div>
            <div style={{
              fontSize: 18, fontWeight: 800,
              margin: '8px 0', color: '#10B981',
            }}>
              Dispute Successfully Resolved!
            </div>
            <p style={{
              fontSize: 13, color: 'var(--text-secondary)',
              maxWidth: 480, margin: '0 auto',
              lineHeight: 1.7,
            }}>
              The AI-mediated negotiation resulted in a mutual settlement of{' '}
              <strong style={{ color: 'var(--on-surface)' }}>
                {fmt(agreedAmt)}
              </strong>
              . Both parties can now sign the generated agreement, which is compliant
              with the MSMED Act, 2006.
            </p>
          </div>
        </>
      )}

      {/* Empty state */}
      {!hasAgreement && !hasSettlement && !loading && (
        <div style={{
          background: 'var(--surface-container-lowest)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          padding: 48,
          textAlign: 'center',
        }}>
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

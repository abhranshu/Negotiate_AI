import React, { useState } from 'react';
import API, { getApiError } from '../api';
import { css, fmt, pct, confColor } from '../theme';
import { Badge, Spinner, Alert, EmptyState } from './UI';

const FACTOR_INSIGHTS = {
  claim_amount_inr:       { icon: '💰', desc: 'Higher claim amounts tend to lower settlement odds' },
  overdue_days:           { icon: '⏱️', desc: 'Longer delays reduce settlement probability' },
  documentation_score:    { icon: '📄', desc: 'Better docs = higher settlement chance' },
  has_signed_contract:    { icon: '✍️', desc: 'A signed contract significantly strengthens your case' },
  has_delivery_proof:     { icon: '📦', desc: 'Delivery proof is strong evidence in your favour' },
  previous_payments_made: { icon: '💳', desc: 'Partial payment history signals buyer intent' },
  invoice_count:          { icon: '🧾', desc: 'Multiple invoices consolidate your claim' },
  prior_disputes:         { icon: '🔁', desc: 'Past disputes between parties affect trust level' },
  msefc_filing:           { icon: '🏛️', desc: 'Formal MSEFC filing signals seriousness' },
  claimant_size:          { icon: '🏢', desc: 'Enterprise size of claimant' },
  respondent_size:        { icon: '🏭', desc: 'Larger respondents usually settle faster' },
  dispute_type:           { icon: '⚖️', desc: 'Certain dispute types resolve quicker than others' },
  industry:               { icon: '🏗️', desc: 'Industry norms affect settlement behavior' },
  state:                  { icon: '📍', desc: 'State-level MSEFC efficiency varies' },
  days_since_dispute:     { icon: '📅', desc: 'Fresh disputes have better settlement odds' },
  amount_log:             { icon: '📊', desc: 'Log-scaled claim amount' },
  overdue_ratio:          { icon: '📈', desc: 'Overdue period relative to standard 30-day terms' },
  doc_amount_interaction: { icon: '🔗', desc: 'Combined effect of docs and claim size' },
};

function FactorBar({ factor }) {
  const maxAbs = 0.5;
  const w     = Math.min(Math.abs(factor.impact) / maxAbs * 100, 100);
  const color = factor.direction === 'positive' ? '#10B981' : '#BA1A1A';
  const insight = FACTOR_INSIGHTS[factor.factor];

  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', marginBottom: 4,
      }}>
        <div style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13 }}>{insight?.icon || '📌'}</span>
          <span style={{ fontWeight: 600, color: 'var(--on-surface)' }}>
            {factor.factor.replace(/_/g, ' ')}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{
            fontSize: 11, color, fontWeight: 700,
          }}>
            {factor.direction === 'positive' ? '▲' : '▼'}{' '}
            {Math.abs(factor.impact).toFixed(4)}
          </span>
        </div>
      </div>
      <div style={{
        height: 6, background: 'var(--border)',
        borderRadius: 3, overflow: 'hidden',
      }}>
        <div style={{
          height: '100%',
          width: w + '%',
          background: color,
          borderRadius: 3,
          transition: 'width 0.6s ease',
        }} />
      </div>
      {insight && (
        <div style={{
          fontSize: 10, color: 'var(--text-secondary)',
          marginTop: 3,
        }}>
          {insight.desc}
        </div>
      )}
    </div>
  );
}

function SettlementGauge({ prob }) {
  const pctVal = Math.round((prob || 0) * 100);
  const color  = pctVal >= 65 ? '#10B981' : pctVal >= 40 ? '#F59E0B' : '#BA1A1A';
  const angle  = (pctVal / 100) * 360;

  return (
    <div style={{
      textAlign: 'center', padding: '4px 0',
    }}>
      <div style={{
        width: 130, height: 130,
        borderRadius: '50%',
        background: `conic-gradient(${color} 0deg ${angle}deg, var(--border) ${angle}deg 360deg)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        position: 'relative',
        margin: '0 auto',
      }}>
        <div style={{
          width: 96, height: 96, borderRadius: '50%',
          background: 'var(--surface-container-lowest)',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          border: '1px solid var(--border)',
        }}>
          <span style={{
            fontSize: 28, fontWeight: 800, color,
            fontFamily: "'Inter', sans-serif",
          }}>
            {pctVal}%
          </span>
          <span style={{
            fontSize: 10, color: 'var(--text-secondary)',
            marginTop: 2,
          }}>
            settlement odds
          </span>
        </div>
      </div>
      <div style={{
        marginTop: 10, display: 'flex', gap: 14,
        justifyContent: 'center', fontSize: 11,
      }}>
        {[['High', '#10B981'], ['Medium', '#F59E0B'], ['Low', '#BA1A1A']].map(([l, c]) => (
          <span key={l} style={{ color: c, fontWeight: 500 }}>
            ● {l}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function PredictionPanel({ caseData, onUpdate, onNavigateToNegotiate }) {
  const [result, setResult]     = useState(null);
  const [loading, setLoading]   = useState(false);
  const [err, setErr]           = useState('');
  const [hasRun, setHasRun]     = useState(false);

  const hasPrediction = !!(caseData?.settlement_probability);

  const runPrediction = async () => {
    setErr(''); setLoading(true);
    try {
      const r = await API.post('/api/cases/' + caseData.id + '/predict');
      setResult(r.data);
      setHasRun(true);
      onUpdate(prev => ({ ...prev, ...r.data }));
    } catch (e) {
      setErr(getApiError(e, 'Prediction failed. Check backend logs.'));
    } finally {
      setLoading(false);
    }
  };

  const probability = result?.settlement_probability ?? caseData?.settlement_probability;
  const rangeLow    = result?.settlement_range_low   ?? caseData?.settlement_range_low;
  const rangeHigh   = result?.settlement_range_high  ?? caseData?.settlement_range_high;
  const adjDays     = result?.adjudication_days      ?? caseData?.adjudication_days;
  const confBand    = result?.confidence_band        ?? caseData?.prediction_confidence;
  const factors     = result?.key_factors            ?? [];
  const recommend   = result?.recommendation         ?? caseData?.prediction_recommendation;

  return (
    <div>
      {/* Header card */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(59,130,246,0.05), rgba(0,102,102,0.05))',
        border: '1px solid rgba(59,130,246,0.2)',
        borderRadius: 8,
        padding: 20,
        marginBottom: 16,
      }}>
        <div style={{
          display: 'flex', alignItems: 'flex-start',
          justifyContent: 'space-between', gap: 12,
        }}>
          <div>
            <div style={{
              fontSize: 15, fontWeight: 700,
              marginBottom: 6, color: 'var(--on-surface)',
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <span>📈</span>
              Module 3 — Outcome Prediction Engine
            </div>
            <p style={{
              fontSize: 12, color: 'var(--text-secondary)',
              margin: 0, lineHeight: 1.6,
            }}>
              XGBoost & LightGBM ensemble trained on MSME Samadhan case data.
              Predicts settlement probability, expected amount range, and adjudication
              timeline. SHAP explainability shows which factors drive the prediction.
            </p>
          </div>
          {confBand && (
            <Badge
              text={'Confidence: ' + confBand}
              color={confColor[confBand] || 'var(--text-secondary)'}
            />
          )}
        </div>

        {!hasPrediction && !hasRun && (
          <div style={{
            marginTop: 14, padding: '10px 14px',
            background: 'var(--surface)',
            border: '1px dashed var(--border)',
            borderRadius: 6,
            fontSize: 12, color: 'var(--text-secondary)',
          }}>
            No prediction run yet for this case. Click below to invoke the ML engine.
          </div>
        )}

        <button
          style={{
            ...css.btn,
            marginTop: 14,
            padding: '10px 24px',
            fontSize: 13,
            background: '#3B82F6',
            color: '#fff',
            boxShadow: '0 2px 8px rgba(59,130,246,0.25)',
          }}
          onClick={runPrediction}
          disabled={loading}
        >
          {loading
            ? <><Spinner /> Training model if needed & running prediction...</>
            : hasPrediction ? 'Re-run Prediction' : 'Run ML Prediction'}
        </button>
        {loading && (
          <div style={{
            fontSize: 11, color: 'var(--text-secondary)',
            marginTop: 6,
          }}>
            First run trains XGBoost on synthetic data — may take 30–60 seconds
          </div>
        )}
      </div>

      {err && <Alert msg={err} type="error" />}

      {/* Results */}
      {(hasPrediction || hasRun) && probability != null && (
        <>
          {/* Main metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div style={{
              background: 'var(--surface-container-lowest)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: 20,
            }}>
              <div style={{
                fontSize: 13, fontWeight: 700, marginBottom: 14,
                color: 'var(--on-surface)',
              }}>
                Settlement Probability
              </div>
              <SettlementGauge prob={probability} />
              <div style={{
                height: 6, background: 'var(--border)',
                borderRadius: 3, overflow: 'hidden',
                marginTop: 12,
              }}>
                <div style={{
                  height: '100%',
                  width: (probability * 100) + '%',
                  background: probability >= 0.65 ? '#10B981'
                    : probability >= 0.4 ? '#F59E0B' : '#BA1A1A',
                  borderRadius: 3,
                  transition: 'width 0.8s ease',
                }} />
              </div>
            </div>

            <div style={{
              background: 'var(--surface-container-lowest)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: 20,
            }}>
              <div style={{
                fontSize: 13, fontWeight: 700, marginBottom: 14,
                color: 'var(--on-surface)',
              }}>
                Prediction Summary
              </div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 10,
              }}>
                {[
                  { label: 'Range Low',       value: fmt(rangeLow),    color: '#10B981' },
                  { label: 'Range High',      value: fmt(rangeHigh),   color: '#06B6D4' },
                  { label: 'Adjudication Days', value: adjDays ? '~' + adjDays + ' days' : '—', color: '#F59E0B' },
                  { label: 'ZOPA Midpoint',   value: rangeLow != null && rangeHigh != null
                    ? fmt((rangeLow + rangeHigh) / 2) : '—', color: '#3C454C' },
                ].map(item => (
                  <div key={item.label} style={{
                    textAlign: 'center',
                    padding: '12px 8px',
                    background: 'var(--surface)',
                    borderRadius: 6,
                    border: '1px solid var(--border)',
                  }}>
                    <div style={{
                      fontSize: 10, color: 'var(--text-secondary)',
                      marginBottom: 2, fontWeight: 500,
                    }}>
                      {item.label}
                    </div>
                    <div style={{
                      fontSize: 18, fontWeight: 800,
                      color: item.color,
                      fontFamily: "'Inter', sans-serif",
                    }}>
                      {item.value}
                    </div>
                  </div>
                ))}
              </div>

              {/* Range visualization */}
              <div style={{ marginTop: 14 }}>
                <div style={{
                  fontSize: 11, color: 'var(--text-secondary)',
                  marginBottom: 6, fontWeight: 500,
                }}>
                  Settlement Range Visualization
                </div>
                <div style={{
                  background: 'var(--surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 6,
                  padding: '12px',
                }}>
                  <div style={{
                    position: 'relative', height: 8,
                    background: 'var(--border)',
                    borderRadius: 4,
                  }}>
                    <div style={{
                      position: 'absolute',
                      left: '10%', right: '10%',
                      top: 0, bottom: 0,
                      background: 'linear-gradient(90deg, #10B981, #06B6D4)',
                      borderRadius: 4,
                      opacity: 0.5,
                    }} />
                    <div style={{
                      position: 'absolute',
                      left: '48%', top: -3, bottom: -3,
                      width: 3,
                      background: 'var(--on-surface)',
                      borderRadius: 2,
                    }} />
                  </div>
                  <div style={{
                    display: 'flex', justifyContent: 'space-between',
                    marginTop: 6, fontSize: 10,
                  }}>
                    <span style={{ color: '#10B981' }}>
                      ₹{(rangeLow / 100000).toFixed(1)}L
                    </span>
                    <span style={{ color: 'var(--on-surface)', fontWeight: 600 }}>
                      ₹{((rangeLow + rangeHigh) / 2 / 100000).toFixed(1)}L
                    </span>
                    <span style={{ color: '#06B6D4' }}>
                      ₹{(rangeHigh / 100000).toFixed(1)}L
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* SHAP factors */}
          {factors.length > 0 && (
            <div style={{
              background: 'var(--surface-container-lowest)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: 20,
              marginTop: 16,
            }}>
              <div style={{
                fontSize: 13, fontWeight: 700, marginBottom: 4,
                color: 'var(--on-surface)',
                display: 'flex', alignItems: 'center', gap: 8,
              }}>
                <span>🔍</span>
                SHAP Explanation
              </div>
              <div style={{
                fontSize: 11, color: 'var(--text-secondary)',
                marginBottom: 14, padding: '8px 12px',
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 6,
              }}>
                <span style={{ color: '#10B981' }}>▲ Green = pushes toward settlement</span>
                {'   '}
                <span style={{ color: '#BA1A1A' }}>▼ Red = reduces settlement probability</span>
              </div>
              {factors.map((f, i) => (
                <FactorBar key={f.factor + i} factor={f} />
              ))}
            </div>
          )}

          {/* Recommendation */}
          {recommend && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(16,185,129,0.06), rgba(6,182,212,0.06))',
              border: '1px solid rgba(16,185,129,0.25)',
              borderRadius: 8,
              padding: 20,
              marginBottom: 16,
            }}>
              <div style={{
                fontSize: 12, fontWeight: 700, marginBottom: 8,
                color: '#10B981',
              }}>
                💡 AI Recommendation
              </div>
              <p style={{
                fontSize: 14, margin: 0, lineHeight: 1.7,
                color: 'var(--on-surface-variant)',
              }}>
                {recommend}
              </p>
            </div>
          )}

          {/* CTA */}
          <div style={{
            background: 'var(--surface-container-lowest)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: 16,
            display: 'flex', alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12, flexWrap: 'wrap',
          }}>
            <div>
              <div style={{
                fontWeight: 600, marginBottom: 2,
                color: 'var(--on-surface)',
                fontSize: 13,
              }}>
                Ready to negotiate?
              </div>
              <div style={{
                fontSize: 12, color: 'var(--text-secondary)',
              }}>
                Use these predictions to enter the AI-mediated negotiation room
              </div>
            </div>
            <button
              style={{
                ...css.btn,
                background: '#3B82F6',
                color: '#fff',
                padding: '10px 20px',
                boxShadow: '0 2px 8px rgba(59,130,246,0.25)',
              }}
              onClick={onNavigateToNegotiate}
            >
              Go to Negotiation →
            </button>
          </div>
        </>
      )}

      {/* No prediction yet */}
      {!hasPrediction && !hasRun && !loading && (
        <div style={{
          background: 'var(--surface-container-lowest)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          padding: 48,
          textAlign: 'center',
        }}>
          <div style={{
            width: 64, height: 64, margin: '0 auto 16px',
            borderRadius: 16,
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            display: 'flex', alignItems: 'center',
            justifyContent: 'center',
            fontSize: 28,
          }}>
            📊
          </div>
          <div style={{
            fontWeight: 700, marginBottom: 4,
            color: 'var(--on-surface)',
            fontSize: 15,
          }}>
            No Prediction Yet
          </div>
          <div style={{
            fontSize: 13, color: 'var(--text-secondary)',
            maxWidth: 400, margin: '0 auto', lineHeight: 1.6,
          }}>
            Run the ML prediction engine to see settlement probability,
            amount range, and SHAP explanations
          </div>
        </div>
      )}
    </div>
  );
}

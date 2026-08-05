import React, { useState } from 'react';
import API from '../api';
import { T, css, fmt, pct, confColor } from '../theme';
import { Badge, Spinner, Stat, ProgressBar, Alert, EmptyState } from './UI';

const FACTOR_INSIGHTS = {
  claim_amount_inr:        { icon: '💰', desc: 'Higher claim amounts tend to lower settlement odds' },
  overdue_days:            { icon: '⏱️', desc: 'Longer delays reduce settlement probability' },
  documentation_score:     { icon: '📄', desc: 'Better docs = higher settlement chance' },
  has_signed_contract:     { icon: '✍️', desc: 'A signed contract significantly strengthens your case' },
  has_delivery_proof:      { icon: '📦', desc: 'Delivery proof is strong evidence in your favour' },
  previous_payments_made:  { icon: '💳', desc: 'Partial payment history signals buyer intent' },
  invoice_count:           { icon: '🧾', desc: 'Multiple invoices consolidate your claim' },
  prior_disputes:          { icon: '🔁', desc: 'Past disputes between parties affect trust level' },
  msefc_filing:            { icon: '🏛️', desc: 'Formal MSEFC filing signals seriousness' },
  claimant_size:           { icon: '🏢', desc: 'Enterprise size of claimant' },
  respondent_size:         { icon: '🏭', desc: 'Larger respondents usually settle faster' },
  dispute_type:            { icon: '⚖️', desc: 'Certain dispute types resolve quicker than others' },
  industry:                { icon: '🏗️', desc: 'Industry norms affect settlement behavior' },
  state:                   { icon: '📍', desc: 'State-level MSEFC efficiency varies' },
  days_since_dispute:      { icon: '📅', desc: 'Fresh disputes have better settlement odds' },
  amount_log:              { icon: '📊', desc: 'Log-scaled claim amount' },
  overdue_ratio:           { icon: '📈', desc: 'Overdue period relative to standard 30-day terms' },
  doc_amount_interaction:  { icon: '🔗', desc: 'Combined effect of docs and claim size' },
};

function FactorBar({ factor }) {
  const maxAbs = 0.5;
  const w = Math.min(Math.abs(factor.impact) / maxAbs * 100, 100);
  const color = factor.direction === 'positive' ? T.green : T.red;
  const insight = FACTOR_INSIGHTS[factor.factor];

  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <div style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
          <span>{insight?.icon || '📌'}</span>
          <span style={{ fontWeight: 600 }}>{factor.factor.replace(/_/g, ' ')}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 11, color, fontWeight: 700 }}>
            {factor.direction === 'positive' ? '▲' : '▼'} {Math.abs(factor.impact).toFixed(4)}
          </span>
        </div>
      </div>
      <div style={{ height: 5, background: T.border, borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: w + '%', background: color,
          borderRadius: 3, transition: 'width 0.6s ease' }} />
      </div>
      {insight && <div style={{ fontSize: 10, color: T.muted, marginTop: 3 }}>{insight.desc}</div>}
    </div>
  );
}

function SettlementGauge({ prob }) {
  const pctVal = Math.round((prob || 0) * 100);
  const color = pctVal >= 65 ? T.green : pctVal >= 40 ? T.yellow : T.red;
  const angle = (pctVal / 100) * 360;

  return (
    <div style={{ textAlign: 'center', padding: '8px 0' }}>
      <div style={{
        width: 140, height: 140, borderRadius: '50%', margin: '0 auto',
        background: `conic-gradient(${color} 0deg ${angle}deg, ${T.border} ${angle}deg 360deg)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        position: 'relative',
      }}>
        <div style={{
          width: 104, height: 104, borderRadius: '50%', background: T.card,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontSize: 30, fontWeight: 800, color }}>{pctVal}%</span>
          <span style={{ fontSize: 11, color: T.muted }}>settlement odds</span>
        </div>
      </div>
      <div style={{ marginTop: 10, display: 'flex', gap: 12, justifyContent: 'center', fontSize: 11 }}>
        {[['High', T.green], ['Medium', T.yellow], ['Low', T.red]].map(([l, c]) => (
          <span key={l} style={{ color: c }}>● {l}</span>
        ))}
      </div>
    </div>
  );
}

export default function PredictionPanel({ caseData, onUpdate, onNavigateToNegotiate }) {
  const [result, setResult]       = useState(null);
  const [loading, setLoading]     = useState(false);
  const [err, setErr]             = useState('');
  const [hasRun, setHasRun]       = useState(false);

  const hasPrediction = !!(caseData?.settlement_probability);

  const runPrediction = async () => {
    setErr(''); setLoading(true);
    try {
      const r = await API.post('/api/cases/' + caseData.id + '/predict');
      setResult(r.data);
      setHasRun(true);
      onUpdate(prev => ({ ...prev, ...r.data }));
    } catch (e) {
      setErr(e.response?.data?.detail || 'Prediction failed. Check backend logs.');
    } finally { setLoading(false); }
  };

  // Show either fresh result or persisted prediction from case
  const probability = result?.settlement_probability ?? caseData?.settlement_probability;
  const rangeLow    = result?.settlement_range_low   ?? caseData?.settlement_range_low;
  const rangeHigh   = result?.settlement_range_high  ?? caseData?.settlement_range_high;
  const adjDays     = result?.adjudication_days      ?? caseData?.adjudication_days;
  const confBand    = result?.confidence_band        ?? caseData?.prediction_confidence;
  const factors     = result?.key_factors            ?? [];
  const recommend   = result?.recommendation         ?? caseData?.prediction_recommendation;

  return (
    <div>
      {/* Header Card */}
      <div style={{ ...css.card, background: `linear-gradient(135deg, ${T.purple}11, ${T.accent}11)`,
        border: '1px solid ' + T.purple + '33' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>📈 Module 3 — Outcome Prediction Engine</div>
            <p style={{ fontSize: 13, color: T.muted, margin: 0, lineHeight: 1.6 }}>
              XGBoost & LightGBM ensemble trained on MSME Samadhan case data.
              Predicts settlement probability, expected amount range, and adjudication timeline.
              SHAP explainability shows which factors drive the prediction.
            </p>
          </div>
          {confBand && <Badge text={'Confidence: ' + confBand} color={confColor[confBand] || T.muted} />}
        </div>

        {!hasPrediction && !hasRun && (
          <div style={{ marginTop: 16, padding: '12px 14px', background: T.bg, borderRadius: 8,
            border: '1px dashed ' + T.border, fontSize: 12, color: T.muted }}>
            ⚠️ &nbsp;No prediction run yet for this case. Click below to invoke the ML engine.
          </div>
        )}

        <button style={{ ...css.btn, marginTop: 14, padding: '12px 28px', fontSize: 14,
          background: `linear-gradient(135deg,${T.purple},${T.accent})`, color: '#fff' }}
          onClick={runPrediction} disabled={loading}>
          {loading
            ? <><Spinner /> Training model if needed & running prediction...</>
            : hasPrediction ? '🔄 Re-run Prediction' : '🚀 Run ML Prediction'}
        </button>
        {loading && (
          <div style={{ fontSize: 11, color: T.muted, marginTop: 8 }}>
            ⏳ First run trains XGBoost on synthetic data — may take 30–60 seconds
          </div>
        )}
      </div>

      {err && <Alert msg={err} type='error' />}

      {/* Results */}
      {(hasPrediction || hasRun) && probability !== null && probability !== undefined && (
        <>
          {/* Main Metrics */}
          <div style={css.grid2}>
            <div style={css.card}>
              <div style={css.title}>🎯 Settlement Probability</div>
              <SettlementGauge prob={probability} />
              <ProgressBar
                pct={probability * 100}
                color={probability >= 0.65 ? T.green : probability >= 0.4 ? T.yellow : T.red} />
            </div>

            <div style={css.card}>
              <div style={css.title}>📊 Prediction Summary</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <Stat label='Range Low'         value={fmt(rangeLow)}   color={T.green} />
                <Stat label='Range High'        value={fmt(rangeHigh)}  color={T.accent2} />
                <Stat label='Adjudication Days' value={adjDays ? '~' + adjDays + ' days' : '—'} color={T.yellow} />
                <Stat label='ZOPA Midpoint'     value={rangeLow != null && rangeHigh != null ? fmt((rangeLow + rangeHigh) / 2) : '—'} color={T.purple} />
              </div>

              {/* Visual range bar */}
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 11, color: T.muted, marginBottom: 6 }}>Settlement Range Visualization</div>
                <div style={{ background: T.bg, borderRadius: 6, padding: '12px', border: '1px solid ' + T.border }}>
                  <div style={{ position: 'relative', height: 8, background: T.border, borderRadius: 4 }}>
                    <div style={{
                      position: 'absolute', left: '10%', right: '10%', top: 0, bottom: 0,
                      background: `linear-gradient(90deg, ${T.green}, ${T.accent2})`,
                      borderRadius: 4, opacity: 0.6,
                    }} />
                    <div style={{
                      position: 'absolute', left: '48%', top: -3, bottom: -3, width: 4,
                      background: T.text, borderRadius: 2,
                    }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 10 }}>
                    <span style={{ color: T.green }}>₹{(rangeLow / 100000).toFixed(1)}L</span>
                    <span style={{ color: T.text, fontWeight: 600 }}>₹{((rangeLow + rangeHigh) / 2 / 100000).toFixed(1)}L</span>
                    <span style={{ color: T.accent2 }}>₹{(rangeHigh / 100000).toFixed(1)}L</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* SHAP Factors */}
          {factors.length > 0 && (
            <div style={css.card}>
              <div style={css.title}>
                🔍 SHAP Explanation
                <span style={{ fontSize: 11, fontWeight: 400, color: T.muted }}>
                  — Top factors influencing this prediction
                </span>
              </div>
              <div style={{ fontSize: 11, color: T.muted, marginBottom: 16, padding: '8px 12px',
                background: T.bg, borderRadius: 6, border: '1px solid ' + T.border }}>
                <span style={{ color: T.green }}>▲ Green = pushes toward settlement</span>
                &nbsp;&nbsp;
                <span style={{ color: T.red }}>▼ Red = reduces settlement probability</span>
              </div>
              {factors.map((f, i) => <FactorBar key={f.factor + i} factor={f} />)}
            </div>
          )}

          {/* Recommendation */}
          {recommend && (
            <div style={{ ...css.card, background: `linear-gradient(135deg, ${T.green}0a, ${T.accent2}0a)`,
              border: '1px solid ' + T.green + '33' }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: T.green }}>
                💡 AI Recommendation
              </div>
              <p style={{ fontSize: 14, margin: 0, lineHeight: 1.8 }}>{recommend}</p>
            </div>
          )}

          {/* Next step CTA */}
          <div style={{ ...css.card, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontWeight: 600, marginBottom: 2 }}>Ready to negotiate?</div>
              <div style={{ fontSize: 12, color: T.muted }}>
                Use these predictions to enter the AI-mediated negotiation room
              </div>
            </div>
            <button style={{ ...css.btn, background: `linear-gradient(135deg,${T.accent2},${T.accent})`,
              color: '#fff', padding: '10px 20px' }}
              onClick={onNavigateToNegotiate}>
              🤝 Go to Negotiation →
            </button>
          </div>
        </>
      )}

      {/* No prediction yet */}
      {!hasPrediction && !hasRun && !loading && (
        <div style={css.card}>
          <EmptyState
            icon="📊"
            text="No Prediction Yet"
            subtext="Run the ML prediction engine to see settlement probability, amount range, and SHAP explanations"
          />
        </div>
      )}
    </div>
  );
}
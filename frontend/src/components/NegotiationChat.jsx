import React, { useState, useEffect, useRef, useCallback } from 'react';
import API from '../api';
import { T, css, fmt, sentiColor } from '../theme';
import { Badge, Spinner, Alert, EmptyState, ProgressBar } from './UI';

const PHASES = ['opening', 'anchoring', 'bargaining', 'closing', 'agreement'];
const PHASE_COLORS = { opening: T.accent, anchoring: T.accent2, bargaining: T.yellow, closing: T.purple, agreement: T.green, deadlock: T.red };

function SentimentIcon({ s }) {
  const map = { cooperative: '😊', conciliatory: '🤝', neutral: '😐', frustrated: '😤', hostile: '😠' };
  return <span title={s}>{map[s] || '💬'}</span>;
}

function PhaseTracker({ current }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, margin: '12px 0' }}>
      {PHASES.map((p, i) => {
        const active = p === current;
        const done = PHASES.indexOf(current) > i;
        return (
          <React.Fragment key={p}>
            <div style={{
              flex: 1, textAlign: 'center', padding: '6px 2px', borderRadius: 6,
              background: active ? PHASE_COLORS[p] + '33' : done ? T.green + '22' : T.bg,
              border: '1px solid ' + (active ? PHASE_COLORS[p] : done ? T.green : T.border),
              fontSize: 10, fontWeight: active ? 700 : 500,
              color: active ? PHASE_COLORS[p] : done ? T.green : T.muted,
            }}>
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </div>
            {i < PHASES.length - 1 && <span style={{ color: T.border, fontSize: 10, padding: '0 2px' }}>›</span>}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function ChatBubble({ m, myParty }) {
  const isMe = m.party === myParty;
  const isMediator = m.party === 'mediator';
  const color = isMediator ? T.purple : isMe ? T.accent : T.border;
  return (
    <div style={{
      display: 'flex',
      justifyContent: isMediator ? 'center' : isMe ? 'flex-end' : 'flex-start',
      marginBottom: 12,
    }}>
      <div style={{
        maxWidth: isMediator ? '92%' : '75%',
        background: isMediator ? T.purple + '18' : isMe ? T.accent + '22' : T.surface,
        border: '1px solid ' + color + '44',
        borderRadius: isMe ? '14px 14px 4px 14px' : isMediator ? 14 : '14px 14px 14px 4px',
        padding: '10px 14px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span style={{ fontSize: 13 }}>{isMediator ? '🤖' : isMe ? '🙋' : '🏢'}</span>
          <span style={{ fontSize: 11, fontWeight: 700, color: color }}>
            {isMediator ? 'AI Mediator' : isMe ? 'You (' + m.party + ')' : m.party}
          </span>
          {m.sentiment && (
            <span style={{ fontSize: 11, color: sentiColor[m.sentiment] || T.muted }}>
              <SentimentIcon s={m.sentiment} /> {m.sentiment}
            </span>
          )}
        </div>
        <div style={{ fontSize: 13, lineHeight: 1.6 }}>{m.text}</div>
        {m.offer && (
          <div style={{
            marginTop: 8, padding: '6px 10px', borderRadius: 8,
            background: T.green + '18', border: '1px solid ' + T.green + '44',
            fontSize: 13, fontWeight: 700, color: T.green,
          }}>
            💵 Offer: {fmt(m.offer)}
          </div>
        )}
      </div>
    </div>
  );
}

function DealMeter({ claim, cOffer, rOffer }) {
  if (!claim) return null;
  const toPct = v => Math.min(100, Math.max(0, (v / claim) * 100));
  return (
    <div style={{ background: T.bg, borderRadius: 10, padding: '14px 16px', border: '1px solid ' + T.border, marginBottom: 14 }}>
      <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 10, color: T.muted }}>
        🎯 ZOPA TRACKER — Live Offer Positions
      </div>
      <div style={{ position: 'relative', height: 14, background: T.border, borderRadius: 7, marginBottom: 4 }}>
        {cOffer != null && (
          <div title={'Claimant: ' + fmt(cOffer)} style={{
            position: 'absolute', left: (toPct(cOffer) - 1) + '%', top: -3,
            width: 18, height: 18, borderRadius: '50%', background: T.accent,
            border: '2px solid #fff', transition: 'left 0.4s ease', zIndex: 2,
          }} />
        )}
        {rOffer != null && (
          <div title={'Respondent: ' + fmt(rOffer)} style={{
            position: 'absolute', left: (toPct(rOffer) - 1) + '%', top: -3,
            width: 18, height: 18, borderRadius: '50%', background: T.yellow,
            border: '2px solid #fff', transition: 'left 0.4s ease', zIndex: 2,
          }} />
        )}
        {cOffer != null && rOffer != null && rOffer >= cOffer && (
          <div style={{
            position: 'absolute',
            left: toPct(cOffer) + '%',
            width: Math.max(0, toPct(rOffer) - toPct(cOffer)) + '%',
            top: 2, bottom: 2, background: T.green, borderRadius: 5, opacity: 0.5,
          }} />
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: T.muted }}>
        <span>₹0</span>
        <span style={{ color: T.green }}>{cOffer != null && rOffer != null && rOffer >= cOffer ? '✓ ZOPA OVERLAP — agreement possible!' : ''}</span>
        <span>{fmt(claim)}</span>
      </div>
      <div style={{ display: 'flex', gap: 14, marginTop: 8, fontSize: 11 }}>
        <span style={{ color: T.accent }}>● Claimant offer: {cOffer != null ? fmt(cOffer) : '—'}</span>
        <span style={{ color: T.yellow }}>● Respondent offer: {rOffer != null ? fmt(rOffer) : '—'}</span>
      </div>
    </div>
  );
}

export default function NegotiationChat({ caseData, onUpdate }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput]       = useState('');
  const [offer, setOffer]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [err, setErr]           = useState('');
  const [lastMeta, setLastMeta] = useState(null);
  const [party]                 = useState('claimant');
  const scrollRef = useRef(null);

  const loadHistory = useCallback(async () => {
    try {
      const r = await API.get(`/api/cases/${caseData.id}/messages`);
      setMessages(r.data);
    } catch { /* history may not exist */ }
  }, [caseData.id]);

  useEffect(() => { loadHistory(); }, [loadHistory]);
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const lastC = [...messages].reverse().find(m => m.party === 'claimant' && m.offer)?.offer ?? null;
  const lastR = [...messages].reverse().find(m => m.party === 'respondent' && m.offer)?.offer ?? null;

  const send = async () => {
    if (!input.trim()) return;
    setErr(''); setLoading(true);
    const myMsg = { party, text: input, offer: offer ? parseFloat(offer) : null, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, myMsg]);
    setInput('');
    try {
      const r = await API.post(`/api/cases/${caseData.id}/negotiate`, {
        text: myMsg.text,
        offer: myMsg.offer,
      });
      setMessages(prev => [...prev, { party: 'mediator', text: r.data.mediator_response, timestamp: new Date().toISOString() }]);
      setLastMeta(r.data);
      setOffer('');
      if (r.data.agreement_reached) onUpdate(prev => ({ ...prev, agreement_amount: r.data.agreement_amount }));
    } catch (e) {
      setErr(e.response?.data?.detail || 'Message failed to send');
    } finally { setLoading(false); }
  };

  const quickReplies = [
    'I am ready to settle at a fair amount.',
    'Your offer is too low considering the delay.',
    'Let us find a middle ground.',
    'I accept the proposed settlement terms.',
  ];

  return (
    <div>
      {err && <Alert msg={err} type="error" />}

      <div style={css.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={css.title}>🤝 Module 4 — AI-Mediated Negotiation Room</div>
          {lastMeta?.phase && <Badge text={'Phase: ' + lastMeta.phase} color={PHASE_COLORS[lastMeta.phase] || T.accent} />}
        </div>
        {lastMeta?.phase && <PhaseTracker current={lastMeta.phase} />}
        <DealMeter claim={caseData.claim_amount} cOffer={lastC} rOffer={lastR} />

        {/* Chat History */}
        <div ref={scrollRef} style={{ ...css.scroll, minHeight: 280, padding: '12px 4px', background: T.bg, borderRadius: 10, border: '1px solid ' + T.border }}>
          {messages.length === 0 ? (
            <EmptyState icon="🕊️" text="No messages yet"
              subtext="Start the negotiation — the AI mediator will moderate the conversation" />
          ) : (
            messages.map((m, i) => <ChatBubble key={i} m={m} myParty={party} />)
          )}
          {loading && (
            <div style={{ textAlign: 'center', color: T.muted, fontSize: 12, padding: 8 }}>
              <Spinner /> AI Mediator is analyzing sentiment & strategy...
            </div>
          )}
        </div>

        {/* Quick replies */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', margin: '12px 0' }}>
          {quickReplies.map(q => (
            <button key={q} style={{ ...css.chip, cursor: 'pointer', padding: '5px 10px', border: 'none' }}
              onClick={() => setInput(q)}>{q}</button>
          ))}
        </div>

        {/* Input Row */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            style={{ ...css.input, flex: 3, marginBottom: 0 }}
            placeholder="Type your message to the other party..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
          />
          <input
            style={{ ...css.input, flex: 1, marginBottom: 0, minWidth: 120 }}
            placeholder="Offer ₹ (optional)"
            type="number"
            value={offer}
            onChange={e => setOffer(e.target.value)}
          />
          <button style={{ ...css.btn, background: `linear-gradient(135deg,${T.accent},${T.accent2})`, color: '#fff', padding: '10px 22px' }}
            onClick={send} disabled={loading || !input.trim()}>
            {loading ? <Spinner /> : 'Send ➤'}
          </button>
        </div>
      </div>

      {/* Mediator Insights */}
      {lastMeta && (
        <div style={css.grid3}>
          <div style={{ ...css.card, margin: 0 }}>
            <div style={{ fontSize: 12, color: T.muted, marginBottom: 4 }}>🧠 Detected Sentiment</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: sentiColor[lastMeta.sentiment_detected] || T.text }}>
              <SentimentIcon s={lastMeta.sentiment_detected} /> {lastMeta.sentiment_detected || '—'}
            </div>
          </div>
          <div style={{ ...css.card, margin: 0 }}>
            <div style={{ fontSize: 12, color: T.muted, marginBottom: 4 }}>🔁 Round</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: T.accent2 }}>{lastMeta.round || 0}</div>
          </div>
          <div style={{ ...css.card, margin: 0 }}>
            <div style={{ fontSize: 12, color: T.muted, marginBottom: 4 }}>🤝 Agreement</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: lastMeta.agreement_reached ? T.green : T.muted }}>
              {lastMeta.agreement_reached ? fmt(lastMeta.agreement_amount) : 'Not yet'}
            </div>
          </div>
        </div>
      )}

      {/* Agreement banner */}
      {(caseData.agreement_amount || lastMeta?.agreement_reached) && (
        <div style={{ ...css.card, background: `linear-gradient(135deg, ${T.green}22, ${T.accent2}22)`,
          border: '1px solid ' + T.green + '55', textAlign: 'center', padding: 28 }}>
          <div style={{ fontSize: 40 }}>🎉</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: T.green, margin: '8px 0' }}>AGREEMENT REACHED!</div>
          <div style={{ fontSize: 26, fontWeight: 800 }}>{fmt(lastMeta?.agreement_amount || caseData.agreement_amount)}</div>
          <div style={{ fontSize: 13, color: T.muted, marginTop: 8 }}>
            Both parties have entered the ZOPA. You can now generate the legal settlement agreement.
          </div>
        </div>
      )}
    </div>
  );
}
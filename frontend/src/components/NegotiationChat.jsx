import React, { useState, useEffect, useRef, useCallback } from 'react';
import API, { getApiError } from '../api';
import { css, fmt, sentiColor } from '../theme';
import { Badge, Spinner, Alert, EmptyState } from './UI';

const PHASES = ['opening', 'anchoring', 'bargaining', 'closing', 'agreement'];
const PHASE_COLORS = {
  opening:    'var(--primary)',
  anchoring:  '#3B82F6',
  bargaining: '#F59E0B',
  closing:    '#3C454C',
  agreement:  '#10B981',
  deadlock:   '#BA1A1A',
};

function SentimentIcon({ s }) {
  const map = {
    cooperative:  '😊',
    conciliatory: '🤝',
    neutral:      '😐',
    frustrated:   '😤',
    hostile:      '😠',
  };
  return <span style={{ fontSize: 13 }}>{map[s] || '💬'}</span>;
}

function PhaseTracker({ current }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 0,
      margin: '14px 0', flexWrap: 'wrap',
    }}>
      {PHASES.map((p, i) => {
        const active = p === current;
        const done   = PHASES.indexOf(current) > i;
        return (
          <React.Fragment key={p}>
            <div style={{
              flex: 1,
              textAlign: 'center',
              padding: '7px 6px',
              borderRadius: 6,
              background: active
                ? PHASE_COLORS[p] + '18'
                : done ? 'rgba(16,185,129,0.08)' : 'var(--surface)',
              border: '1px solid ' + (active
                ? PHASE_COLORS[p] + '66'
                : done ? '#10B98144' : 'var(--border)'),
              fontSize: 10, fontWeight: active ? 700 : 500,
              color: active
                ? PHASE_COLORS[p]
                : done ? '#10B981' : 'var(--text-secondary)',
              letterSpacing: '0.02em',
            }}>
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </div>
            {i < PHASES.length - 1 && (
              <span style={{
                color: 'var(--border)', fontSize: 10,
                padding: '0 2px', alignSelf: 'center',
              }}>
                ›
              </span>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function ChatBubble({ m, myParty }) {
  const isMe        = m.party === myParty;
  const isMediator  = m.party === 'mediator';
  const baseColor   = isMediator ? '#8B5CF6' : isMe ? 'var(--primary)' : 'var(--border)';
  const bgColor     = isMediator
    ? 'rgba(139,92,246,0.06)'
    : isMe ? 'rgba(0,102,102,0.06)' : 'var(--surface)';

  return (
    <div style={{
      display: 'flex',
      justifyContent: isMediator ? 'center' : isMe ? 'flex-end' : 'flex-start',
      marginBottom: 12,
      animation: 'fadeInUp 0.2s ease-out both',
    }}>
      <div style={{
        maxWidth: isMediator ? '85%' : '75%',
        background: bgColor,
        border: '1px solid ' + baseColor + '44',
        borderRadius: isMe ? '10px 10px 4px 10px' : isMediator ? 10 : '10px 10px 10px 4px',
        padding: '10px 14px',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          marginBottom: 4,
        }}>
          <span style={{ fontSize: 13 }}>
            {isMediator ? '🤖' : isMe ? '🙋' : '🏢'}
          </span>
          <span style={{
            fontSize: 11, fontWeight: 700,
            color: baseColor,
          }}>
            {isMediator ? 'AI Mediator' : isMe ? 'You' : m.party}
          </span>
          {m.sentiment && (
            <span style={{
              fontSize: 11, color: sentiColor[m.sentiment] || 'var(--text-secondary)',
            }}>
              <SentimentIcon s={m.sentiment} />{' '}
              {m.sentiment}
            </span>
          )}
        </div>
        <div style={{
          fontSize: 13, lineHeight: 1.6, color: 'var(--on-surface)',
          fontFamily: "'Inter', sans-serif",
        }}>
          {m.text}
        </div>
        {m.offer && (
          <div style={{
            marginTop: 8, padding: '6px 10px',
            borderRadius: 6,
            background: 'rgba(16,185,129,0.08)',
            border: '1px solid rgba(16,185,129,0.25)',
            fontSize: 13, fontWeight: 700, color: '#10B981',
            display: 'inline-block',
          }}>
            Offer: {fmt(m.offer)}
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
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 8,
      padding: '14px 16px',
      marginBottom: 14,
    }}>
      <div style={{
        fontSize: 11, fontWeight: 700, marginBottom: 10,
        color: 'var(--text-secondary)', letterSpacing: '0.03em',
      }}>
        ZOPA TRACKER — Live Offer Positions
      </div>
      <div style={{
        position: 'relative', height: 10,
        background: 'var(--border)', borderRadius: 5,
        marginBottom: 6,
      }}>
        {cOffer != null && (
          <div title={'Claimant: ' + fmt(cOffer)} style={{
            position: 'absolute', left: (toPct(cOffer) - 1) + '%',
            top: -3, width: 14, height: 14, borderRadius: '50%',
            background: 'var(--primary)',
            border: '2px solid #fff', transition: 'left 0.4s ease',
            zIndex: 2,
          }} />
        )}
        {rOffer != null && (
          <div title={'Respondent: ' + fmt(rOffer)} style={{
            position: 'absolute', left: (toPct(rOffer) - 1) + '%',
            top: -3, width: 14, height: 14, borderRadius: '50%',
            background: '#F59E0B',
            border: '2px solid #fff', transition: 'left 0.4s ease',
            zIndex: 2,
          }} />
        )}
        {cOffer != null && rOffer != null && rOffer >= cOffer && (
          <div style={{
            position: 'absolute',
            left: toPct(cOffer) + '%',
            width: Math.max(0, toPct(rOffer) - toPct(cOffer)) + '%',
            top: 2, bottom: 2,
            background: 'rgba(16,185,129,0.25)',
            borderRadius: 5,
          }} />
        )}
      </div>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: 10, color: 'var(--text-secondary)',
      }}>
        <span>₹0</span>
        {cOffer != null && rOffer != null && rOffer >= cOffer && (
          <span style={{ color: '#10B981', fontWeight: 600 }}>
            ✓ ZOPA Overlap — agreement possible
          </span>
        )}
        <span>{fmt(claim)}</span>
      </div>
      <div style={{
        display: 'flex', gap: 16, marginTop: 8,
        fontSize: 11, color: 'var(--text-secondary)',
        flexWrap: 'wrap',
      }}>
        <span style={{ color: 'var(--primary)', fontWeight: 600 }}>
          ● Claimant:{' '}
          {cOffer != null ? fmt(cOffer) : '—'}
        </span>
        <span style={{ color: '#F59E0B', fontWeight: 600 }}>
          ● Respondent:{' '}
          {rOffer != null ? fmt(rOffer) : '—'}
        </span>
      </div>
    </div>
  );
}

export default function NegotiationChat({ caseData, onUpdate }) {
  const [messages, setMessages]       = useState([]);
  const [input, setInput]             = useState('');
  const [offer, setOffer]             = useState('');
  const [loading, setLoading]         = useState(false);
  const [err, setErr]                 = useState('');
  const [lastMeta, setLastMeta]       = useState(null);
  const [party]                       = useState('claimant');
  const [streamingText, setStreamingText] = useState('');
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef                          = useRef(null);
  const onUpdateRef                    = useRef(onUpdate);
  onUpdateRef.current = onUpdate;
  const scrollRef                      = useRef(null);

  const loadHistory = useCallback(async () => {
    try {
      const r = await API.get(`/api/cases/${caseData.id}/messages`);
      setMessages(r.data);
    } catch { /* history may not exist */ }
  }, [caseData.id]);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  // WebSocket real-time
  useEffect(() => {
    const base = (API.defaults.baseURL || 'http://localhost:8000').replace(/^http/, 'ws');
    const ws = new WebSocket(`${base}/api/cases/ws/${caseData.id}?party=${party}`);
    wsRef.current = ws;
    ws.onopen  = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);
    ws.onmessage = e => {
      let f;
      try { f = JSON.parse(e.data); } catch { return; }
      if (f.type === 'user_message') {
        setMessages(prev => [...prev, {
          party: f.sender, text: f.text, offer: f.offer,
          timestamp: new Date().toISOString()
        }]);
      } else if (f.type === 'mediator_started') {
        setStreamingText('');
      } else if (f.type === 'mediator_token') {
        setStreamingText(prev => prev + (f.text || ''));
      } else if (f.type === 'mediator_response') {
        setMessages(prev => [...prev, {
          party: 'mediator',
          text: f.text,
          sentiment: f.sentiment,
          phase: f.phase,
          timestamp: new Date().toISOString(),
        }]);
        setLastMeta(f);
        setStreamingText('');
        if (f.agreement_reached) {
          onUpdateRef.current(prev => ({
            ...prev, agreement_amount: f.agreement_amount
          }));
        }
      }
    };
    return () => ws.close();
  }, [caseData.id, party]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages, streamingText]);

  const lastC = [...messages].reverse()
    .find(m => m.party === 'claimant' && m.offer)?.offer ?? null;
  const lastR = [...messages].reverse()
    .find(m => m.party === 'respondent' && m.offer)?.offer ?? null;

  const send = async () => {
    if (!input.trim()) return;
    setErr('');
    const text = input.trim();
    const amt  = offer ? parseFloat(offer) : null;
    setInput('');
    setOffer('');
    if (wsConnected && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ text, offer: amt }));
      return;
    }
    setLoading(true);
    const myMsg = { party, text, offer: amt, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, myMsg]);
    try {
      const r = await API.post(`/api/cases/${caseData.id}/negotiate`, { text, offer: amt });
      setMessages(prev => [...prev, {
        party: 'mediator',
        text: r.data.mediator_response,
        sentiment: r.data.sentiment_detected,
        phase: r.data.phase,
        timestamp: new Date().toISOString(),
      }]);
      setLastMeta(r.data);
      if (r.data.agreement_reached) {
        onUpdate(prev => ({
          ...prev, agreement_amount: r.data.agreement_amount
        }));
      }
    } catch (e) {
      setErr(getApiError(e, 'Message failed to send'));
    } finally {
      setLoading(false);
    }
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

      {/* Chat card */}
      <div style={{
        background: 'var(--surface-container-lowest)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        padding: 20,
      }}>
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          alignItems: 'center', marginBottom: 4,
        }}>
          <div style={{
            fontSize: 15, fontWeight: 700, color: 'var(--on-surface)',
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <span>🤝</span>
            AI-Mediated Negotiation Room
          </div>
          {lastMeta?.phase && (
            <Badge
              text={'Phase: ' + lastMeta.phase}
              color={PHASE_COLORS[lastMeta.phase] || 'var(--primary)'}
            />
          )}
        </div>
        {lastMeta?.phase && <PhaseTracker current={lastMeta.phase} />}
        <DealMeter claim={caseData.claim_amount} cOffer={lastC} rOffer={lastR} />

        {/* Messages */}
        <div ref={scrollRef} style={{
          ...css.scroll,
          minHeight: 280,
          padding: '12px 4px',
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          marginBottom: 12,
        }}>
          {messages.length === 0 ? (
            <EmptyState
              icon="🕊️"
              text="No messages yet"
              subtext="Start the negotiation — the AI mediator will moderate the conversation"
            />
          ) : (
            messages.map((m, i) => <ChatBubble key={i} m={m} myParty={party} />)
          )}
          {streamingText && (
            <div style={{
              display: 'flex', justifyContent: 'center',
              marginBottom: 12,
            }}>
              <div style={{
                maxWidth: '85%',
                background: 'rgba(139,92,246,0.06)',
                border: '1px solid rgba(139,92,246,0.3)',
                borderRadius: 10,
                padding: '10px 14px',
              }}>
                <div style={{
                  fontSize: 11, fontWeight: 700,
                  color: '#8B5CF6', marginBottom: 4,
                }}>
                  AI Mediator typing…
                </div>
                <div style={{
                  fontSize: 13, lineHeight: 1.6,
                  color: 'var(--on-surface)',
                }}>
                  {streamingText}▌
                </div>
              </div>
            </div>
          )}
          {loading && (
            <div style={{
              textAlign: 'center', color: 'var(--text-secondary)',
              fontSize: 12, padding: 8,
            }}>
              <Spinner /> AI Mediator is analyzing sentiment & strategy...
            </div>
          )}
        </div>

        {/* Quick replies */}
        <div style={{
          display: 'flex', gap: 6, flexWrap: 'wrap',
          marginBottom: 12,
        }}>
          {quickReplies.map(q => (
            <button
              key={q}
              style={{
                ...css.btnGhost,
                color: 'var(--text-secondary)',
                borderColor: 'var(--border)',
                padding: '6px 12px',
                fontSize: 12,
              }}
              onClick={() => { setInput(q); setOffer(''); }
            }
            >
              {q}
            </button>
          ))}
        </div>

        {/* Input */}
        <div style={{
          display: 'flex', gap: 10, alignItems: 'center',
          flexWrap: 'wrap',
        }}>
          <input
            style={{
              ...css.input,
              flex: 3,
              marginBottom: 0,
              fontSize: 13,
            }}
            placeholder="Type your message to the other party..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
          />
          <input
            style={{
              ...css.input,
              flex: 1,
              marginBottom: 0,
              minWidth: 120,
              fontSize: 13,
            }}
            placeholder="Offer ₹ (optional)"
            type="number"
            value={offer}
            onChange={e => setOffer(e.target.value)}
          />
          <button
            style={{
              ...css.btn,
              background: 'var(--primary)',
              color: 'var(--on-primary)',
              padding: '10px 20px',
              boxShadow: '0 2px 8px rgba(0,102,102,0.25)',
            }}
            onClick={send}
            disabled={loading || !input.trim()}
          >
            {loading ? <Spinner /> : 'Send'}
          </button>
        </div>
      </div>

      {/* Mediator insights row */}
      {lastMeta && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 12,
          marginBottom: 16,
        }}>
          <div style={{
            background: 'var(--surface-container-lowest)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: '14px 16px',
          }}>
            <div style={{
              fontSize: 11, color: 'var(--text-secondary)',
              marginBottom: 4, fontWeight: 500,
            }}>
              Detected Sentiment
            </div>
            <div style={{
              fontSize: 16, fontWeight: 700,
              color: sentiColor[lastMeta.sentiment_detected] || 'var(--on-surface)',
              display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <SentimentIcon s={lastMeta.sentiment_detected} />
              {lastMeta.sentiment_detected || '—'}
            </div>
          </div>
          <div style={{
            background: 'var(--surface-container-lowest)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: '14px 16px',
          }}>
            <div style={{
              fontSize: 11, color: 'var(--text-secondary)',
              marginBottom: 4, fontWeight: 500,
            }}>
              Round
            </div>
            <div style={{
              fontSize: 16, fontWeight: 700,
              color: 'var(--primary)',
            }}>
              {lastMeta.round || 0}
            </div>
          </div>
          <div style={{
            background: 'var(--surface-container-lowest)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: '14px 16px',
          }}>
            <div style={{
              fontSize: 11, color: 'var(--text-secondary)',
              marginBottom: 4, fontWeight: 500,
            }}>
              Agreement
            </div>
            <div style={{
              fontSize: 16, fontWeight: 700,
              color: lastMeta.agreement_reached ? '#10B981' : 'var(--text-secondary)',
            }}>
              {lastMeta.agreement_reached
                ? fmt(lastMeta.agreement_amount)
                : 'Not yet'}
            </div>
          </div>
        </div>
      )}

      {/* Agreement banner */}
      {(caseData.agreement_amount || lastMeta?.agreement_reached) && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(16,185,129,0.08), rgba(6,182,212,0.08))',
          border: '1px solid rgba(16,185,129,0.35)',
          borderRadius: 8,
          textAlign: 'center',
          padding: 28,
          animation: 'scaleIn 0.4s ease-out both',
        }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>🎉</div>
          <div style={{
            fontSize: 18, fontWeight: 800,
            color: '#10B981', margin: '8px 0',
          }}>
            AGREEMENT REACHED!
          </div>
          <div style={{
            fontSize: 26, fontWeight: 800,
            color: 'var(--primary)',
          }}>
            {fmt(lastMeta?.agreement_amount || caseData.agreement_amount)}
          </div>
          <div style={{
            fontSize: 13, color: 'var(--text-secondary)',
            marginTop: 8,
            maxWidth: 480, margin: '8px auto 0', lineHeight: 1.6,
          }}>
            Both parties have entered the ZOPA.
            You can now generate the legal settlement agreement.
          </div>
        </div>
      )}
    </div>
  );
}

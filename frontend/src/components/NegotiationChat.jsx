import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import API, { getApiError } from '../api';
import { css, fmt, sentiColor } from '../theme';
import { Badge, Spinner, Alert, EmptyState, Button } from './UI';
import { useDebouncedCallback } from '../hooks/useDebouncedCallback';

// How long the peer keeps seeing "typing…" after the last keystroke, and the
// client-side watchdog that clears a stale indicator if the sender vanishes.
const TYPING_STOP_MS = 500;
const TYPING_WATCHDOG_MS = 5000;

const PHASES = ['opening', 'anchoring', 'bargaining', 'closing', 'agreement'];
const PHASE_COLORS = {
  opening:    'var(--primary)',
  anchoring:  '#3B82F6',
  bargaining: '#F59E0B',
  closing:    '#3C454C',
  agreement:  '#10B981',
  deadlock:   '#BA1A1A',
};

const SentimentIcon = React.memo(function SentimentIcon({ s }) {
  const map = {
    cooperative:  '😊',
    conciliatory: '🤝',
    neutral:      '😐',
    frustrated:   '😤',
    hostile:      '😠',
  };
  return <span style={{ fontSize: 13 }}>{map[s] || '💬'}</span>;
});

const PhaseTracker = React.memo(function PhaseTracker({ current }) {
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
});

const ChatBubble = React.memo(function ChatBubble({ m, myParty }) {
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
});

const DealMeter = React.memo(function DealMeter({ claim, cOffer, rOffer }) {
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
});

const QUICK_REPLIES = [
  'I am ready to settle at a fair amount.',
  'Your offer is too low considering the delay.',
  'Let us find a middle ground.',
  'I accept the proposed settlement terms.',
];

/*
 * Message list is its own memoized component: while the mediator streams tokens
 * the parent re-renders on every token, but `messages`/`myParty` keep their
 * identity, so React bails out of the whole list instead of walking every bubble.
 */
const MessageList = React.memo(function MessageList({ messages, myParty }) {
  return messages.map((m, i) => <ChatBubble key={i} m={m} myParty={myParty} />);
});

/*
 * The composer owns the input/offer state so typing (one state change per
 * keystroke) only re-renders these two fields, not the whole negotiation room.
 */
const Composer = React.memo(function Composer({ onSend, onTyping, loading }) {
  const [input, setInput] = useState('');
  const [offer, setOffer] = useState('');
  // The peer should learn about typing as it starts, so `true` goes out on the
  // leading edge while the matching `false` is debounced until the user pauses.
  const typingRef = useRef(false);
  const { debounced: stopTypingLater, cancel: cancelStopTyping } =
    useDebouncedCallback(() => onTyping(false), TYPING_STOP_MS);

  const handleMessageChange = useCallback((e) => {
    setInput(e.target.value);
    if (!typingRef.current) {
      typingRef.current = true;
      onTyping(true);
    }
    stopTypingLater();
  }, [onTyping, stopTypingLater]);

  const submit = useCallback(() => {
    const text = input.trim();
    if (!text) return;
    // Explicit check: offer=0 ("free settlement") is valid — the old
    // truthy test silently dropped it.
    const trimmed = offer.trim();
    const amt = trimmed !== '' ? parseFloat(trimmed) : null;
    if (trimmed !== '' && !Number.isFinite(amt)) return;
    onSend(text, amt);
    // Sending ends the burst now — don't make the peer wait out the timer.
    if (typingRef.current) {
      typingRef.current = false;
      cancelStopTyping();
      onTyping(false);
    }
    setInput('');
    setOffer('');
  }, [input, offer, onSend, onTyping, cancelStopTyping]);

  const pickQuickReply = useCallback((q) => { setInput(q); setOffer(''); }, []);

  return (
    <>
      {/* Quick replies */}
      <div style={{
        display: 'flex', gap: 6, flexWrap: 'wrap',
        marginBottom: 12,
      }}>
        {QUICK_REPLIES.map(q => (
          <button
            key={q}
            type="button"
            className="btn btn-ghost btn-sm quick-reply"
            onClick={() => pickQuickReply(q)}
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
          onChange={handleMessageChange}
          onKeyDown={e => e.key === 'Enter' && submit()}
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
        <Button
          variant="primary"
          loading={loading}
          disabled={!input.trim()}
          onClick={submit}
        >
          Send
        </Button>
      </div>
    </>
  );
});

export default function NegotiationChat({ caseData, onUpdate }) {
  const [messages, setMessages]       = useState([]);
  const [loading, setLoading]         = useState(false);
  const [err, setErr]                 = useState('');
  const [lastMeta, setLastMeta]       = useState(null);
  const [party]                       = useState('claimant');
  const [streamingText, setStreamingText] = useState('');
  const [wsConnected, setWsConnected] = useState(false);
  const [otherTyping, setOtherTyping] = useState(false);
  // True between sending a message and the mediator starting to answer. Without
  // it a dropped socket was indistinguishable from "thinking": the message was
  // fire-and-forget over the WebSocket, so no reply and no error ever appeared.
  const [awaitingReply, setAwaitingReply] = useState(false);
  const awaitingRef    = useRef(false);
  const replyTimerRef  = useRef(null);
  const wsRef                          = useRef(null);
  const onUpdateRef                    = useRef(onUpdate);
  onUpdateRef.current = onUpdate;
  const scrollRef                      = useRef(null);
  const typingWatchdogRef              = useRef(null);

  const loadHistory = useCallback(async () => {
    try {
      const r = await API.get(`/api/cases/${caseData.id}/messages`);
      setMessages(r.data);
    } catch { /* history may not exist */ }
  }, [caseData.id]);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  // Peer typing indicator. The sender emits `is_typing: false` when it pauses,
  // but if it drops off mid-sentence nobody would, so a watchdog clears it.
  const stopReplyWatch = useCallback(() => {
    if (replyTimerRef.current) {
      clearTimeout(replyTimerRef.current);
      replyTimerRef.current = null;
    }
    awaitingRef.current = false;
    setAwaitingReply(false);
  }, []);

  const startReplyWatch = useCallback(() => {
    awaitingRef.current = true;
    setAwaitingReply(true);
    if (replyTimerRef.current) clearTimeout(replyTimerRef.current);
    // Backstop only — a dropped socket is normally caught by onclose long
    // before this fires. Generous, because a GPU/CPU-split model can legitimately
    // take a while to produce its first token.
    replyTimerRef.current = setTimeout(() => {
      replyTimerRef.current = null;
      if (!awaitingRef.current) return;
      awaitingRef.current = false;
      setAwaitingReply(false);
      setErr('The mediator did not reply. Your message was sent — resend it if no reply appears.');
    }, 90000);
  }, []);

  useEffect(() => () => {
    if (replyTimerRef.current) clearTimeout(replyTimerRef.current);
  }, []);

  const clearOtherTyping = useCallback(() => {
    if (typingWatchdogRef.current) {
      clearTimeout(typingWatchdogRef.current);
      typingWatchdogRef.current = null;
    }
    setOtherTyping(false);
  }, []);

  const showOtherTyping = useCallback(() => {
    setOtherTyping(true);
    if (typingWatchdogRef.current) clearTimeout(typingWatchdogRef.current);
    typingWatchdogRef.current = setTimeout(() => {
      typingWatchdogRef.current = null;
      setOtherTyping(false);
    }, TYPING_WATCHDOG_MS);
  }, []);

  useEffect(() => clearOtherTyping, [clearOtherTyping]);

  // WebSocket real-time
  useEffect(() => {
    const base = (API.defaults.baseURL || 'http://localhost:8000').replace(/^http/, 'ws');
    let closed = false;
    let attempt = 0;
    let retryTimer = null;

    // One socket per invocation; onclose schedules the next attempt.
    function connect() {
      const ws = new WebSocket(`${base}/api/cases/ws/${caseData.id}?party=${party}`);
      wsRef.current = ws;
      ws.onopen = () => { attempt = 0; setWsConnected(true); };
      ws.onerror = () => { setWsConnected(false); clearOtherTyping(); };
      ws.onclose = () => {
        setWsConnected(false);
        clearOtherTyping();
        // If we were mid-request the reply is never coming, so say so rather
        // than leaving the user watching a spinner forever. The message itself
        // was delivered, so ask them to resend instead of replaying it — a
        // replay would post a second mediator turn.
        if (awaitingRef.current) {
          stopReplyWatch();
          setErr('Connection to the mediator dropped before it replied. Your message was sent — resend it if no reply appears.');
        }
        // Panels stay mounted across tab switches now, so without reconnecting a
        // dropped socket stayed dead for the rest of the session: every later
        // message silently took the REST path, or was lost entirely.
        if (closed) return;
        attempt += 1;
        retryTimer = setTimeout(connect, Math.min(1000 * 2 ** attempt, 15000));
      };
      ws.onmessage = e => {
        let f;
        try { f = JSON.parse(e.data); } catch { return; }
        if (f.type === 'typing') {
          // Our own frames are echoed back by the broadcast — ignore them.
          if (f.sender !== party) (f.is_typing ? showOtherTyping() : clearOtherTyping)();
        } else if (f.type === 'user_message') {
          if (f.sender !== party) clearOtherTyping();
          setMessages(prev => [...prev, {
            party: f.sender, text: f.text, offer: f.offer,
            timestamp: new Date().toISOString()
          }]);
        } else if (f.type === 'mediator_started') {
          stopReplyWatch();          // the reply is arriving — stop the watchdog
          setStreamingText('');
        } else if (f.type === 'mediator_token') {
          setStreamingText(prev => prev + (f.text || ''));
        } else if (f.type === 'mediator_response') {
          stopReplyWatch();
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
    }

    connect();
    return () => {
      closed = true;
      if (retryTimer) clearTimeout(retryTimer);
      wsRef.current?.close();
    };
  }, [caseData.id, party, clearOtherTyping, showOtherTyping, stopReplyWatch]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages, streamingText]);

  const lastC = useMemo(() =>
    [...messages].reverse()
      .find(m => m.party === 'claimant' && m.offer)?.offer ?? null,
    [messages]
  );
  const lastR = useMemo(() =>
    [...messages].reverse()
      .find(m => m.party === 'respondent' && m.offer)?.offer ?? null,
    [messages]
  );

  const sendTyping = useCallback((isTyping) => {
    const ws = wsRef.current;
    // Nothing to fall back to over REST — a missing indicator is harmless.
    if (!wsConnected || ws?.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: 'typing', is_typing: isTyping }));
  }, [wsConnected]);

  const send = useCallback(async (text, amt) => {
    setErr('');
    if (wsConnected && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ text, offer: amt }));
      // Over the socket there is no response object to await, so track it
      // explicitly: 'mediator_started' clears this, a dropped socket reports it.
      startReplyWatch();
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
        onUpdateRef.current(prev => ({
          ...prev, agreement_amount: r.data.agreement_amount
        }));
      }
    } catch (e) {
      setErr(getApiError(e, 'Message failed to send'));
    } finally {
      setLoading(false);
    }
  }, [caseData.id, party, wsConnected, startReplyWatch]);

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
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {otherTyping && (
              <span style={{
                fontSize: 11, fontStyle: 'italic',
                color: 'var(--text-secondary)',
              }}>
                <span style={{ color: '#8B5CF6' }}>●</span> Other party is typing…
              </span>
            )}
            {lastMeta?.phase && (
              <Badge
                text={'Phase: ' + lastMeta.phase}
                color={PHASE_COLORS[lastMeta.phase] || 'var(--primary)'}
              />
            )}
          </div>
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
            <MessageList messages={messages} myParty={party} />
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
          {(loading || awaitingReply) && (
            <div style={{
              textAlign: 'center', color: 'var(--text-secondary)',
              fontSize: 12, padding: 8,
            }}>
              <Spinner /> AI Mediator is analyzing sentiment & strategy...
            </div>
          )}
        </div>

        <Composer onSend={send} onTyping={sendTyping} loading={loading} />
      </div>

      {/* Mediator insights row */}
      {lastMeta && (
        <div className="grid-cols-3" style={{ display: 'grid', gap: 12, marginBottom: 16 }}>
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

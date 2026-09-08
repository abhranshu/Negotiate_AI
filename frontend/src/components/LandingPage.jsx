
import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { T } from '../theme';
 
/* Scroll Reveal Hook */
function useReveal(threshold) {
  threshold = threshold || 0.15;
  const ref = useRef(null);
  useEffect(function () {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      function (entries) {
        if (entries[0].isIntersecting) { el.classList.add('visible'); obs.unobserve(el); }
      },
      { threshold }
    );
    obs.observe(el);
    return function () { obs.disconnect(); };
  }, [threshold]);
  return ref;
}
 
function RevealDiv(props) {
  const cls = props.className || '';
  const dir = props.direction || 'up';
  const delay = props.delay || 0;
  const st = props.style || {};
  const dirClass = dir === 'left' ? 'reveal-left' : dir === 'right' ? 'reveal-right' : 'reveal';
  const ref = useReveal(0.12);
  return (
    <div ref={ref} className={dirClass + ' ' + cls} style={{ transitionDelay: delay + 's', ...st }}>
      {props.children}
    </div>
  );
}
 
/* Animated Counter */
function AnimatedCounter(props) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const started = useRef(false);
  useEffect(function () {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting && !started.current) {
        started.current = true;
        const duration = 2000, start = performance.now();
        const animate = function (now) {
          const progress = Math.min((now - start) / duration, 1);
          setCount(Math.floor((1 - Math.pow(1 - progress, 4)) * props.target));
          if (progress < 1) requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
      }
    }, { threshold: 0.5 });
    obs.observe(el);
    return function () { obs.disconnect(); };
  }, [props.target]);
  return <span ref={ref}>{count.toLocaleString('en-IN')}{props.suffix || ''}</span>;
}
 
/* Floating Orbs */
function FloatingOrbs() {
  const orbs = [
    { size: 300, color: 'rgba(59,130,246,0.08)', top: '-10%', left: '-5%', dur: '20s' },
    { size: 250, color: 'rgba(6,182,212,0.06)', bottom: '10%', right: '-8%', dur: '25s' },
    { size: 200, color: 'rgba(139,92,246,0.05)', top: '40%', left: '60%', dur: '18s' }
  ];
  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {orbs.map((o, i) => (
        <div key={i} style={{
          position: 'absolute', width: o.size, height: o.size, borderRadius: '50%',
          background: 'radial-gradient(circle, ' + o.color + ', transparent 70%)',
          top: o.top, bottom: o.bottom, left: o.left, right: o.right,
          animation: 'float ' + o.dur + ' ease-in-out infinite',
          animationDelay: (i * 2) + 's', filter: 'blur(40px)'
        }} />
      ))}
    </div>
  );
}
 
/* Navbar */
function Navbar({ onNavigate }) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(function () {
    const handler = function () { setScrolled(window.scrollY > 40); };
    window.addEventListener('scroll', handler, { passive: true });
    return function () { window.removeEventListener('scroll', handler); };
  }, []);
  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
      padding: '0 40px', height: 72, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      background: scrolled ? 'rgba(10,15,30,0.85)' : 'transparent',
      backdropFilter: scrolled ? 'blur(20px)' : 'none',
      WebkitBackdropFilter: scrolled ? 'blur(20px)' : 'none',
      borderBottom: scrolled ? '1px solid rgba(30,45,69,0.5)' : '1px solid transparent',
      transition: 'all 0.4s cubic-bezier(0.16,1,0.3,1)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ fontSize: 28 }}>⚖️</div>
        <span style={{ fontSize: 20, fontWeight: 800, fontFamily: 'var(--font-display)' }}>
          <span className="gradient-text-static">Negotiate</span>
          <span style={{ color: T.text }}>AI</span>
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 32, fontSize: 14, fontWeight: 500 }}>
        {['Features', 'How It Works', 'Modules', 'Stats'].map(function (item) {
          return <a key={item} href={'#' + item.toLowerCase().replace(/ /g, '-')}
            style={{ color: T.muted, textDecoration: 'none', transition: 'color 0.25s', cursor: 'pointer' }}>{item}</a>;
        })}
        <button onClick={() => onNavigate('/app')}
          style={{ padding: '10px 24px', borderRadius: 10, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 14, fontFamily: 'var(--font-body)', background: 'linear-gradient(135deg, #3b82f6, #06b6d4)', color: '#fff' }}>
          Launch App →
        </button>
      </div>
    </nav>
  );
}
 
/* Data */
const FEATURES = [
  { icon: '🎙️', title: 'Voice Dispute Intake', desc: 'Speak in any Indian language. Whisper ASR + NER auto-fills dispute details.', color: T.accent },
  { icon: '📄', title: 'Document Intelligence', desc: 'Upload invoices, POs, contracts. OCR + DistilBERT classifies and extracts data.', color: T.accent2 },
  { icon: '📊', title: 'Outcome Prediction', desc: 'XGBoost + SHAP predicts settlement probability, range, and timeline.', color: T.green },
  { icon: '🤝', title: 'AI-Mediated Negotiation', desc: 'Nash Bargaining + sentiment analysis. Real-time ZOPA tracking.', color: T.purple },
  { icon: '📜', title: 'Settlement Generator', desc: 'MSMED Act-compliant legal agreement. Rule-based validator.', color: T.yellow },
  { icon: '🧠', title: 'Legal RAG Engine', desc: 'TF-IDF retrieval of MSMED Act provisions. Grounds citations in real law.', color: T.red }
];
 
const STEPS = [
  { num: '01', icon: '🎙️', title: 'Voice & Document Intake', desc: 'Record a voice dispute or upload documents. Auto-extracts party names, amounts, and dates.', color: T.accent },
  { num: '02', icon: '📊', title: 'ML Outcome Prediction', desc: 'XGBoost + LightGBM predicts settlement probability and range. SHAP explains every factor.', color: T.accent2 },
  { num: '03', icon: '🤝', title: 'AI-Mediated Negotiation', desc: 'Nash Bargaining Solution and sentiment analysis guide parties toward agreement.', color: T.green },
  { num: '04', icon: '📜', title: 'Settlement Generation', desc: 'Generates legally valid agreement compliant with MSMED Act 2006.', color: T.purple },
  { num: '05', icon: '✅', title: 'Validation & Signing', desc: 'Rule-based validator checks all mandatory clauses.', color: T.yellow }
];
 
const MODULES = [
  { icon: '🎙️', title: 'Whisper ASR + NER', tech: 'OpenAI Whisper + spaCy', desc: 'Supports 12+ Indian languages. NER extracts amounts, dates, and party names.', color: T.accent },
  { icon: '📄', title: 'Document Classification', tech: 'DistilBERT + Tesseract OCR', desc: 'Classifies invoices, POs, contracts. Extracts line-item amounts.', color: T.accent2 },
  { icon: '📊', title: 'Prediction Ensemble', tech: 'XGBoost + LightGBM + SHAP', desc: 'Trained on synthetic MSME Samadhan data. Predicts settlement probability.', color: T.green },
  { icon: '🤝', title: 'Game Theory Engine', tech: 'Nash Bargaining + Sentiment', desc: 'Nash Bargaining Solution computes optimal split. ZOPA detection.', color: T.purple },
  { icon: '📜', title: 'Settlement Generator', tech: 'Template + Legal Validator', desc: 'MSMED Act Sections 15-23 compliant. Rule-based validator.', color: T.yellow },
  { icon: '🧠', title: 'Legal RAG Engine', tech: 'TF-IDF + MSMED Corpus', desc: 'TF-IDF keyword matching. Injects real law citations.', color: T.red }
];
 
const STATS = [
  { value: 5, suffix: '+', label: 'ML Modules', color: T.accent },
  { value: 12, suffix: '+', label: 'Indian Languages', color: T.accent2 },
  { value: 94, suffix: '%', label: 'Settlement Accuracy', color: T.green },
  { value: 45, suffix: ' days', label: 'Avg Resolution Time', color: T.purple }
];
 
const PIPELINE = [
  { icon: '🎙️', label: 'Voice', desc: 'Whisper ASR' },
  { icon: '📄', label: 'Documents', desc: 'OCR + NER' },
  { icon: '📊', label: 'Predict', desc: 'XGBoost' },
  { icon: '🤝', label: 'Negotiate', desc: 'Game Theory' },
  { icon: '📜', label: 'Settle', desc: 'MSMED PDF' }
];
 
/* ═══════════════════════════════════════════════════════════════════════════
   LANDING PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
export default function LandingPage() {
  const navigate = useNavigate();
  return (
    <div style={{ minHeight: '100vh', background: T.bg, color: T.text, fontFamily: 'var(--font-body)' }}>
      <Navbar onNavigate={navigate} />
 
      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <section className="grid-bg" style={{ position: 'relative', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '120px 40px 80px', overflow: 'hidden' }}>
        <FloatingOrbs />
        <div style={{ position: 'relative', zIndex: 2, textAlign: 'center', maxWidth: 900 }}>
          <div className="animate-fade-in-down" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '8px 20px', borderRadius: 50, background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.25)', fontSize: 13, fontWeight: 600, color: T.accent, marginBottom: 32 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: T.green, animation: 'dot-pulse 2s infinite' }} />
            Powered by XGBoost + Game Theory + Legal LLM
          </div>
          <h1 className="hero-title animate-fade-in-up" style={{ fontSize: '4rem', fontWeight: 900, lineHeight: 1.1, fontFamily: 'var(--font-display)', marginBottom: 24 }}>
            AI-Powered <span className="gradient-text">MSME Dispute</span><br />Resolution Platform
          </h1>
          <p className="hero-subtitle animate-fade-in-up delay-2" style={{ fontSize: 18, color: T.muted, lineHeight: 1.7, maxWidth: 640, margin: '0 auto 40px' }}>
            Resolve payment disputes under the <strong style={{ color: T.text }}>MSMED Act 2006</strong> using voice intake, document intelligence, predictive analytics, and AI-mediated negotiation.
          </p>
          <div className="animate-fade-in-up delay-3" style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button className="btn-primary" style={{ fontSize: 16, padding: '16px 40px' }} onClick={() => navigate('/app')}>⚖️ Start Resolving Disputes</button>
            <button className="btn-outline" style={{ fontSize: 16, padding: '16px 40px' }} onClick={() => { const el = document.getElementById('how-it-works'); if (el) el.scrollIntoView({ behavior: 'smooth' }); }}>See How It Works ↓</button>
          </div>
          <div className="animate-fade-in-up delay-4" style={{ display: 'flex', gap: 20, justifyContent: 'center', marginTop: 48, flexWrap: 'wrap' }}>
            {['MSMED Act 2006', '5-Step ML Pipeline', 'Multilingual Voice', 'Legal LLM'].map(tag =>
              <span key={tag} style={{ padding: '6px 16px', borderRadius: 8, fontSize: 12, fontWeight: 600, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: T.muted }}>{tag}</span>
            )}
          </div>
          <div className="animate-fade-in-up delay-5 animate-float" style={{ marginTop: 64, padding: '24px 32px', borderRadius: 20, background: 'rgba(15,22,38,0.8)', backdropFilter: 'blur(20px)', border: '1px solid rgba(30,45,69,0.6)', display: 'inline-flex', alignItems: 'center', gap: 24, boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}>
            {PIPELINE.map((step, i) => (
              <React.Fragment key={step.label}>
                <div style={{ textAlign: 'center', minWidth: 70 }}>
                  <div style={{ fontSize: 28, marginBottom: 4 }}>{step.icon}</div>
                  <div style={{ fontSize: 12, fontWeight: 700 }}>{step.label}</div>
                  <div style={{ fontSize: 10, color: T.muted }}>{step.desc}</div>
                </div>
                {i < 4 && <div style={{ color: T.border, fontSize: 20 }}>→</div>}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>
 
      {/* ── STATS ────────────────────────────────────────────────────────── */}
      <section id="stats" style={{ padding: '80px 40px' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 20 }}>
            {STATS.map((stat, i) => (
              <RevealDiv key={stat.label} delay={i * 0.1}>
                <div style={{ textAlign: 'center', padding: '32px 16px', borderRadius: 16, background: 'rgba(15,22,38,0.6)', border: '1px solid rgba(30,45,69,0.4)' }}>
                  <div style={{ fontSize: 40, fontWeight: 900, color: stat.color, fontFamily: 'var(--font-display)' }}>
                    <AnimatedCounter target={stat.value} suffix={stat.suffix} />
                  </div>
                  <div style={{ fontSize: 13, color: T.muted, marginTop: 6 }}>{stat.label}</div>
                </div>
              </RevealDiv>
            ))}
          </div>
        </div>
      </section>
      <div className="section-divider" />
 
      {/* ── FEATURES ─────────────────────────────────────────────────────── */}
      <section id="features" style={{ padding: '100px 40px' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <RevealDiv style={{ textAlign: 'center', marginBottom: 64 }}>
            <span style={{ display: 'inline-block', padding: '6px 16px', borderRadius: 20, background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.25)', fontSize: 12, fontWeight: 700, color: T.accent, marginBottom: 16, textTransform: 'uppercase' }}>Why NegotiateAI</span>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 800, fontFamily: 'var(--font-display)', marginBottom: 16 }}>End-to-End <span className="gradient-text">Dispute Resolution</span></h2>
            <p style={{ fontSize: 16, color: T.muted, maxWidth: 560, margin: '0 auto', lineHeight: 1.7 }}>From voice intake to legally binding settlement — every step powered by AI.</p>
          </RevealDiv>
          <div className="features-grid stagger-children" style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 20 }}>
            {FEATURES.map((f, i) => (
              <RevealDiv key={f.title} delay={i * 0.08}>
                <div className="glass-card" style={{ padding: '28px 24px', height: '100%' }}>
                  <div style={{ width: 52, height: 52, borderRadius: 14, background: f.color + '15', border: '1px solid ' + f.color + '33', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26, marginBottom: 16 }}>{f.icon}</div>
                  <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 10 }}>{f.title}</h3>
                  <p style={{ fontSize: 13, color: T.muted, lineHeight: 1.7, margin: 0 }}>{f.desc}</p>
                </div>
              </RevealDiv>
            ))}
          </div>
        </div>
      </section>
      <div className="section-divider" />
 
      {/* ── HOW IT WORKS ─────────────────────────────────────────────────── */}
      <section id="how-it-works" style={{ padding: '100px 40px' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <RevealDiv style={{ textAlign: 'center', marginBottom: 64 }}>
            <span style={{ display: 'inline-block', padding: '6px 16px', borderRadius: 20, background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.25)', fontSize: 12, fontWeight: 700, color: T.accent2, marginBottom: 16, textTransform: 'uppercase' }}>Process</span>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 800, fontFamily: 'var(--font-display)', marginBottom: 16 }}>How It <span className="gradient-text">Works</span></h2>
            <p style={{ fontSize: 16, color: T.muted, maxWidth: 520, margin: '0 auto', lineHeight: 1.7 }}>Five steps from intake to legally binding settlement.</p>
          </RevealDiv>
          <div className="steps-grid" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 0 }}>
            {STEPS.map((step, i) => (
              <RevealDiv key={step.num} direction={i % 2 === 0 ? 'left' : 'right'} delay={0.05}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 32, padding: '28px 32px' }}>
                  <div style={{ width: 64, height: 64, borderRadius: 16, flexShrink: 0, background: step.color + '15', border: '1px solid ' + step.color + '33', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, fontWeight: 900, color: step.color, fontFamily: 'var(--font-display)' }}>{step.num}</div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                      <span style={{ fontSize: 22 }}>{step.icon}</span>
                      <h3 style={{ fontSize: 17, fontWeight: 700 }}>{step.title}</h3>
                    </div>
                    <p style={{ fontSize: 13, color: T.muted, lineHeight: 1.7, margin: 0, maxWidth: 700 }}>{step.desc}</p>
                  </div>
                </div>
              </RevealDiv>
            ))}
          </div>
        </div>
      </section>
      <div className="section-divider" />
 
      {/* ── MODULES ──────────────────────────────────────────────────────── */}
      <section id="modules" style={{ padding: '100px 40px' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <RevealDiv style={{ textAlign: 'center', marginBottom: 64 }}>
            <span style={{ display: 'inline-block', padding: '6px 16px', borderRadius: 20, background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.25)', fontSize: 12, fontWeight: 700, color: T.purple, marginBottom: 16, textTransform: 'uppercase' }}>Technology</span>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 800, fontFamily: 'var(--font-display)', marginBottom: 16 }}>Under the <span className="gradient-text">Hood</span></h2>
            <p style={{ fontSize: 16, color: T.muted, maxWidth: 560, margin: '0 auto', lineHeight: 1.7 }}>State-of-the-art ML, purpose-built for Indian MSME dispute resolution.</p>
          </RevealDiv>
          <div className="features-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {MODULES.map((m, i) => (
              <RevealDiv key={m.title} delay={i * 0.08}>
                <div className="glass-card" style={{ padding: '24px', height: '100%' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 14 }}>
                    <div style={{ width: 48, height: 48, borderRadius: 12, flexShrink: 0, background: m.color + '15', border: '1px solid ' + m.color + '33', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24 }}>{m.icon}</div>
                    <div>
                      <h3 style={{ fontSize: 15, fontWeight: 700 }}>{m.title}</h3>
                      <div style={{ fontSize: 11, color: m.color, fontWeight: 600, marginTop: 2 }}>{m.tech}</div>
                    </div>
                  </div>
                  <p style={{ fontSize: 13, color: T.muted, lineHeight: 1.7, margin: 0 }}>{m.desc}</p>
                </div>
              </RevealDiv>
            ))}
          </div>
        </div>
      </section>
      <div className="section-divider" />
 
      {/* ── QUOTE ────────────────────────────────────────────────────────── */}
      <section style={{ padding: '100px 40px' }}>
        <div style={{ maxWidth: 700, margin: '0 auto', textAlign: 'center' }}>
          <RevealDiv>
            <div style={{ fontSize: 48, marginBottom: 16 }}>💬</div>
            <blockquote style={{ fontSize: 22, fontWeight: 500, lineHeight: 1.7, fontStyle: 'italic', color: T.text, margin: '0 0 24px' }}>
              "Under the MSMED Act, 95% of disputes should be resolved within 90 days. Yet the average is 487 days. NegotiateAI aims to bring that back under 45."
            </blockquote>
            <div style={{ fontSize: 13, color: T.muted }}>— Based on MSME Samadhan data analysis</div>
          </RevealDiv>
        </div>
      </section>
      <div className="section-divider" />
 
      {/* ── CTA ──────────────────────────────────────────────────────────── */}
      <section style={{ padding: '100px 40px' }}>
        <RevealDiv>
          <div style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center', padding: '60px 40px', borderRadius: 24, position: 'relative', overflow: 'hidden', background: 'linear-gradient(135deg, rgba(59,130,246,0.1), rgba(6,182,212,0.1))', border: '1px solid rgba(59,130,246,0.2)' }}>
            <div style={{ position: 'absolute', top: '-50%', left: '50%', transform: 'translateX(-50%)', width: 400, height: 400, borderRadius: '50%', background: 'radial-gradient(circle, rgba(59,130,246,0.15), transparent 70%)', filter: 'blur(60px)', pointerEvents: 'none' }} />
            <div style={{ position: 'relative', zIndex: 2 }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>⚖️</div>
              <h2 style={{ fontSize: '2.2rem', fontWeight: 800, fontFamily: 'var(--font-display)', marginBottom: 16 }}>Ready to Resolve <span className="gradient-text">Disputes</span>?</h2>
              <p style={{ fontSize: 16, color: T.muted, maxWidth: 500, margin: '0 auto 32px', lineHeight: 1.7 }}>Start using the AI-powered MSMED dispute resolution platform. No credit card required for demo mode.</p>
              <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
                <button className="btn-primary" style={{ fontSize: 16, padding: '16px 40px' }} onClick={() => navigate('/app')}>🚀 Launch Platform</button>
                <button className="btn-outline" style={{ fontSize: 16, padding: '16px 40px' }} onClick={() => navigate('/app')}>👤 Try Demo Mode</button>
              </div>
            </div>
          </div>
        </RevealDiv>
      </section>
 
      {/* ── FOOTER ───────────────────────────────────────────────────────── */}
      <footer style={{ padding: '40px 40px 32px', borderTop: '1px solid rgba(30,45,69,0.4)', textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 12 }}>
          <span style={{ fontSize: 20 }}>⚖️</span>
          <span style={{ fontSize: 16, fontWeight: 700 }}><span className="gradient-text-static">Negotiate</span>AI</span>
        </div>
        <p style={{ fontSize: 12, color: T.muted, lineHeight: 1.7, maxWidth: 480, margin: '0 auto 16px' }}>AI-powered MSME Online Dispute Resolution platform compliant with the MSMED Act, 2006.</p>
        <div style={{ fontSize: 11, color: T.muted }}>© 2026 NegotiateAI. All rights reserved.</div>
      </footer>
    </div>
  );
}
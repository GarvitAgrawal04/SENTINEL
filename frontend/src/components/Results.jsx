import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { gsap } from 'gsap';



// ─── Score Arc ────────────────────────────────────────────────────────────────
function ScoreArc({ score, color }) {
  const R = 96, circ = 2 * Math.PI * R;
  const [display, setDisplay] = useState(0);
  const [offset,  setOffset]  = useState(circ);

  useEffect(() => {
    const dur = 2600, start = Date.now();
    const tick = () => {
      const t = Math.min((Date.now() - start) / dur, 1);
      const e = 1 - Math.pow(1 - t, 4);
      setDisplay(Math.round(e * score));
      setOffset(circ * (1 - e * score / 100));
      if (t < 1) requestAnimationFrame(tick);
    };
    setTimeout(() => requestAnimationFrame(tick), 400);
  }, [score]);

  const size = 260;
  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Tick marks */}
        {Array.from({ length: 40 }).map((_, i) => {
          const angle = (i / 40) * Math.PI * 2;
          const r1 = R + 20, r2 = R + 24;
          return <line key={i}
            x1={size/2 + Math.cos(angle)*r1} y1={size/2 + Math.sin(angle)*r1}
            x2={size/2 + Math.cos(angle)*r2} y2={size/2 + Math.sin(angle)*r2}
            stroke={`${color}30`} strokeWidth="1" />;
        })}
        {/* Track */}
        <circle cx={size/2} cy={size/2} r={R} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="12" />
        {/* Progress glow (blurred duplicate) */}
        <circle cx={size/2} cy={size/2} r={R} fill="none" stroke={color} strokeWidth="16"
          strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset}
          style={{ filter: `blur(6px)`, opacity: 0.3 }} />
        {/* Progress */}
        <circle cx={size/2} cy={size/2} r={R} fill="none" stroke={color} strokeWidth="10"
          strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset}
          style={{ filter: `drop-shadow(0 0 12px ${color})` }} />
        {/* Inner decorative ring */}
        <circle cx={size/2} cy={size/2} r={R-22} fill="none" stroke={`${color}12`} strokeWidth="1" />
        <circle cx={size/2} cy={size/2} r={R+28} fill="none" stroke={`${color}08`} strokeWidth="1" strokeDasharray="3 9" />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{
          fontFamily: 'var(--font-display)', fontWeight: 900,
          fontSize: '4.5rem', lineHeight: 1, letterSpacing: '-0.04em',
          color, textShadow: `0 0 60px ${color}80`,
        }}>{display}</div>
        <div style={{
          fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
          letterSpacing: '0.25em', textTransform: 'uppercase',
          color: 'rgba(255,255,255,0.60)', marginTop: '0.5rem',
          textShadow: '0 0 10px rgba(255,255,255,0.2)'
        }}>trust score</div>
      </div>
    </div>
  );
}

// ─── Rule grid S1–S8 ──────────────────────────────────────────────────────────
const RULE_META = {
  S1: { name: 'Zero-Width', desc: 'Invisible Unicode codepoints' },
  S2: { name: 'Hidden HTML', desc: 'HTML comment exfiltration' },
  S3: { name: 'MCP Inject', desc: 'Protocol hijack' },
  S4: { name: 'Override', desc: 'Prompt suppression phrasing' },
  S5: { name: 'Exfiltrate', desc: 'Credential extraction vectors' },
  S6: { name: 'Diff Drift', desc: 'Cross-version delta abuse' },
  S7: { name: 'Encoded', desc: 'Base64/obfuscated payloads' },
  S8: { name: 'Cross-File', desc: 'Context leak across files' },
};
function RuleGrid({ findings }) {
  const fired = new Set(findings?.map(f => f.rule_id) || []);
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '0.5rem' }}>
      {Object.entries(RULE_META).map(([rule, meta]) => {
        const hit = fired.has(rule);
        return (
          <div key={rule} style={{
            padding: '1rem', borderRadius: 12, position: 'relative', overflow: 'hidden',
            background: hit ? 'rgba(255,41,41,0.08)' : 'rgba(255,255,255,0.04)',
            backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)',
            border: `1px solid ${hit ? 'rgba(255,41,41,0.3)' : 'rgba(255,255,255,0.1)'}`,
            boxShadow: hit ? '0 0 20px rgba(255,41,41,0.1)' : '0 4px 12px rgba(0,0,0,0.2)',
            transition: 'all 0.3s',
          }}>
            {hit && <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: 'linear-gradient(90deg, #ff2929, #ff6b6b)', borderRadius: '10px 10px 0 0' }} />}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.85rem', color: hit ? '#ff4444' : 'rgba(255,255,255,0.6)', textShadow: hit ? '0 0 10px rgba(255,41,41,0.4)' : 'none' }}>{rule}</span>
              <span style={{ fontSize: '0.8rem', color: hit ? '#ff4444' : 'rgba(0,255,136,0.6)', textShadow: hit ? '0 0 10px rgba(255,41,41,0.4)' : 'none' }}>{hit ? '✗' : '✓'}</span>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: hit ? 'rgba(255,80,80,0.9)' : 'rgba(255,255,255,0.45)', letterSpacing: '0.05em' }}>{meta.name}</div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Expandable finding ───────────────────────────────────────────────────────
function Finding({ f, accent }) {
  const [open, setOpen] = useState(false);
  const sevColor = { high: '#ff2929', critical: '#ff0000', medium: '#ff8c00', low: '#00d9ff' };
  const c = sevColor[f.severity] || '#ff8c00';
  const sevLabel = { high: 'HIGH', critical: 'CRIT', medium: 'MED', low: 'LOW' }[f.severity] || 'MED';
  return (
    <div onClick={() => setOpen(o => !o)} style={{
      borderRadius: 12, overflow: 'hidden', cursor: 'pointer',
      background: 'rgba(255,255,255,0.02)', border: `1px solid rgba(255,255,255,0.1)`,
      backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)',
      transition: 'border-color 0.2s, box-shadow 0.2s, transform 0.2s',
      boxShadow: open ? `0 0 30px ${c}18` : '0 4px 15px rgba(0,0,0,0.3)',
    }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = `${c}40`; e.currentTarget.style.transform = 'translateY(-2px)'; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)'; e.currentTarget.style.transform = 'none'; }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem 1.25rem' }}>
        <div style={{ width: 4, borderRadius: 2, background: c, boxShadow: `0 0 10px ${c}90`, alignSelf: 'stretch', flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', padding: '0.2rem 0.6rem', borderRadius: 4, background: `${c}18`, color: c, border: `1px solid ${c}30`, fontWeight: 700 }}>{sevLabel}</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', padding: '0.2rem 0.6rem', borderRadius: 4, background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.70)', border: '1px solid rgba(255,255,255,0.1)' }}>{f.rule_id}</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'rgba(255,255,255,0.85)' }}>L{f.line}</span>
          </div>
          <div style={{ fontFamily: 'var(--font-body)', fontSize: '0.95rem', color: 'rgba(255,255,255,0.95)', lineHeight: 1.4 }}>{f.message}</div>
        </div>
        <span style={{ color: 'rgba(255,255,255,0.50)', fontSize: '0.7rem', transition: 'transform 0.2s', transform: open ? 'rotate(180deg)' : 'none', flexShrink: 0 }}>▾</span>
      </div>
      {open && f.snippet && (
        <div style={{ padding: '0 1rem 0.9rem' }}>
          <div style={{ padding: '0.6rem 0.8rem', borderRadius: 8, background: 'rgba(0,0,0,0.6)', border: `1px solid ${c}18`, fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'rgba(255,255,255,0.80)', overflowX: 'auto' }}>
            <span style={{ color: c, opacity: 0.5, marginRight: 8 }}>›</span>{f.snippet}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Results ──────────────────────────────────────────────────────────────────
export default function Results({ result, onShowAgentEye, onReset }) {
  const rootRef = useRef(null);

  const BAND = {
    red:   { label: 'COMPROMISED',    color: '#ff2929', icon: '◉', sub: 'Active threat vectors detected' },
    amber: { label: 'SUSPICIOUS',     color: '#ff8c00', icon: '◎', sub: 'Potential threats detected' },
    green: { label: 'VERIFIED CLEAN', color: '#00ff88', icon: '◇', sub: 'All checks passed' },
  }[result.color_band] || { label: 'UNKNOWN', color: '#fff', icon: '○', sub: '' };

  const highCount = result.findings?.filter(f => ['high','critical'].includes(f.severity)).length || 0;
  const medCount  = result.findings?.filter(f => f.severity === 'medium').length || 0;
  const lowCount  = result.findings?.filter(f => f.severity === 'low').length || 0;
  const hasS1     = result.findings?.some(f => f.rule_id === 'S1');
  const l3        = result.layer3_result;

  const l3Status = !l3
    ? { label: 'Unavailable', note: 'Set GROQ_API_KEY to enable', color: 'rgba(255,255,255,0.55)' }
    : l3.error
    ? { label: 'Layer 3 Error', note: l3.error, color: '#ff8c00' }
    : l3.serves_stated_purpose
    ? { label: 'Legitimate Intent', note: 'Neural analysis confirms purpose matches stated function.', color: '#00ff88' }
    : { label: 'Deceptive Intent', note: 'Neural analysis detected intent diverges from stated purpose.', color: '#ff2929' };

  useEffect(() => {
    if (!rootRef.current) return;
    gsap.fromTo(rootRef.current.querySelectorAll('.r-in'),
      { y: 50, opacity: 0, filter: 'blur(6px)' },
      { y: 0, opacity: 1, filter: 'blur(0px)', stagger: 0.07, duration: 0.9, ease: 'power3.out' }
    );
  }, []);

  return (
    <div ref={rootRef} style={{ minHeight: '100vh', background: 'transparent', cursor: 'none', paddingBottom: '3rem', position: 'relative', zIndex: 1 }}>
      {/* Faint grid */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.02) 1px,transparent 1px)',
        backgroundSize: '60px 60px',
        maskImage: 'radial-gradient(ellipse 70% 80% at 50% 0%, black 20%, transparent 100%)',
      }} />

      <div style={{ position: 'relative', zIndex: 10, maxWidth: 1120, margin: '0 auto', padding: '0 1.5rem' }}>

        {/* Nav strip */}
        <div className="r-in" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1.25rem 0 2.5rem' }}>
          <button onClick={onReset} style={{
            fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.8rem', letterSpacing: '0.2em',
            color: 'rgba(255,255,255,0.90)', background: 'rgba(255,255,255,0.08)',
            backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)',
            border: '1px solid rgba(255,255,255,0.25)', borderRadius: 100,
            padding: '0.6rem 1.4rem', cursor: 'pointer', transition: 'all 0.2s',
            boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
            textShadow: '0 0 10px rgba(255,255,255,0.3)'
          }}
            onMouseEnter={e => { e.target.style.color = '#fff'; e.target.style.background = 'rgba(255,255,255,0.15)'; e.target.style.borderColor = 'rgba(255,255,255,0.4)'; e.target.style.transform = 'translateY(-1px)'; }}
            onMouseLeave={e => { e.target.style.color = 'rgba(255,255,255,0.9)'; e.target.style.background = 'rgba(255,255,255,0.08)'; e.target.style.borderColor = 'rgba(255,255,255,0.25)'; e.target.style.transform = 'none'; }}
          >← SCAN ANOTHER</button>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6rem', color: 'rgba(255,255,255,0.50)', letterSpacing: '0.15em' }}>{result.filename}</span>
        </div>

        {/* ── Verdict hero ── */}
        <div className="r-in" style={{
          borderRadius: 24, padding: '2.5rem',
          background: 'rgba(4,4,10,0.85)', backdropFilter: 'blur(6px)',
          border: `1px solid ${BAND.color}18`,
          boxShadow: `0 0 100px ${BAND.color}10, 0 40px 80px rgba(0,0,0,0.6)`,
          display: 'flex', flexDirection: 'row', gap: '3rem', alignItems: 'center',
          flexWrap: 'wrap', marginBottom: '1.5rem',
        }}>
          <ScoreArc score={result.trust_score} color={BAND.color} />
          <div style={{ flex: 1, minWidth: 200 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.55rem', letterSpacing: '0.4em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.55)', marginBottom: '0.75rem' }}>
              Sentinel Verdict
            </div>
            <div style={{
              fontFamily: 'var(--font-display)', fontWeight: 900,
              fontSize: 'clamp(2rem,5vw,3.5rem)', letterSpacing: '-0.03em',
              color: BAND.color,
              textShadow: `0 0 60px ${BAND.color}60`,
              marginBottom: '0.4rem',
            }}>
              {BAND.icon} {BAND.label}
            </div>
            <div style={{ fontFamily: 'var(--font-body)', fontSize: '0.9rem', color: 'rgba(255,255,255,0.65)', marginBottom: '1.5rem' }}>{BAND.sub}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {highCount > 0 && <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', padding: '0.3rem 0.8rem', borderRadius: 100, background: 'rgba(255,41,41,0.1)', color: '#ff2929', border: '1px solid rgba(255,41,41,0.25)' }}>{highCount} HIGH</span>}
              {medCount  > 0 && <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', padding: '0.3rem 0.8rem', borderRadius: 100, background: 'rgba(255,140,0,0.1)', color: '#ff8c00', border: '1px solid rgba(255,140,0,0.25)' }}>{medCount} MED</span>}
              {lowCount  > 0 && <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', padding: '0.3rem 0.8rem', borderRadius: 100, background: 'rgba(0,217,255,0.1)', color: '#00d9ff', border: '1px solid rgba(0,217,255,0.25)' }}>{lowCount} LOW</span>}
              {!result.findings?.length && <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', padding: '0.3rem 0.8rem', borderRadius: 100, background: 'rgba(0,255,136,0.1)', color: '#00ff88', border: '1px solid rgba(0,255,136,0.25)' }}>✓ Zero findings</span>}
            </div>
          </div>
        </div>

        {/* ── S1–S8 rule breakdown ── */}
        <div className="r-in" style={{ borderRadius: 20, padding: '1.5rem 1.75rem', background: 'rgba(4,4,10,0.75)', backdropFilter: 'blur(6px)', border: '1px solid rgba(255,255,255,0.07)', marginBottom: '1.5rem' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.55rem', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.55)', marginBottom: '1rem' }}>
            Layer 1 · Deterministic Rules S1–S8
          </div>
          <RuleGrid findings={result.findings} />
        </div>

        {/* ── 3 columns ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}
          className="r-in"
        >
          {/* Findings */}
          <div style={{ borderRadius: 20, padding: '1.5rem', background: 'rgba(255,255,255,0.02)', backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.85)' }}>
                Findings · {result.findings?.length || 0}
              </span>
              {hasS1 && (
                <button onClick={onShowAgentEye} style={{
                  fontFamily: 'var(--font-mono)', fontSize: '0.7rem', letterSpacing: '0.1em',
                  padding: '0.4rem 0.8rem', borderRadius: 100, cursor: 'pointer',
                  background: 'rgba(124,58,237,0.15)', color: '#c4b5fd',
                  border: '1px solid rgba(167,139,250,0.4)', transition: 'all 0.2s',
                }}
                  onMouseEnter={e => e.target.style.background = 'rgba(124,58,237,0.25)'}
                  onMouseLeave={e => e.target.style.background = 'rgba(124,58,237,0.12)'}
                >⬡ Eye View</button>
              )}
            </div>
            {result.findings?.length > 0
              ? <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {result.findings.map((f, i) => <Finding key={i} f={f} accent={BAND.color} />)}
                </div>
              : <div style={{ textAlign: 'center', padding: '2rem 0' }}>
                  <div style={{ fontSize: '2.5rem', color: '#00ff88', marginBottom: '0.5rem', textShadow: '0 0 15px rgba(0,255,136,0.6)' }}>◇</div>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color: '#00ff88', marginBottom: '0.25rem' }}>Zero findings</div>
                  <div style={{ fontFamily: 'var(--font-body)', fontSize: '0.8rem', color: 'rgba(255,255,255,0.65)' }}>All 8 rules passed</div>
                </div>
            }
          </div>

          {/* L2 + L3 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ borderRadius: 20, padding: '1.25rem 1.5rem', background: 'rgba(255,255,255,0.02)', backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)', border: '1px solid rgba(255,255,255,0.1)', flex: 1, boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.85)', marginBottom: '0.75rem' }}>Layer 2 · Historical Diff</div>
              <div style={{ fontFamily: 'var(--font-body)', fontSize: '0.9rem', color: 'rgba(255,255,255,0.75)', marginBottom: '0.75rem' }}>Cross-version delta analysis applied.</div>
              {result.findings?.length > 0 && (
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: '#ff8c00' }}>New findings → <strong>−10 penalty</strong></div>
              )}
            </div>

            {/* Flow arrow */}
            <div style={{ display: 'flex', justifyContent: 'center', height: 28 }}>
              <div style={{ width: 1, background: 'linear-gradient(to bottom, rgba(255,255,255,0.2), rgba(0,217,255,0.6))', position: 'relative' }}>
                <div style={{ position: 'absolute', bottom: 0, left: '50%', transform: 'translateX(-50%)', width: 6, height: 6, borderRadius: '50%', background: 'var(--cyan)', boxShadow: '0 0 10px var(--cyan)' }} />
              </div>
            </div>

            <div style={{ borderRadius: 20, padding: '1.25rem 1.5rem', background: 'rgba(255,255,255,0.02)', backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)', border: `1px solid ${l3Status.color}40`, flex: 1, boxShadow: `0 8px 32px ${l3Status.color}15` }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.85)', marginBottom: '0.75rem' }}>Layer 3 · Neural Reasoning</div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.1rem', color: l3Status.color, marginBottom: '0.5rem', textShadow: `0 0 15px ${l3Status.color}50` }}>{l3Status.label}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'rgba(255,255,255,0.85)', lineHeight: 1.6, fontStyle: 'italic' }}>
                {l3?.reasoning ? `"${l3.reasoning.slice(0,120)}…"` : l3Status.note}
              </div>
            </div>
          </div>

          {/* Competitor table */}
          <div style={{ borderRadius: 20, padding: '1.5rem', background: 'rgba(255,255,255,0.02)', backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.85)', marginBottom: '1rem' }}>
              Why Tools Miss This
            </div>
            {[
              { name: 'Snyk', focus: 'Code dependencies', detects: false },
              { name: 'Socket.dev', focus: 'npm behaviour', detects: false },
              { name: 'AgentLinter', focus: 'Doc quality', detects: false },
              { name: 'Semgrep', focus: 'Code patterns', detects: false },
              { name: 'SENTINEL.md', focus: 'Agent instructions', detects: true },
            ].map(({ name, focus, detects }) => (
              <div key={name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.8rem 0', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                <div>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '0.95rem', color: detects ? '#fff' : 'rgba(255,255,255,0.6)' }}>{name}</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'rgba(255,255,255,0.75)', marginTop: 4 }}>{focus}</div>
                </div>
                <div style={{
                  fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.7rem',
                  letterSpacing: '0.15em', padding: '0.3rem 0.7rem', borderRadius: 100,
                  background: detects ? 'rgba(0,255,136,0.1)' : 'rgba(255,41,41,0.1)',
                  color: detects ? '#00ff88' : '#ff4444',
                  border: `1px solid ${detects ? 'rgba(0,255,136,0.3)' : 'rgba(255,41,41,0.3)'}`,
                  textShadow: detects ? '0 0 10px rgba(0,255,136,0.4)' : 'none',
                }}>
                  {detects ? '✓ DETECTS' : '✗ BLIND'}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Score arithmetic ── */}
        <div className="r-in" style={{ borderRadius: 20, padding: '1.5rem 1.75rem', background: 'rgba(255,255,255,0.02)', backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)', border: '1px solid rgba(255,255,255,0.1)', marginBottom: '2.5rem', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.85)', marginBottom: '1rem' }}>Trust Score Arithmetic</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', padding: '0.35rem 0.75rem', borderRadius: 8, background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.60)' }}>100</span>
            {result.findings?.map((f, i) => {
              const pen = f.severity === 'high' || f.severity === 'critical' ? 15 : f.severity === 'medium' ? 10 : 5;
              return (
                <React.Fragment key={i}>
                  <span style={{ color: 'rgba(255,255,255,0.55)', fontFamily: 'var(--font-mono)' }}>−</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', padding: '0.35rem 0.75rem', borderRadius: 8, background: 'rgba(255,41,41,0.1)', color: '#ff2929', border: '1px solid rgba(255,41,41,0.2)' }}>
                    {pen} <span style={{ opacity: 0.5, fontSize: '0.75rem' }}>({f.rule_id})</span>
                  </span>
                </React.Fragment>
              );
            })}
            {result.findings?.length > 0 && (
              <React.Fragment>
                <span style={{ color: 'rgba(255,255,255,0.55)', fontFamily: 'var(--font-mono)' }}>−</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', padding: '0.35rem 0.75rem', borderRadius: 8, background: 'rgba(255,140,0,0.1)', color: '#ff8c00', border: '1px solid rgba(255,140,0,0.2)' }}>10 <span style={{ opacity: 0.5, fontSize: '0.75rem' }}>(L2)</span></span>
              </React.Fragment>
            )}
            <span style={{ color: 'rgba(255,255,255,0.55)', fontFamily: 'var(--font-mono)' }}>=</span>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.2rem', padding: '0.35rem 1rem', borderRadius: 10, background: `${BAND.color}15`, color: BAND.color, border: `1px solid ${BAND.color}30`, boxShadow: `0 0 20px ${BAND.color}25` }}>
              {result.trust_score}
            </span>
          </div>
        </div>

        {/* ── CTAs ── */}
        <div className="r-in" style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <button onClick={onReset} style={{
            fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: '1rem',
            padding: '0.85rem 2.5rem', borderRadius: 100, cursor: 'pointer',
            background: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.95)',
            backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)',
            border: '1px solid rgba(255,255,255,0.3)', transition: 'all 0.2s',
            boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
            textShadow: '0 0 10px rgba(255,255,255,0.2)'
          }}
            onMouseEnter={e => { e.target.style.background = 'rgba(255,255,255,0.18)'; e.target.style.color = '#fff'; e.target.style.borderColor = 'rgba(255,255,255,0.5)'; e.target.style.transform = 'translateY(-2px)'; }}
            onMouseLeave={e => { e.target.style.background = 'rgba(255,255,255,0.1)'; e.target.style.color = 'rgba(255,255,255,0.95)'; e.target.style.borderColor = 'rgba(255,255,255,0.3)'; e.target.style.transform = 'none'; }}
          >Scan Another File</button>
          {hasS1 && (
            <button onClick={onShowAgentEye} style={{
              fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: '0.9rem',
              padding: '0.85rem 2rem', borderRadius: 100, cursor: 'pointer',
              background: 'rgba(124,58,237,0.15)', color: '#a78bfa',
              border: '1px solid rgba(167,139,250,0.35)', transition: 'all 0.2s',
              boxShadow: '0 0 30px rgba(124,58,237,0.15)',
            }}
              onMouseEnter={e => { e.target.style.background = 'rgba(124,58,237,0.28)'; e.target.style.boxShadow = '0 0 50px rgba(124,58,237,0.3)'; }}
              onMouseLeave={e => { e.target.style.background = 'rgba(124,58,237,0.15)'; e.target.style.boxShadow = '0 0 30px rgba(124,58,237,0.15)'; }}
            >⬡ Agent's Eye View</button>
          )}
        </div>
      </div>
    </div>
  );
}

import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { gsap } from 'gsap';



// ─── Auto-scrolling threat ticker ─────────────────────────────────────────────
const TICKER_ITEMS = [
  'S1 · Zero-Width Injection',
  'S2 · Hidden HTML Comment Exfiltration',
  'S3 · MCP Protocol Hijack',
  'S4 · Override Phrasing Attack',
  'S5 · Credential Exfiltration Vector',
  'S6 · Cross-Version Diff Drift',
  'S7 · Base64 Encoded Payload',
  'S8 · Cross-File Context Leak',
  'L3 · Neural Intent Analysis',
];

function Ticker() {
  const trackRef = useRef(null);
  useEffect(() => {
    const el = trackRef.current;
    if (!el) return;
    let x = 0;
    const speed = 0.6;
    let raf;
    const animate = () => {
      x -= speed;
      if (x < -el.scrollWidth / 2) x = 0;
      el.style.transform = `translateX(${x}px)`;
      raf = requestAnimationFrame(animate);
    };
    animate();
    return () => cancelAnimationFrame(raf);
  }, []);

  const repeated = [...TICKER_ITEMS, ...TICKER_ITEMS, ...TICKER_ITEMS];

  return (
    <div className="fixed bottom-0 left-0 right-0 overflow-hidden" style={{
      zIndex: 20, height: 36,
      background: 'rgba(0,0,0,0.8)',
      borderTop: '1px solid rgba(255,41,41,0.15)',
      backdropFilter: 'blur(6px)',
    }}>
      <div ref={trackRef} style={{ display: 'flex', whiteSpace: 'nowrap', willChange: 'transform' }}>
        {repeated.map((item, i) => (
          <span key={i} style={{
            fontFamily: 'var(--font-mono)', fontSize: '0.6rem',
            letterSpacing: '0.2em', textTransform: 'uppercase',
            color: 'rgba(255,41,41,0.5)',
            padding: '0 2.5rem', lineHeight: '36px',
            display: 'inline-block',
          }}>
            <span style={{ color: 'rgba(255,41,41,0.3)', marginRight: '1rem' }}>▶</span>
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

// ─── Tilt card ────────────────────────────────────────────────────────────────
const SCENARIOS = [
  {
    id: 'trapdoor_style_demo.md',
    band: 'red', score: 10,
    label: 'Supply Chain',
    headline: 'TrapDoor',
    sub: 'Zero-Width Hijack',
    desc: 'Invisible Unicode in a real CLAUDE.md. 6 codepoints. Zero rendered characters. The AI reads instructions you literally cannot see.',
    tags: ['S1 · Zero-Width', 'S5 · Exfil', 'L3 Active'],
    accent: '#ff2929',
    level: 'CRITICAL',
  },
  {
    id: 'adversarial_injection_demo.md',
    band: 'red', score: 25,
    label: 'State Actor',
    headline: 'SANDWORM',
    sub: 'Override Injection',
    desc: 'Nation-state grade prompt takeover buried in compliance language. Explicit suppression vectors. Bypasses all existing tools.',
    tags: ['S4 · Override ×3', 'L3 Active'],
    accent: '#ff2929',
    level: 'CRITICAL',
  },
  {
    id: 'kill_shot_2_demo.md',
    band: 'amber', score: 40,
    label: 'APT Group',
    headline: 'MoltX',
    sub: 'Dual-Vector',
    desc: 'Two distinct suppression vectors disguised as system directives. Evades single-pattern scanners by splitting the attack across paragraphs.',
    tags: ['S4 · Override ×2', 'L3 Active'],
    accent: '#ff8c00',
    level: 'HIGH',
  },
  {
    id: 'clean_reference.md',
    band: 'green', score: 100,
    label: 'Production',
    headline: 'CLEAN',
    sub: 'Verified Authentic',
    desc: 'Real CLAUDE.md from a major open-source repository. Zero hidden chars. Zero override phrasing. Pure engineering intent.',
    tags: ['All rules pass', 'L3 ✓ Legit'],
    accent: '#00ff88',
    level: 'NONE',
  },
];

function TiltCard({ s, onSelect }) {
  const cardRef = useRef(null);
  const glowRef = useRef(null);
  const [hovered, setHovered] = useState(false);
  const [scored, setScored]   = useState(0);
  const entered = useRef(false);

  // Count-up on viewport enter
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !entered.current) {
        entered.current = true;
        const dur = 1400, start = Date.now();
        const tick = () => {
          const t = Math.min((Date.now() - start) / dur, 1);
          setScored(Math.round((1 - Math.pow(1-t, 3)) * s.score));
          if (t < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      }
    }, { threshold: 0.3 });
    if (cardRef.current) obs.observe(cardRef.current);
    return () => obs.disconnect();
  }, [s.score]);

  const onMove = (e) => {
    const card = cardRef.current; if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    const rx = ((y - rect.height/2) / rect.height) * -14;
    const ry = ((x - rect.width/2) / rect.width) * 14;
    card.style.transform = `perspective(1000px) rotateX(${rx}deg) rotateY(${ry}deg) translateZ(12px)`;
    if (glowRef.current) glowRef.current.style.background = `radial-gradient(circle at ${x}px ${y}px, ${s.accent}20, transparent 70%)`;
  };
  const onLeave = () => {
    gsap.to(cardRef.current, { transform: 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)', duration: 0.7, ease: 'power3.out', clearProps: 'transform' });
    if (glowRef.current) glowRef.current.style.background = 'transparent';
    setHovered(false);
  };

  const circ = 2 * Math.PI * 42;

  return (
    <div
      ref={cardRef}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      onMouseEnter={() => setHovered(true)}
      onClick={() => onSelect(s.id)}
      style={{
        cursor: 'pointer', borderRadius: 20, position: 'relative',
        boxShadow: hovered ? `0 30px 80px rgba(0,0,0,.7), 0 0 60px ${s.accent}20` : '0 8px 40px rgba(0,0,0,.5)',
        transition: 'box-shadow 0.3s',
      }}
    >
      {/* Gradient border */}
      <div style={{
        position: 'absolute', inset: 0, borderRadius: 20, padding: 1,
        background: hovered
          ? `linear-gradient(135deg, ${s.accent}80, ${s.accent}20, ${s.accent}60)`
          : `linear-gradient(135deg, ${s.accent}30, transparent, ${s.accent}15)`,
        WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
        WebkitMaskComposite: 'xor', maskComposite: 'exclude',
        transition: 'background 0.3s',
      }} />

      <div style={{
        containerType: 'inline-size', textAlign: 'left',
        borderRadius: 20, padding: '2.5rem',
        background: 'rgba(3,3,8,0.9)', backdropFilter: 'blur(6px)',
        border: `1px solid ${s.accent}15`,
        display: 'flex', flexDirection: 'column', gap: '1.25rem',
        height: '100%', position: 'relative', overflow: 'hidden',
      }}>
        {/* Mouse glow */}
        <div ref={glowRef} style={{ position: 'absolute', inset: 0, borderRadius: 20, pointerEvents: 'none', transition: 'background 0.15s' }} />

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
          <div style={{ minWidth: 0, flex: 1, textAlign: 'left' }}>
            <div style={{
              fontFamily: 'var(--font-mono)', fontSize: '0.65rem',
              letterSpacing: '0.35em', textTransform: 'uppercase',
              color: `${s.accent}80`, marginBottom: '0.35rem',
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}>{s.label}</div>
            <div style={{
              fontFamily: 'var(--font-display)', fontWeight: 900,
              fontSize: 'clamp(1rem, 8cqw, 2.2rem)', lineHeight: 1,
              color: 'rgba(255,255,255,0.95)',
              letterSpacing: '-0.03em',
              whiteSpace: 'nowrap',
            }}>{s.headline}</div>
            <div style={{
              fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
              color: `${s.accent}90`, marginTop: '0.4rem',
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}>{s.sub}</div>
          </div>

          {/* Score arc */}
          <div style={{ position: 'relative', width: 96, height: 96, flexShrink: 0 }}>
            <svg width="96" height="96" style={{ transform: 'rotate(-90deg)' }}>
              <circle cx="48" cy="48" r="42" fill="none" stroke={`${s.accent}15`} strokeWidth="6" />
              <circle cx="48" cy="48" r="42" fill="none" stroke={s.accent} strokeWidth="6"
                strokeLinecap="round" strokeDasharray={circ}
                strokeDashoffset={circ * (1 - scored / 100)}
                style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(.16,1,.3,1)', filter: `drop-shadow(0 0 10px ${s.accent}80)` }}
              />
            </svg>
            <div style={{
              position: 'absolute', inset: 0, display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              fontFamily: 'var(--font-mono)', fontWeight: 700,
              fontSize: '1.2rem', color: s.accent,
            }}>{scored}</div>
          </div>
        </div>

        {/* Severity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {s.level !== 'NONE' && (
            <div style={{
              width: 6, height: 6, borderRadius: '50%', background: s.accent,
              boxShadow: `0 0 8px ${s.accent}`, flexShrink: 0,
              animation: s.level === 'CRITICAL' ? 'pulse-ring 1.8s ease-out infinite' : 'none',
            }} />
          )}
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: '0.6rem',
            letterSpacing: '0.25em', textTransform: 'uppercase',
            color: s.accent, opacity: 0.8,
          }}>{s.level}</span>
        </div>

        {/* Description */}
        <p style={{
          fontFamily: 'var(--font-body)', fontSize: '0.95rem',
          color: 'rgba(255,255,255,0.75)', lineHeight: 1.7,
          flex: 1,
        }}>{s.desc}</p>

        {/* Tags */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
          {s.tags.map(t => (
            <span key={t} style={{
              fontFamily: 'var(--font-mono)', fontSize: '0.65rem',
              letterSpacing: '0.15em', textTransform: 'uppercase',
              padding: '0.35rem 0.75rem', borderRadius: 6,
              background: `${s.accent}0e`, color: s.accent,
              border: `1px solid ${s.accent}22`,
            }}>{t}</span>
          ))}
        </div>

        {/* Hover CTA arrow */}
        <div style={{
          position: 'absolute', bottom: 20, right: 20,
          width: 30, height: 30, borderRadius: '50%',
          background: s.accent, display: 'flex', alignItems: 'center', justifyContent: 'center',
          opacity: hovered ? 1 : 0, transform: hovered ? 'scale(1)' : 'scale(0.5)',
          transition: 'opacity 0.25s, transform 0.25s',
          boxShadow: `0 0 20px ${s.accent}90`,
        }}>
          <span style={{ color: '#000', fontWeight: 900, fontSize: '0.8rem' }}>→</span>
        </div>
      </div>
    </div>
  );
}

// ─── Upload zone ──────────────────────────────────────────────────────────────
function UploadZone({ onUpload }) {
  const fileRef = useRef(null);
  const [drag, setDrag] = useState(false);
  const process = f => { const r = new FileReader(); r.onload = e => onUpload(f.name, e.target.result); r.readAsText(f); };
  return (
    <div
      onDragOver={e => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={e => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files[0]; if (f) process(f); }}
      onClick={() => fileRef.current?.click()}
      style={{
        position: 'relative', borderRadius: 24, padding: '4rem 2rem',
        background: drag ? 'rgba(0,217,255,0.05)' : 'rgba(255,255,255,0.02)',
        border: `1px solid ${drag ? 'rgba(0,217,255,0.4)' : 'rgba(255,255,255,0.07)'}`,
        boxShadow: drag ? '0 0 50px rgba(0,217,255,0.12)' : 'none',
        cursor: 'pointer', textAlign: 'center',
        transition: 'all 0.25s',
        backdropFilter: 'blur(6px)',
      }}
    >
      <div style={{
        width: 60, height: 60, borderRadius: '50%', margin: '0 auto 1.5rem',
        background: 'rgba(0,217,255,0.08)', border: '1px solid rgba(0,217,255,0.2)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '1.8rem', color: 'var(--cyan)',
        transition: 'transform 0.25s',
        transform: drag ? 'scale(1.15) translateY(-2px)' : 'scale(1)',
      }}>↑</div>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '1.4rem', color: 'rgba(255,255,255,0.80)', marginBottom: '0.75rem' }}>
        {drag ? 'Release to inspect' : 'Drop your file here'}
      </div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'rgba(255,255,255,0.65)', letterSpacing: '0.2em' }}>
        .md · .json · .yaml · .txt — any agent instruction file
      </div>
      <input ref={fileRef} type="file" style={{ display: 'none' }} accept=".md,.json,.yaml,.yml,.txt"
        onChange={e => { const f = e.target.files[0]; if (f) process(f); }} />
    </div>
  );
}

// ─── Stat counter ─────────────────────────────────────────────────────────────
function Stat({ value, label, color = 'rgba(255,255,255,0.9)' }) {
  const [v, setV] = useState('—');
  const ref = useRef(null);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      obs.disconnect();
      const n = parseFloat(value);
      if (isNaN(n)) { setV(value); return; }
      const isInt = Number.isInteger(n);
      const dur = 1600, start = Date.now();
      const tick = () => {
        const t = Math.min((Date.now()-start)/dur, 1);
        const ease = 1 - Math.pow(1-t, 3);
        setV(isInt ? Math.round(ease * n).toString() : (ease * n).toFixed(1));
        if (t < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }, { threshold: 0.5 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [value]);

  return (
    <div ref={ref} style={{ textAlign: 'center' }}>
      <div style={{
        fontFamily: 'var(--font-display)', fontWeight: 900,
        fontSize: 'clamp(2rem, 4vw, 3.5rem)', letterSpacing: '-0.03em',
        color, textShadow: `0 0 40px ${color}50`, lineHeight: 1,
      }}>{v}</div>
      <div style={{
        fontFamily: 'var(--font-mono)', fontSize: '0.8rem',
        letterSpacing: '0.25em', textTransform: 'uppercase',
        color: 'rgba(255,255,255,0.85)', marginTop: '0.6rem',
        textShadow: '0 0 10px rgba(255,255,255,0.3)',
      }}>{label}</div>
    </div>
  );
}

// ─── Entry ────────────────────────────────────────────────────────────────────
export default function Entry({ onDemoSelect, onFileUpload }) {
  const heroRef  = useRef(null);
  const lineRefs = [useRef(null), useRef(null), useRef(null)];
  const subRef   = useRef(null);

  useEffect(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power4.out' } });
    lineRefs.forEach((ref, i) => {
      if (ref.current) {
        tl.fromTo(ref.current, { y: 100, opacity: 0, filter: 'blur(6px)' },
          { y: 0, opacity: 1, filter: 'blur(0px)', duration: 1.0 }, i * 0.14);
      }
    });
    if (subRef.current) {
      tl.fromTo(subRef.current, { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8 }, 0.4);
    }
  }, []);

  return (
    <div style={{ minHeight: '100vh', cursor: 'none', paddingBottom: 36, position: 'relative' }}>
      {/* Grid lines */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
        backgroundSize: '80px 80px',
        maskImage: 'radial-gradient(ellipse 80% 70% at 50% 50%, black 30%, transparent 100%)',
      }} />

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 10 }}>

        {/* Nav */}
        <nav style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '1.25rem 2rem',
          borderBottom: '1px solid rgba(255,255,255,0.04)',
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.6rem',
            background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 100, padding: '0.4rem 0.9rem',
            backdropFilter: 'blur(6px)',
          }}>
            <div style={{
              width: 22, height: 22, borderRadius: 6, background: 'rgba(0,217,255,0.12)',
              border: '1px solid rgba(0,217,255,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.65rem', color: 'var(--cyan)' }}>S</span>
            </div>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.85rem', color: 'rgba(255,255,255,0.90)' }}>
              SENTINEL.md
            </span>
          </div>
          <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--green)', boxShadow: '0 0 8px var(--green)' }} />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6rem', letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.55)' }}>Engine Live</span>
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6rem', color: 'rgba(255,255,255,0.45)', letterSpacing: '0.2em' }}>NexHack 2.0</span>
          </div>
        </nav>

        {/* Hero headline */}
        <div ref={heroRef} style={{ textAlign: 'center', padding: 'clamp(4rem,8vh,7rem) 2rem 3rem' }}>

          {/* Pill eyebrow */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
            background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 100, padding: '0.4rem 1rem', marginBottom: '2.5rem',
            backdropFilter: 'blur(6px)',
          }}>
            <div style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--cyan)', boxShadow: '0 0 8px var(--cyan)' }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6rem', letterSpacing: '0.3em', textTransform: 'uppercase', color: 'var(--cyan)' }}>
              The Firewall for AI Agent Instructions
            </span>
          </div>

          {/* Line 1: "Your AI reads" — each char floats in a wave */}
          <div style={{ overflow: 'hidden', lineHeight: 0.92, marginBottom: '0.05em' }}>
            <div ref={lineRefs[0]} style={{
              fontFamily: 'var(--font-display)', fontWeight: 900,
              fontSize: 'clamp(2.5rem, 6vw, 5.5rem)',
              letterSpacing: '-0.03em',
              color: 'rgba(255,255,255,0.97)',
              display: 'inline-flex', flexWrap: 'wrap', justifyContent: 'center',
            }}>
              {'Your\u00A0AI\u00A0reads'.split('').map((ch, i) => (
                <span key={i} style={{
                  display: 'inline-block',
                  animation: `float-char ${2.4 + (i % 3) * 0.3}s ease-in-out ${i * 0.055}s infinite`,
                  whiteSpace: 'pre',
                }}>{ch}</span>
              ))}
            </div>
          </div>

          {/* Line 2: "every instruction." — moving shimmer fire gradient */}
          <div style={{ overflow: 'hidden', lineHeight: 0.92, marginBottom: '0.15em' }}>
            <div ref={lineRefs[1]} style={{
              fontFamily: 'var(--font-display)', fontWeight: 900,
              fontSize: 'clamp(2.5rem, 6vw, 5.5rem)',
              letterSpacing: '-0.03em',
              background: 'linear-gradient(90deg, #ff1a1a 0%, #ff4444 15%, #ff8080 30%, #ffcccc 45%, #ff8080 60%, #ff4444 75%, #ff1a1a 100%)',
              backgroundSize: '300% 100%',
              WebkitBackgroundClip: 'text', backgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              animation: 'glow-pulse 3s ease-in-out infinite', willChange: 'filter',
              
            }}>
              every instruction.
            </div>
          </div>

          {/* Line 3: subtitle — slow drift */}
          <div style={{ overflow: 'hidden', lineHeight: 1.1, marginBottom: '1.2em' }}>
            <div ref={lineRefs[2]} style={{
              fontFamily: 'var(--font-display)', fontWeight: 300,
              fontSize: 'clamp(1rem, 2vw, 1.8rem)',
              letterSpacing: '-0.01em',
              color: 'rgba(255,255,255,0.65)',
              animation: 'float-char 5s ease-in-out 0.5s infinite',
            }}>
              Even the ones you can&rsquo;t see.
            </div>
          </div>

          {/* Sub paragraph — glows faintly on hover */}
          <p ref={subRef} style={{
            maxWidth: 520, margin: '2.5rem auto',
            fontFamily: 'var(--font-body)', fontSize: '1rem', lineHeight: 1.8,
            color: 'rgba(255,255,255,0.75)',
            transition: 'color 0.4s',
          }}
            onMouseEnter={e => e.currentTarget.style.color = 'rgba(255,255,255,0.65)'}
            onMouseLeave={e => e.currentTarget.style.color = 'rgba(255,255,255,0.4)'}
          >
            In June 2026, invisible Unicode characters in npm packages silently reprogrammed AI coding agents.
            No malware. No CVE. Just a text file.{' '}
            <em style={{ color: 'rgba(255,100,100,0.6)', fontStyle: 'normal' }}>Every existing scanner missed it completely.</em>
          </p>


          {/* Stats row */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: 'clamp(2rem,6vw,5rem)', margin: '0 auto 5rem', flexWrap: 'wrap' }}>
            <Stat value="100" label="% Detection Recall" color="var(--green)" />
            <Stat value="0" label="False Positives" color="var(--cyan)" />
            <Stat value="3" label="Detection Layers" color="var(--purple)" />
            <Stat value="8" label="Rule Coverage (S1–S8)" color="rgba(255,255,255,0.70)" />
          </div>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', maxWidth: 900, margin: '0 auto 2.5rem' }}>
            <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.05)' }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.85)', whiteSpace: 'nowrap', textShadow: '0 0 10px rgba(255,255,255,0.3)' }}>
              choose a threat scenario
            </span>
            <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.05)' }} />
          </div>

          {/* Scenario cards */}
          <div style={{
            maxWidth: 1600, margin: '0 auto 4rem',
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '1.5rem', padding: '0 1rem',
          }}>
            {SCENARIOS.map(s => <TiltCard key={s.id} s={s} onSelect={onDemoSelect} />)}
          </div>

          {/* Upload */}
          <div style={{ maxWidth: 800, margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '0.75rem' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.85)', textShadow: '0 0 10px rgba(255,255,255,0.3)' }}>
                — or inspect your own file —
              </span>
            </div>
            <UploadZone onUpload={onFileUpload} />
          </div>
        </div>
      </div>

      {/* Scrolling threat ticker */}
      <Ticker />
    </div>
  );
}

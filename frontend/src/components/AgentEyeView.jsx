import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { gsap } from 'gsap';

// ─── Zero-width codepoints — DO NOT MODIFY ────────────────────────────────────
const ZERO_WIDTH = new Map([
  ['\u200b', { name: 'ZERO WIDTH SPACE', hex: '200B', desc: 'Invisible space character. Encodes hidden payload tokens without rendering whitespace. Consumed directly by the AI tokenizer as a real token boundary.' }],
  ['\u200c', { name: 'ZERO WIDTH NON-JOINER', hex: '200C', desc: 'Zero-width formatting character used as payload delimiter or bit-flip encoder. Invisible to all text editors.' }],
  ['\u200d', { name: 'ZERO WIDTH JOINER', hex: '200D', desc: 'Zero-width glyph joiner. Injected into tokenizer context as a hidden control character.' }],
  ['\u200e', { name: 'LEFT-TO-RIGHT MARK', hex: '200E', desc: 'Directional control character. Used for prompt visual spoofing — text reads differently to human vs AI.' }],
  ['\u200f', { name: 'RIGHT-TO-LEFT MARK', hex: '200F', desc: 'Directional control character that inverts terminal display order. Payload hidden by reversal.' }],
  ['\ufeff', { name: 'ZERO WIDTH NO-BREAK SPACE', hex: 'FEFF', desc: 'Byte order mark smuggled mid-sentence to segment instructions into separate tokenizer contexts.' }],
  ['\u2060', { name: 'WORD JOINER', hex: '2060', desc: 'Zero-width word joiner. Separates token boundaries invisibly.' }],
  ['\u2061', { name: 'FUNCTION APPLICATION', hex: '2061', desc: 'Invisible math operator codepoint. Passes through most sanitizers.' }],
  ['\u2062', { name: 'INVISIBLE TIMES', hex: '2062', desc: 'Invisible math multiplication codepoint.' }],
  ['\u2063', { name: 'INVISIBLE SEPARATOR', hex: '2063', desc: 'Invisible punctuation separator codepoint.' }],
  ['\u2064', { name: 'INVISIBLE PLUS', hex: '2064', desc: 'Invisible math addition codepoint.' }],
]);

// ─── Parse a single line into elements ───────────────────────────────────────
function parseLine(line) {
  const elements = [];
  let hasHidden = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (ZERO_WIDTH.has(char)) {
      hasHidden = true;
      elements.push({ type: 'hidden', char, info: ZERO_WIDTH.get(char), key: i });
    } else {
      if (elements.length > 0 && elements[elements.length - 1].type === 'visible') {
        elements[elements.length - 1].text += char;
      } else {
        elements.push({ type: 'visible', text: char, key: i });
      }
    }
  }
  return { elements, hasHidden };
}

// ─── Terminal window chrome ───────────────────────────────────────────────────
function TerminalChrome({ title, accent, children, scrollRef }) {
  return (
    <div className="flex flex-col rounded-xl overflow-hidden h-full"
      style={{ 
        background: 'rgba(255,255,255,0.02)', 
        backdropFilter: 'blur(6px)', 
        WebkitBackdropFilter: 'blur(6px)', 
        border: `1px solid ${accent}40`,
        boxShadow: '0 8px 32px rgba(0,0,0,0.5), inset 0 0 40px rgba(255,255,255,0.02)'
      }}>
      {/* Title bar */}
      <div className="flex items-center gap-2 px-4 py-3 flex-shrink-0"
        style={{ background: 'rgba(255,255,255,0.04)', borderBottom: `1px solid ${accent}30` }}>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full" style={{ background: '#ff5f56' }} />
          <div className="w-2.5 h-2.5 rounded-full" style={{ background: '#ffbd2e' }} />
          <div className="w-2.5 h-2.5 rounded-full" style={{ background: accent }} />
        </div>
        <div className="ml-2 text-xs" style={{ color: `${accent}80`, fontFamily: 'var(--font-mono)' }}>{title}</div>
      </div>
      {/* Content */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4" style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', lineHeight: '1.7' }}>
        {children}
      </div>
    </div>
  );
}

// ─── Inspector panel (slides up on token click) ───────────────────────────────
function Inspector({ selected, onDismiss }) {
  const panelRef = useRef(null);

  useEffect(() => {
    if (selected && panelRef.current) {
      gsap.fromTo(panelRef.current, { y: 80, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4, ease: 'power3.out' });
    }
  }, [selected]);

  if (!selected) return null;

  return (
    <div ref={panelRef} className="fixed bottom-0 left-0 right-0 z-50 px-6 pb-6">
      <div className="max-w-4xl mx-auto rounded-2xl p-6"
        style={{ background: 'rgba(8,5,20,0.8)', border: '1px solid rgba(167,139,250,0.4)', backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)', boxShadow: '0 -20px 80px rgba(124,58,237,0.2), 0 0 40px rgba(124,58,237,0.1)' }}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-xs px-2.5 py-1 rounded font-bold"
                style={{ background: 'rgba(167,139,250,0.2)', color: '#a78bfa', border: '1px solid rgba(167,139,250,0.4)', fontFamily: 'var(--font-mono)' }}>
                U+{selected.info.hex}
              </span>
              <span className="text-base font-bold text-white" style={{ fontFamily: 'var(--font-display)' }}>
                {selected.info.name}
              </span>
              <div className="token-pulse w-2 h-2 rounded-full flex-shrink-0" style={{ background: '#a78bfa' }} />
            </div>
            <p className="text-sm leading-relaxed mb-4" style={{ color: 'rgba(255,255,255,.5)', fontFamily: 'var(--font-body)' }}>
              {selected.info.desc}
            </p>
            <div className="p-3 rounded-lg text-xs" style={{ background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.2)', color: 'rgba(167,139,250,.7)', fontFamily: 'var(--font-mono)' }}>
              <span style={{ color: '#a78bfa', marginRight: 8 }}>›</span>
              This character is <strong style={{ color: '#a78bfa' }}>invisible in every text editor</strong> but is present in the byte stream — the AI tokenizer processes it as a real instruction boundary or modifier.
            </div>
          </div>
          <button onClick={onDismiss}
            className="flex-shrink-0 px-3 py-1.5 rounded-full text-xs cursor-pointer hover:scale-105 transition-transform"
            style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,.4)', fontFamily: 'var(--font-mono)' }}>
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main AgentEyeView ────────────────────────────────────────────────────────
export default function AgentEyeView({ rawText = '', onBack }) {
  const [selected, setSelected] = useState(null);
  const humanScrollRef = useRef(null);
  const agentScrollRef = useRef(null);
  const syncing = useRef(false);
  const containerRef = useRef(null);

  // Parse lines
  const lines = useMemo(() => (rawText ? rawText.split('\n') : []), [rawText]);
  const parsedLines = useMemo(() => lines.map(parseLine), [lines]);

  // Stats
  const totalHidden = useMemo(() => {
    let n = 0;
    for (const char of rawText) { if (ZERO_WIDTH.has(char)) n++; }
    return n;
  }, [rawText]);
  const infectedLines = useMemo(() => parsedLines.filter(p => p.hasHidden).length, [parsedLines]);

  // Synced scroll
  const syncScroll = useCallback((source, target) => {
    if (syncing.current) return;
    syncing.current = true;
    const ratio = source.scrollTop / Math.max(1, source.scrollHeight - source.clientHeight);
    target.scrollTop = ratio * (target.scrollHeight - target.clientHeight);
    requestAnimationFrame(() => { syncing.current = false; });
  }, []);

  useEffect(() => {
    const h = humanScrollRef.current, a = agentScrollRef.current;
    if (!h || !a) return;
    const onHuman = () => syncScroll(h, a);
    const onAgent = () => syncScroll(a, h);
    h.addEventListener('scroll', onHuman);
    a.addEventListener('scroll', onAgent);
    return () => { h.removeEventListener('scroll', onHuman); a.removeEventListener('scroll', onAgent); };
  }, [syncScroll]);

  // Entrance animation
  useEffect(() => {
    if (containerRef.current) {
      gsap.fromTo(containerRef.current.querySelectorAll('.ae-anim'),
        { y: 30, opacity: 0 },
        { y: 0, opacity: 1, stagger: 0.07, duration: 0.7, ease: 'power3.out' }
      );
    }
  }, []);

  return (
    <div ref={containerRef} className="min-h-screen flex flex-col scanlines" style={{ background: 'transparent', cursor: 'none', position: 'relative', zIndex: 1 }}>
      {/* Purple ambient */}
      <div className="fixed inset-0 pointer-events-none" style={{
        background: 'radial-gradient(ellipse 80% 50% at 50% -5%, rgba(124,58,237,0.15), transparent 60%)',
        zIndex: 0,
      }} />

      <div className="relative z-10 flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <div className="ae-anim flex-shrink-0 px-6 py-5 flex items-center justify-between"
          style={{ borderBottom: '1px solid rgba(255,255,255,.05)', backdropFilter: 'blur(6px)' }}>
          <div className="flex items-center gap-6">
            <button onClick={onBack}
              className="liquid-glass flex items-center gap-2 text-sm px-5 py-2.5 rounded-full cursor-pointer hover:scale-[1.03] transition-all"
              style={{ 
                color: 'rgba(255,255,255,0.90)', fontFamily: 'var(--font-mono)', fontWeight: 700, letterSpacing: '0.1em',
                background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.3)',
                boxShadow: '0 4px 15px rgba(0,0,0,0.3)', textShadow: '0 0 10px rgba(255,255,255,0.3)'
              }}>
              ← BACK TO RESULTS
            </button>
            <div>
              <h2 className="text-3xl font-black text-white" style={{ fontFamily: 'var(--font-display)', textShadow: '0 0 15px rgba(255,255,255,0.3)' }}>
                What Your AI Actually Sees
              </h2>
              <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,.5)', fontFamily: 'var(--font-body)' }}>
                Purple tokens are invisible to humans but tokenized by the AI as real instructions.
              </p>
            </div>
          </div>
          {/* Stats */}
          <div className="flex items-center gap-4">
            {[
              { label: 'Hidden Codepoints', value: totalHidden, color: totalHidden > 0 ? '#ff4444' : '#00ff88' },
              { label: 'Infected Lines', value: infectedLines, color: infectedLines > 0 ? '#ff8c00' : '#00ff88' },
              { label: 'Total Lines', value: lines.length, color: 'rgba(255,255,255,.5)' },
            ].map(({ label, value, color }) => (
              <div key={label} className="liquid-glass px-4 py-2 rounded-xl text-center" style={{ background: 'rgba(255,255,255,0.02)', backdropFilter: 'blur(6px)', border: '1px solid rgba(255,255,255,0.1)' }}>
                <div className="text-2xl font-black" style={{ color, fontFamily: 'var(--font-display)', textShadow: `0 0 10px ${color}50` }}>{value}</div>
                <div className="text-[10px] tracking-wider uppercase mt-1" style={{ color: 'rgba(255,255,255,.4)', fontFamily: 'var(--font-mono)' }}>{label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Split panels */}
        <div className="ae-anim flex-1 flex overflow-hidden px-6 py-4 gap-0 min-h-0">
          {/* Human view */}
          <div className="flex-1 min-w-0">
            <TerminalChrome title="human_view.md — what you see" accent="rgba(255,255,255,0.4)" scrollRef={humanScrollRef}>
              {lines.map((line, idx) => {
                const { hasHidden } = parsedLines[idx] || {};
                return (
                  <div key={idx} className="flex gap-3"
                    style={{ background: hasHidden ? 'rgba(255,41,41,0.04)' : 'transparent', borderLeft: hasHidden ? '2px solid rgba(255,41,41,0.3)' : '2px solid transparent', paddingLeft: hasHidden ? 6 : 6 }}>
                    <span className="w-8 text-right flex-shrink-0 select-none" style={{ color: hasHidden ? 'rgba(255,41,41,0.4)' : 'rgba(255,255,255,.12)' }}>{idx + 1}</span>
                    <span style={{ color: 'rgba(255,255,255,.7)', wordBreak: 'break-all' }}>{line || ' '}</span>
                  </div>
                );
              })}
            </TerminalChrome>
          </div>

          {/* VS Divider */}
          <div className="flex flex-col items-center justify-center px-3 flex-shrink-0">
            <div className="flex-1" style={{ width: 1, background: 'linear-gradient(to bottom, transparent, rgba(167,139,250,0.3) 30%, rgba(167,139,250,0.5) 50%, rgba(167,139,250,0.3) 70%, transparent)' }} />
            <div className="px-2 py-1.5 rounded-full text-[9px] font-bold my-2"
              style={{ background: 'rgba(124,58,237,0.2)', color: '#a78bfa', border: '1px solid rgba(167,139,250,0.4)', fontFamily: 'var(--font-mono)' }}>
              VS
            </div>
            <div className="flex-1" style={{ width: 1, background: 'linear-gradient(to bottom, rgba(167,139,250,0.3), transparent)' }} />
          </div>

          {/* Agent view */}
          <div className="flex-1 min-w-0">
            <TerminalChrome title="agent_perspective.md — click tokens to inspect" accent="#a78bfa" scrollRef={agentScrollRef}>
              {lines.map((line, idx) => {
                const { elements, hasHidden } = parsedLines[idx] || { elements: [], hasHidden: false };
                return (
                  <div key={idx} className="flex gap-3"
                    style={{ background: hasHidden ? 'rgba(124,58,237,0.06)' : 'transparent', borderLeft: hasHidden ? '2px solid rgba(167,139,250,0.4)' : '2px solid transparent', paddingLeft: 6 }}>
                    <span className="w-8 text-right flex-shrink-0 select-none" style={{ color: hasHidden ? '#a78bfa' : 'rgba(255,255,255,.12)' }}>{idx + 1}</span>
                    <span className="flex flex-wrap items-center" style={{ wordBreak: 'break-all' }}>
                      {elements.length === 0 ? (
                        <span style={{ color: 'rgba(255,255,255,.7)' }}> </span>
                      ) : elements.map((el) => {
                        if (el.type === 'hidden') {
                          return (
                            <button key={el.key}
                              onClick={() => setSelected({ ...el, lineIdx: idx })}
                              className="token-pulse inline-flex items-center mx-1 px-1.5 py-0.5 rounded text-[11px] font-bold cursor-pointer transition-all hover:scale-110"
                              style={{
                                background: selected?.key === el.key && selected?.lineIdx === idx ? 'rgba(167,139,250,0.5)' : 'rgba(167,139,250,0.2)',
                                border: '1px solid rgba(167,139,250,0.6)',
                                color: '#a78bfa',
                                fontFamily: 'var(--font-mono)',
                                verticalAlign: 'middle',
                              }}>
                              U+{el.info.hex}
                            </button>
                          );
                        }
                        return <span key={el.key} style={{ color: 'rgba(255,255,255,.7)' }}>{el.text}</span>;
                      })}
                    </span>
                  </div>
                );
              })}
            </TerminalChrome>
          </div>
        </div>

        {/* Empty state */}
        {totalHidden === 0 && (
          <div className="ae-anim fixed inset-x-0 bottom-6 flex justify-center z-10 px-6">
            <div className="rounded-2xl px-8 py-5 text-center"
              style={{ background: 'rgba(0,255,136,0.05)', border: '1px solid rgba(0,255,136,0.2)', backdropFilter: 'blur(6px)' }}>
              <div className="text-3xl mb-2 text-glow-green" style={{ color: '#00ff88' }}>◇</div>
              <div className="text-base font-bold mb-1" style={{ color: '#00ff88', fontFamily: 'var(--font-display)' }}>
                Identical Views
              </div>
              <div className="text-sm" style={{ color: 'rgba(255,255,255,.4)', fontFamily: 'var(--font-body)' }}>
                No hidden codepoints detected. Human and agent perspectives are the same.
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Inspector */}
      <Inspector selected={selected} onDismiss={() => setSelected(null)} />
    </div>
  );
}

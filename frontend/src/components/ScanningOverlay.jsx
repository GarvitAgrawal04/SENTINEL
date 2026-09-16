import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { gsap } from 'gsap';

export default function ScanningOverlay({ phase, filename, rawText = '' }) {
  const [logs, setLogs] = useState([]);
  const logsEndRef = useRef(null);

  useEffect(() => {
    // Generate rapid backend logs
    const lines = [
      `[INIT] Analyzing target: ${filename}`,
      '[SYS] Allocating memory buffers for deep scan...',
      '[S1] Checking for zero-width Unicode characters (U+200B, U+200C)...',
      '[S2] Scanning for hidden HTML comment exfiltration vectors...',
      '[S4] Analyzing override phrasing ("Ignore previous instructions")...',
    ];

    let interval;
    let tick = 0;

    const generateNextLog = () => {
      tick++;
      if (tick === 1) return `[FILE_DUMP] Extracting chunks...`;
      if (tick > 1 && tick < 5 && rawText) {
        const start = (tick * 50) % Math.max(1, rawText.length - 100);
        const snippet = rawText.slice(start, start + 80).replace(/\n/g, '\\n');
        return `[BUFFER] 0x${Math.floor(Math.random()*1000).toString(16).toUpperCase()} : "${snippet}"`;
      }
      
      const r = Math.random();
      if (r < 0.2) return `[HEX_DUMP] 0x${Math.floor(Math.random()*16777215).toString(16)} 0x${Math.floor(Math.random()*16777215).toString(16)} 0x${Math.floor(Math.random()*16777215).toString(16)}`;
      if (r < 0.4) return `[LAYER_3] Evaluating neural intent... Context depth: ${Math.floor(Math.random() * 4000)} tokens`;
      if (r < 0.6) return `[S${Math.floor(Math.random()*8)+1}] Pattern match against known adversarial templates...`;
      if (r < 0.8) return `[TELEMETRY] Threat score synthesis in progress. Confidence: ${(Math.random() * 100).toFixed(2)}%`;
      return `[SYSTEM] ${phase || 'Processing data streams...'}`;
    };

    let logCount = 0;
    const addLog = () => {
      if (logCount < lines.length) {
        setLogs(prev => [...prev.slice(-20), { id: Date.now() + Math.random(), text: lines[logCount], color: '#00d9ff' }]);
      } else {
        const text = generateNextLog();
        const color = text.includes('[LAYER_3]') ? '#00ff88' : text.includes('HEX') ? '#7c3aed' : text.includes('BUFFER') ? 'rgba(255,255,255,0.5)' : '#00d9ff';
        setLogs(prev => [...prev.slice(-25), { id: Date.now() + Math.random(), text, color }]);
      }
      logCount++;
      // Randomize speed of logs (fast burst, slow churn)
      interval = setTimeout(addLog, Math.random() * 100 + 50);
    };

    interval = setTimeout(addLog, 100);
    return () => clearTimeout(interval);
  }, [filename, rawText, phase]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'auto' });
  }, [logs]);

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, overflow: 'hidden' }}>
      {/* UI Overlay */}
      <div style={{ position: 'absolute', inset: 0, zIndex: 10, display: 'flex', flexDirection: 'column' }}>
        
        {/* Top bar */}
        <div style={{ padding: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.75)', marginBottom: '0.5rem' }}>
              Target Acquired
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '1.2rem', color: '#fff' }}>
              {filename}
            </div>
          </div>
          
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.75)', marginBottom: '0.5rem' }}>
              Engine Status
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', color: '#ff2929', animation: 'pulse-ring 1s infinite' }}>
              LIVE SCAN
            </div>
          </div>
        </div>

        {/* Center content - Terminal Window */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'stretch', justifyContent: 'center', padding: '2rem' }}>
          <div style={{ 
            width: '100%', maxWidth: 1000, 
            background: 'rgba(5,5,12,0.7)', 
            backdropFilter: 'blur(6px)',
            border: '1px solid rgba(0,217,255,0.15)',
            borderRadius: '16px',
            boxShadow: '0 30px 60px rgba(0,0,0,0.8), inset 0 0 40px rgba(0,217,255,0.05)',
            display: 'flex', flexDirection: 'column',
            overflow: 'hidden', position: 'relative'
          }}>
            {/* Terminal Header */}
            <div style={{ 
              padding: '1rem', borderBottom: '1px solid rgba(0,217,255,0.1)', 
              background: 'rgba(255,255,255,0.02)', display: 'flex', alignItems: 'center', gap: '0.75rem'
            }}>
              <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ff2929' }} />
              <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ff8c00' }} />
              <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#00ff88' }} />
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'rgba(255,255,255,0.65)', marginLeft: '1rem' }}>
                sentinel-core-engine / scan-process
              </div>
            </div>

            {/* Terminal Logs */}
            <div style={{ 
              flex: 1, overflowY: 'auto', padding: '1.5rem', 
              fontFamily: 'var(--font-mono)', fontSize: '0.85rem', lineHeight: 1.6,
              display: 'flex', flexDirection: 'column', justifyContent: 'flex-start'
            }}>
              {logs.map(log => (
                <div key={log.id} style={{ color: log.color, marginBottom: '0.2rem', wordBreak: 'break-all' }}>
                  <span style={{ color: 'rgba(255,255,255,0.55)', marginRight: '0.75rem' }}>{'>'}</span>
                  {log.text}
                </div>
              ))}
              <div ref={logsEndRef} style={{ height: 1 }} />
            </div>
            
            {/* Scanline effect over terminal */}
            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, height: '100%',
              background: `linear-gradient(to bottom, transparent, rgba(0,217,255,0.05), transparent)`,
              animation: 'scan-sweep 2s linear infinite',
              pointerEvents: 'none'
            }} />
          </div>
        </div>

        {/* Bottom indicator */}
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '1.2rem', color: '#fff', letterSpacing: '0.1em' }}>
            {phase} <span className="cursor-blink">▊</span>
          </div>
        </div>
      </div>
    </div>
  );
}

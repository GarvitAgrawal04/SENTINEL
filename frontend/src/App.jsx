import React, { useState, useEffect, useRef } from 'react';
import Intro from './components/Intro';
import Entry from './components/Entry';
import Results from './components/Results';
import AgentEyeView from './components/AgentEyeView';
import ScanningOverlay from './components/ScanningOverlay';
import './index.css';
import GlobalWebGL from './components/GlobalWebGL';

// ─── Custom cursor ────────────────────────────────────────────────────────────
function CustomCursor() {
  const dotRef = useRef(null);
  const ringRef = useRef(null);
  const pos = useRef({ x: 0, y: 0 });
  const ring = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const onMove = (e) => {
      pos.current = { x: e.clientX, y: e.clientY };
      if (dotRef.current) {
        dotRef.current.style.transform = `translate3d(${e.clientX}px, ${e.clientY}px, 0) translate(-50%, -50%)`;
      }
    };
    let rafId;
    const animateRing = () => {
      ring.current.x += (pos.current.x - ring.current.x) * 0.12;
      ring.current.y += (pos.current.y - ring.current.y) * 0.12;
      if (ringRef.current) {
        ringRef.current.style.transform = `translate3d(${ring.current.x}px, ${ring.current.y}px, 0) translate(-50%, -50%)`;
      }
      rafId = requestAnimationFrame(animateRing);
    };
    animateRing();
    window.addEventListener('mousemove', onMove);
    return () => {
      window.removeEventListener('mousemove', onMove);
      cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <>
      <div ref={dotRef} className="custom-cursor-dot" />
      <div ref={ringRef} className="custom-cursor-ring" />
    </>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [appState, setAppState] = useState('intro');
  const [scanResult, setScanResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [rawText, setRawText] = useState('');
  const [loadingPhase, setLoadingPhase] = useState('Initializing...');
  const [scanFilename, setScanFilename] = useState('');
  const [introFading, setIntroFading] = useState(false);
  const [introProgress, setIntroProgress] = useState(0);

  const handleIntroComplete = () => {
    setIntroFading(true);
    setTimeout(() => {
      setAppState('entry');
      setIntroFading(false);
      document.body.style.overflow = '';
    }, 800);
  };

  const fetchRawText = async (filename) => {
    try {
      const res = await fetch(`/samples/${filename}`);
      if (res.ok) return await res.text();
      return '';
    } catch { return ''; }
  };

  const handleDemoSelect = async (filename) => {
    setScanFilename(filename);
    setAppState('loading');
    setLoadingPhase('Parsing agent instruction file...');
    try {
      const [text, res] = await Promise.all([
        fetchRawText(filename),
        fetch(`http://localhost:8000/scan/demo?file=${filename}`)
      ]);
      setRawText(text);
      if (!res.ok) throw new Error(`Backend error: ${res.statusText}`);
      setLoadingPhase('Querying Layer 3 neural reasoning...');
      const data = await res.json();
      setScanResult(data);
      setAppState('results');
    } catch (err) {
      setErrorMessage(err.message || 'Unknown error');
      setAppState('error');
    }
  };

  const handleFileUpload = async (filename, content) => {
    setScanFilename(filename);
    setAppState('loading');
    setLoadingPhase('Parsing agent instruction file...');
    setRawText(content);
    try {
      const formData = new FormData();
      const blob = new Blob([content], { type: 'text/plain' });
      formData.append('file', blob, filename);
      const res = await fetch('http://localhost:8000/scan/file', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) throw new Error(`Backend error: ${res.statusText}`);
      setLoadingPhase('Querying Layer 3 neural reasoning...');
      const data = await res.json();
      setScanResult(data);
      setAppState('results');
    } catch (err) {
      setErrorMessage(err.message || 'Unknown error');
      setAppState('error');
    }
  };

  const handleReset = () => {
    setAppState('entry');
    setScanResult(null);
    setRawText('');
    setErrorMessage('');
    setScanFilename('');
  };

  return (
    <>
      <CustomCursor />
      
      {/* Persistant 3D Background */}
      <GlobalWebGL appState={appState} scrollProgress={introProgress} band={scanResult?.color_band} />

      {/* Cinematic intro — self-managed fixed positioning */}
      {(appState === 'intro' || introFading) && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 9999,
          opacity: introFading ? 0 : 1,
          transition: 'opacity 0.8s ease-out',
          pointerEvents: introFading ? 'none' : 'auto',
        }}>
          <Intro onComplete={handleIntroComplete} onProgress={setIntroProgress} />
        </div>
      )}

      {appState === 'loading' && (
        <ScanningOverlay phase={loadingPhase} filename={scanFilename} rawText={rawText} />
      )}
      {appState === 'error' && (
        <div className="min-h-screen flex items-center justify-center scanlines"
          style={{ background: 'var(--bg)' }}>
          <div className="text-center p-12 liquid-glass rounded-2xl max-w-md">
            <div className="text-7xl mb-6 text-glow-red" style={{ color: 'var(--red)' }}>⚠</div>
            <h2 className="text-2xl font-bold mb-4" style={{ color: 'var(--red)', fontFamily: 'var(--font-display)' }}>
              Scan Failed
            </h2>
            <p className="mb-8 text-sm" style={{ color: 'rgba(255,255,255,0.4)', fontFamily: 'var(--font-mono)' }}>
              {errorMessage}
            </p>
            <button
              onClick={handleReset}
              className="px-8 py-3 rounded-full text-sm font-bold text-black cursor-pointer magnetic"
              style={{ background: 'var(--cyan)', boxShadow: '0 0 30px rgba(0,217,255,0.4)' }}
            >
              Try Again
            </button>
          </div>
        </div>
      )}
      {appState === 'agentEye' && (
        <AgentEyeView rawText={rawText} onBack={() => setAppState('results')} />
      )}
      {appState === 'results' && (
        <Results
          result={scanResult}
          onShowAgentEye={() => setAppState('agentEye')}
          onReset={handleReset}
        />
      )}
      {appState === 'entry' && (
        <Entry onDemoSelect={handleDemoSelect} onFileUpload={handleFileUpload} />
      )}
    </>
  );
}

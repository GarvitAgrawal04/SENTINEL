import React, { useEffect } from 'react';

export default function Intro({ onComplete }) {
  useEffect(() => {
    const handler = (e) => {
      if (e.data && e.data.type === 'KAGE_COMPLETE') {
        onComplete();
      }
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, [onComplete]);

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', background: '#05070a' }}>
      <iframe
        src="/landing-pages/kage.html"
        title="SENTINEL.md Kage"
        style={{
          width: '100%',
          height: '100%',
          border: 'none',
          display: 'block'
        }}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
      
      <button 
        onClick={onComplete}
        style={{
          position: 'fixed', top: 80, right: 130, zIndex: 100,
          background: 'rgba(255,255,255,0.05)',
          border: '1px solid rgba(255,255,255,0.1)',
          color: '#fff',
          padding: '10px 24px',
          borderRadius: '100px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          letterSpacing: '0.2em',
          backdropFilter: 'blur(6px)',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          textTransform: 'uppercase'
        }}
        onMouseOver={e => {
          e.currentTarget.style.background = 'rgba(255,255,255,0.15)';
          e.currentTarget.style.borderColor = 'rgba(255,255,255,0.3)';
        }}
        onMouseOut={e => {
          e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
          e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
        }}
      >
        SKIP SEQ →
      </button>
    </div>
  );
}

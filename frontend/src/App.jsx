import React, { useState } from 'react';
import Entry from './components/Entry';
import Results from './components/Results';
import AgentEyeView from './components/AgentEyeView';
import { Loader2, AlertCircle, XCircle } from 'lucide-react';

export default function App() {
  const [appState, setAppState] = useState('entry'); // entry, loading, error, results, agentEye
  const [scanResult, setScanResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [rawText, setRawText] = useState('');
  const [loadingPhase, setLoadingPhase] = useState('Initializing deterministic scan...');

  const ZERO_WIDTH_REGEX = /[\u200B\u200C\u200D\u200E\u200F\uFEFF\u2060-\u2064]/;

  const fetchRawText = async (filename) => {
    try {
      const res = await fetch(`/samples/${filename}`);
      if (res.ok) {
        return await res.text();
      }
      return '';
    } catch {
      return '';
    }
  };

  const handleDemoSelect = async (filename) => {
    setAppState('loading');
    setLoadingPhase('Running S1-S8 deterministic rules...');
    
    // Concurrently fetch raw text and trigger backend scan
    try {
      const [text, res] = await Promise.all([
        fetchRawText(filename),
        fetch(`http://localhost:8000/scan/demo?file=${filename}`)
      ]);

      setRawText(text);

      if (!res.ok) {
        throw new Error(`Backend error: ${res.statusText}`);
      }
      
      setLoadingPhase('Querying Layer 3 neural model...');
      const data = await res.json();
      
      setScanResult(data);
      setAppState('results');
    } catch (err) {
      setErrorMessage(err.message || 'Unknown error occurred');
      setAppState('error');
    }
  };

  const handleFileUpload = async (filename, content) => {
    setAppState('loading');
    setLoadingPhase('Running S1-S8 deterministic rules...');
    setRawText(content);
    
    try {
      const formData = new FormData();
      const blob = new Blob([content], { type: 'text/plain' });
      formData.append('file', blob, filename);

      const res = await fetch('http://localhost:8000/scan/file', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        throw new Error(`Backend error: ${res.statusText}`);
      }

      setLoadingPhase('Querying Layer 3 neural model...');
      const data = await res.json();
      
      setScanResult(data);
      setAppState('results');
    } catch (err) {
      setErrorMessage(err.message || 'Unknown error occurred');
      setAppState('error');
    }
  };

  const handleReset = () => {
    setScanResult(null);
    setRawText('');
    setAppState('entry');
  };

  return (
    <div className="min-h-screen bg-[#050505] text-[#FAFAFA] font-sans selection:bg-purple-500/30">
      {appState === 'entry' && (
        <Entry onDemoSelect={handleDemoSelect} onFileUpload={handleFileUpload} />
      )}

      {appState === 'loading' && (
        <div className="min-h-screen flex flex-col items-center justify-center gap-6">
          <div className="relative">
            <Loader2 className="w-16 h-16 text-neutral-500 animate-spin" />
            <div className="absolute inset-0 border-t-2 border-white rounded-full animate-spin" style={{ animationDuration: '1.5s' }} />
          </div>
          <h2 className="text-xl font-bold tracking-widest uppercase">Executing Scan</h2>
          <p className="text-neutral-500 font-mono text-sm animate-pulse">{loadingPhase}</p>
        </div>
      )}

      {appState === 'error' && (
        <div className="min-h-screen flex flex-col items-center justify-center gap-6 text-center px-4">
          <XCircle className="w-16 h-16 text-red-500" />
          <h2 className="text-2xl font-bold">Scan Failed</h2>
          <p className="text-neutral-500 max-w-md">{errorMessage}</p>
          <button 
            onClick={handleReset}
            className="mt-4 px-6 py-3 rounded-lg bg-white text-black font-medium hover:bg-neutral-200 transition-colors cursor-pointer"
          >
            Return to Dashboard
          </button>
        </div>
      )}

      {appState === 'results' && scanResult && (
        <Results 
          result={scanResult} 
          hasHidden={ZERO_WIDTH_REGEX.test(rawText)}
          onShowAgentEye={() => setAppState('agentEye')}
          onReset={handleReset}
        />
      )}

      {appState === 'agentEye' && (
        <AgentEyeView 
          rawText={rawText} 
          onBack={() => setAppState('results')}
        />
      )}
    </div>
  );
}

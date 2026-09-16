import React, { useState } from 'react';
import { 
  ArrowLeft, 
  Eye, 
  Bot, 
  User, 
  AlertTriangle, 
  Sparkles, 
  Check, 
  Copy, 
  Download, 
  ShieldCheck, 
  Terminal,
  Layers
} from 'lucide-react';
import { motion } from 'framer-motion';
import { sounds } from './utils/soundEffects';

const ZERO_WIDTH = new Map([
  ['\u200b', { name: 'ZERO WIDTH SPACE', hex: '200B', desc: 'Invisible space character used to encode hidden payload tokens without rendering whitespace.' }],
  ['\u200c', { name: 'ZERO WIDTH NON-JOINER', hex: '200C', desc: 'Zero-width formatting character often used as a payload delimiter or bit-flip encoder.' }],
  ['\u200d', { name: 'ZERO WIDTH JOINER', hex: '200D', desc: 'Zero-width glyph joiner ingested directly into tokenizer context.' }],
  ['\u200e', { name: 'LEFT-TO-RIGHT MARK', hex: '200E', desc: 'Directional control character used for prompt visual spoofing.' }],
  ['\u200f', { name: 'RIGHT-TO-LEFT MARK', hex: '200F', desc: 'Directional control character that inverts terminal display order.' }],
  ['\ufeff', { name: 'ZERO WIDTH NO-BREAK SPACE (BOM)', hex: 'FEFF', desc: 'Byte order mark smuggled mid-sentence to segment instructions.' }],
  ['\u2060', { name: 'WORD JOINER', hex: '2060', desc: 'Zero-width word joiner character.' }],
  ['\u2061', { name: 'FUNCTION APPLICATION', hex: '2061', desc: 'Invisible math operator codepoint.' }],
  ['\u2062', { name: 'INVISIBLE TIMES', hex: '2062', desc: 'Invisible math multiplication codepoint.' }],
  ['\u2063', { name: 'INVISIBLE SEPARATOR', hex: '2063', desc: 'Invisible punctuation separator codepoint.' }],
  ['\u2064', { name: 'INVISIBLE PLUS', hex: '2064', desc: 'Invisible math addition codepoint.' }]
]);

export default function AgentsEyeView({ rawText = '', onBack }) {
  const [selectedCodepoint, setSelectedCodepoint] = useState(null);
  const [copiedClean, setCopiedClean] = useState(false);
  const [isDecontaminated, setIsDecontaminated] = useState(false);

  const lines = rawText ? rawText.split('\n') : [];

  // Count total hidden characters
  let totalHiddenCount = 0;
  for (let char of rawText) {
    if (ZERO_WIDTH.has(char)) totalHiddenCount++;
  }

  // Sanitized text (strip all zero-width characters)
  const getSanitizedText = () => {
    let clean = '';
    for (let char of rawText) {
      if (!ZERO_WIDTH.has(char)) clean += char;
    }
    return clean;
  };

  const handleCopyClean = () => {
    navigator.clipboard.writeText(getSanitizedText());
    setCopiedClean(true);
    sounds.playSuccess();
    setTimeout(() => setCopiedClean(false), 2500);
  };

  const handleDownloadClean = () => {
    sounds.playSuccess();
    const element = document.createElement('a');
    const file = new Blob([getSanitizedText()], { type: 'text/markdown' });
    element.href = URL.createObjectURL(file);
    element.download = 'decontaminated_CLAUDE.md';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const renderAgentCell = (line) => {
    let hasHidden = false;
    const elements = [];
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (ZERO_WIDTH.has(char)) {
        hasHidden = true;
        const info = ZERO_WIDTH.get(char);
        elements.push(
          <button
            key={i}
            onClick={() => {
              sounds.playClick();
              setSelectedCodepoint({ ...info, index: i });
            }}
            className="mx-0.5 px-1.5 py-0.5 rounded bg-supernova hover:bg-supernova-400 text-white font-mono text-[10px] font-bold shadow-glow-threat inline-flex items-center gap-1 cursor-pointer transition-transform hover:scale-110"
            title={`Click to inspect U+${info.hex} (${info.name})`}
          >
            <span>U+{info.hex}</span>
          </button>
        );
      } else {
        elements.push(<span key={i}>{char}</span>);
      }
    }

    return { elements, hasHidden };
  };

  return (
    <div className="min-h-screen w-full bg-obsidian-950 text-white font-sans flex flex-col selection:bg-cyber selection:text-black">
      
      {/* Top Cyber Navigation Bar */}
      <header className="sticky top-0 z-50 bg-obsidian-900/90 backdrop-blur-xl border-b border-white/10 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              sounds.playClick();
              onBack();
            }}
            className="px-4 py-2 rounded-xl glass-panel hover:bg-white/10 text-white font-mono text-xs font-bold transition-all flex items-center gap-2 border border-white/15"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>BACK TO RESULTS</span>
          </button>

          <div className="flex items-center gap-2">
            <Eye className="w-5 h-5 text-supernova-400" />
            <h1 className="text-base font-bold font-mono uppercase tracking-wider text-white">
              Agent's-Eye View // Zero-Width X-Ray
            </h1>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-supernova/20 border border-supernova/40 text-supernova-300 font-mono text-xs font-bold">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>{totalHiddenCount} INVISIBLE CHARACTERS LOCATED</span>
          </div>

          <button
            onClick={handleCopyClean}
            className="px-4 py-2 rounded-xl bg-cyber/15 hover:bg-cyber text-cyber hover:text-obsidian-950 border border-cyber/40 font-mono text-xs font-bold transition-all flex items-center gap-2"
          >
            {copiedClean ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            <span>{copiedClean ? 'CLEAN COPIED' : 'COPY SANITIZED'}</span>
          </button>

          <button
            onClick={handleDownloadClean}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyber to-hologram text-obsidian-950 font-mono text-xs font-bold transition-all flex items-center gap-2 shadow-glow-cyber"
          >
            <Download className="w-4 h-4" />
            <span>DECONTAMINATE & EXPORT</span>
          </button>
        </div>
      </header>

      {/* Main Split-Screen Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col gap-6">
        
        {/* Codepoint Inspector Banner (If selected) */}
        {selectedCodepoint && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-2xl bg-supernova/10 border border-supernova/40 flex items-start justify-between gap-4 font-mono text-xs"
          >
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-supernova flex items-center justify-center text-white font-bold shrink-0">
                U+{selectedCodepoint.hex}
              </div>
              <div>
                <div className="font-bold text-supernova-300 text-sm">{selectedCodepoint.name}</div>
                <p className="text-slate-300 mt-1 leading-relaxed">{selectedCodepoint.desc}</p>
                <div className="text-slate-500 text-[10px] mt-1">Byte Index Offset: char #{selectedCodepoint.index}</div>
              </div>
            </div>
            <button
              onClick={() => setSelectedCodepoint(null)}
              className="text-slate-400 hover:text-white px-2 py-1"
            >
              ✕
            </button>
          </motion.div>
        )}

        {/* Side-by-Side Comparison Panels */}
        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Left Panel: Human Developer View */}
          <div className="flex flex-col rounded-2xl glass-panel border border-white/15 overflow-hidden">
            <div className="px-5 py-3.5 bg-obsidian-900 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2 font-mono text-xs font-bold text-slate-300">
                <User className="w-4 h-4 text-slate-400" />
                <span>HUMAN DEVELOPER VIEW (GITHUB / IDE)</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-white/10 text-slate-400">
                APPEARS INNOCUOUS
              </span>
            </div>

            <div className="flex-1 p-5 overflow-y-auto font-mono text-xs text-slate-300 leading-relaxed bg-obsidian-950/60 divide-y divide-white/5">
              {lines.map((line, idx) => (
                <div key={idx} className="py-1.5 flex items-start gap-4">
                  <span className="text-slate-600 select-none w-6 text-right shrink-0">{idx + 1}</span>
                  <span className="whitespace-pre-wrap break-all">{line || ' '}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right Panel: AI Agent's Internal Token Representation */}
          <div className="flex flex-col rounded-2xl glass-panel border border-supernova/40 overflow-hidden shadow-glow-threat/20">
            <div className="px-5 py-3.5 bg-obsidian-900 border-b border-supernova/30 flex items-center justify-between">
              <div className="flex items-center gap-2 font-mono text-xs font-bold text-supernova-300">
                <Bot className="w-4 h-4 text-supernova" />
                <span>SENTINEL X-RAY (TOKEN STREAM INGESTED)</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-supernova text-white font-bold animate-pulse">
                STEGANOGRAPHY EXPOSED
              </span>
            </div>

            <div className="flex-1 p-5 overflow-y-auto font-mono text-xs text-slate-200 leading-relaxed bg-obsidian-950/60 divide-y divide-white/5">
              {lines.map((line, idx) => {
                const { elements, hasHidden } = renderAgentCell(line);
                return (
                  <div key={idx} className={`py-1.5 flex items-start gap-4 ${hasHidden ? 'bg-supernova/5' : ''}`}>
                    <span className={`select-none w-6 text-right shrink-0 ${hasHidden ? 'text-supernova font-bold' : 'text-slate-600'}`}>
                      {idx + 1}
                    </span>
                    <div className="whitespace-pre-wrap break-all flex-1">
                      {elements}
                      {hasHidden && (
                        <span className="text-supernova-400 font-bold text-[10px] ml-2 animate-pulse">
                          ← [EXPLOIT EMBEDDED]
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>

        {/* Bottom Legend */}
        <div className="p-4 rounded-xl glass-panel border border-white/10 flex flex-wrap items-center justify-between gap-4 font-mono text-xs text-slate-400">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-supernova"></span>
              <span className="text-white">U+XXXX Badges</span>
              <span>= Hidden zero-width steganographic payload</span>
            </div>
          </div>
          <div>
            Click any red <code className="text-supernova">U+XXXX</code> badge above to inspect codepoint metadata.
          </div>
        </div>

      </main>
    </div>
  );
}

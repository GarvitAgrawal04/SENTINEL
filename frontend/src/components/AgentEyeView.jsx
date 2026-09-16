import React, { useState } from 'react';
import { ArrowLeft, Eye, Bot, User, AlertTriangle } from 'lucide-react';

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

export default function AgentEyeView({ rawText = '', onBack }) {
  const [selectedCodepoint, setSelectedCodepoint] = useState(null);
  const lines = rawText ? rawText.split('\n') : [];

  let totalHiddenCount = 0;
  for (let char of rawText) {
    if (ZERO_WIDTH.has(char)) totalHiddenCount++;
  }

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
            onClick={() => setSelectedCodepoint({ ...info, index: i })}
            className="mx-[1px] px-1 py-[1px] rounded bg-purple-500/20 hover:bg-purple-500/40 border border-purple-500 text-purple-300 font-mono text-[10px] font-bold cursor-pointer transition-colors"
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
    <div className="w-full max-w-7xl mx-auto px-6 py-12 flex flex-col gap-6">
      <header className="flex items-center justify-between pb-6 border-b border-neutral-800">
        <div className="flex items-center gap-6">
          <button
            onClick={onBack}
            className="px-4 py-2 rounded-lg bg-neutral-900 hover:bg-neutral-800 text-white text-sm font-medium transition-colors flex items-center gap-2 cursor-pointer border border-neutral-800"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Verdict</span>
          </button>

          <div className="flex items-center gap-3">
            <Eye className="w-5 h-5 text-purple-400" />
            <h1 className="text-xl font-bold tracking-tight text-white">X-Ray Vision: Hidden Payload Revealed</h1>
          </div>
        </div>

        <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 font-mono text-sm font-medium">
          <AlertTriangle className="w-4 h-4" />
          <span>{totalHiddenCount} Invisible Characters Extracted</span>
        </div>
      </header>

      {selectedCodepoint && (
        <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-start justify-between">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400 font-mono font-bold">
              U+{selectedCodepoint.hex}
            </div>
            <div>
              <div className="font-bold text-white text-base">{selectedCodepoint.name}</div>
              <p className="text-neutral-400 mt-1">{selectedCodepoint.desc}</p>
              <div className="text-neutral-500 font-mono text-xs mt-2">Byte Index Offset: #{selectedCodepoint.index}</div>
            </div>
          </div>
          <button onClick={() => setSelectedCodepoint(null)} className="text-neutral-500 hover:text-white p-2">✕</button>
        </div>
      )}

      {/* Side-by-Side Comparison Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-4">
        
        {/* Left Panel: Human Developer View */}
        <div className="flex flex-col rounded-xl border border-neutral-800 overflow-hidden bg-[#0a0a0a]">
          <div className="px-5 py-4 bg-[#111] border-b border-neutral-800 flex items-center justify-between">
            <div className="flex items-center gap-2 font-medium text-sm text-neutral-300">
              <User className="w-4 h-4 text-neutral-500" />
              <span>Human Editor View (VS Code / GitHub)</span>
            </div>
            <span className="px-2 py-1 rounded text-[10px] font-mono font-bold uppercase bg-neutral-800 text-neutral-400">
              Appears Normal
            </span>
          </div>
          <div className="flex-1 p-5 overflow-y-auto font-mono text-sm text-neutral-400 leading-relaxed bg-[#0a0a0a] border-t-4 border-transparent">
            {lines.map((line, idx) => (
              <div key={idx} className="flex items-start gap-4 py-1 group">
                <span className="text-neutral-600 select-none w-8 text-right shrink-0 font-mono text-xs mt-[2px]">{idx + 1}</span>
                <span className="whitespace-pre-wrap break-all">{line || ' '}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right Panel: AI Agent's Internal Token Representation */}
        <div className="flex flex-col rounded-xl border border-purple-500/30 overflow-hidden bg-[#0a0a0a] shadow-[0_0_30px_rgba(168,85,247,0.05)]">
          <div className="px-5 py-4 bg-purple-500/10 border-b border-purple-500/30 flex items-center justify-between">
            <div className="flex items-center gap-2 font-medium text-sm text-purple-300">
              <Bot className="w-4 h-4 text-purple-400" />
              <span>Machine Parser (Token Stream)</span>
            </div>
            <span className="px-2 py-1 rounded text-[10px] font-mono font-bold uppercase bg-purple-500 text-white animate-pulse">
              Steganography Exposed
            </span>
          </div>
          <div className="flex-1 p-5 overflow-y-auto font-mono text-sm text-neutral-300 leading-relaxed bg-[#0a0a0a] border-t-4 border-transparent">
            {lines.map((line, idx) => {
              const { elements, hasHidden } = renderAgentCell(line);
              return (
                <div key={idx} className={`flex items-start gap-4 py-1 rounded ${hasHidden ? 'bg-purple-500/10 -mx-2 px-2' : ''}`}>
                  <span className={`select-none w-8 text-right shrink-0 font-mono text-xs mt-[2px] ${hasHidden ? 'text-purple-400 font-bold' : 'text-neutral-600'}`}>
                    {idx + 1}
                  </span>
                  <div className="whitespace-pre-wrap break-all flex-1">
                    {elements}
                    {hasHidden && (
                      <span className="text-purple-400 font-bold text-[10px] ml-2 uppercase">
                        ← [HIDDEN PAYLOAD]
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

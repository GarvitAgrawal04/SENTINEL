import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, ShieldAlert, ShieldCheck, Activity, Terminal, Eye, AlertTriangle, CheckCircle2, Bot, Info } from 'lucide-react';

export default function Results({ result, hasHidden, onShowAgentEye, onReset }) {
  const isClean = result.color_band === 'green';
  const isCompromised = result.color_band === 'red' || (result.findings && result.findings.length > 0);
  
  const highCount = result.findings?.filter(f => f.severity === 'high' || f.severity === 'critical').length || 0;
  const mediumCount = result.findings?.filter(f => f.severity === 'medium').length || 0;
  const lowCount = result.findings?.filter(f => f.severity === 'low').length || 0;

  const [expandedFinding, setExpandedFinding] = useState(null);

  const getStatusColor = () => {
    if (result.color_band === 'red') return 'text-red-500 border-red-500/30 bg-red-500/10 shadow-[0_0_40px_rgba(239,68,68,0.15)]';
    if (result.color_band === 'amber') return 'text-orange-500 border-orange-500/30 bg-orange-500/10 shadow-[0_0_40px_rgba(249,115,22,0.15)]';
    return 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10 shadow-[0_0_40px_rgba(16,185,129,0.15)]';
  };

  const getLayer3Status = () => {
    if (!result.layer3_result) return { text: 'Unavailable', color: 'text-neutral-500 bg-neutral-900 border-neutral-800' };
    if (result.layer3_result.error) return { text: 'Error', color: 'text-orange-500 bg-orange-500/10 border-orange-500/30' };
    if (result.layer3_result.serves_stated_purpose) return { text: 'Verified Fine', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' };
    return { text: 'Deceptive Intent Detected', color: 'text-red-400 bg-red-500/10 border-red-500/30' };
  };

  const l3Status = getLayer3Status();

  return (
    <div className="w-full max-w-7xl mx-auto px-6 py-12 flex flex-col gap-8">
      {/* Header */}
      <header className="flex items-center justify-between">
        <button
          onClick={onReset}
          className="px-4 py-2 rounded-lg bg-neutral-900 hover:bg-neutral-800 text-white text-sm font-medium transition-colors flex items-center gap-2 cursor-pointer border border-neutral-800"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Scan Another File</span>
        </button>
        <div className="font-mono text-sm text-neutral-500">
          Target: <span className="text-white">{result.filename || 'unknown'}</span>
        </div>
      </header>

      {/* Top Section: Central Verdict & Linter Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Central Verdict (Takes up 5 cols) */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`lg:col-span-5 flex flex-col items-center justify-center p-12 rounded-2xl border ${getStatusColor()}`}
        >
          <div className="text-sm font-mono tracking-widest uppercase mb-4 opacity-80">Final Trust Score</div>
          <div className="text-8xl font-black tracking-tighter mb-6">{result.trust_score}</div>
          <div className="flex items-center gap-2 text-2xl font-bold uppercase tracking-wide">
            {result.color_band === 'green' ? <ShieldCheck className="w-8 h-8" /> : <ShieldAlert className="w-8 h-8" />}
            {result.color_band === 'red' ? 'Compromised' : result.color_band === 'amber' ? 'Suspicious' : 'Verified Clean'}
          </div>
        </motion.div>

        {/* Two-Tool Comparison (Takes up 7 cols) */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-7 flex flex-col rounded-2xl border border-neutral-800 overflow-hidden bg-[#0a0a0a]"
        >
          <div className="px-6 py-4 bg-[#111] border-b border-neutral-800">
            <h2 className="text-sm font-mono tracking-widest text-neutral-400 uppercase">Detection Discrepancy</h2>
          </div>
          <div className="flex-1 grid grid-cols-2 divide-x divide-neutral-800">
            {/* Standard Tool */}
            <div className="p-8 flex flex-col items-center justify-center text-center">
              <CheckCircle2 className="w-12 h-12 text-neutral-600 mb-4" />
              <h3 className="text-lg font-medium text-neutral-300 mb-2">Standard Syntax Linter</h3>
              <p className="text-sm text-neutral-500">
                0 Syntax Errors.<br/>Valid JSON/Markdown.<br/>Passes all standard CI checks.
              </p>
            </div>
            {/* Sentinel Tool */}
            <div className={`p-8 flex flex-col items-center justify-center text-center ${isCompromised ? 'bg-red-500/5' : 'bg-emerald-500/5'}`}>
              {isCompromised ? <AlertTriangle className="w-12 h-12 text-red-500 mb-4" /> : <ShieldCheck className="w-12 h-12 text-emerald-500 mb-4" />}
              <h3 className={`text-lg font-medium mb-2 ${isCompromised ? 'text-red-400' : 'text-emerald-400'}`}>Sentinel Deep Scan</h3>
              <p className={`text-sm ${isCompromised ? 'text-red-500/80' : 'text-emerald-500/80'}`}>
                {isCompromised ? `${result.findings?.length} adversarial payloads extracted.` : `0 hidden payloads or overrides.`}
                <br/>Semantic intent verified.
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Col: Deterministic Findings */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-5 h-5 text-neutral-400" />
              <h2 className="text-xl font-bold text-white">Rule Engine Findings</h2>
            </div>
            
            {/* Severity Bar Visualization */}
            <div className="flex items-center gap-1 h-6 bg-neutral-900 rounded p-1">
              <div className="text-[10px] font-mono text-neutral-500 mr-2">SEVERITY:</div>
              {highCount > 0 && <div className="h-full bg-red-500 rounded-sm px-1.5 flex items-center justify-center text-[10px] font-bold text-white" title={`${highCount} High/Critical`}>{highCount}</div>}
              {mediumCount > 0 && <div className="h-full bg-orange-500 rounded-sm px-1.5 flex items-center justify-center text-[10px] font-bold text-white" title={`${mediumCount} Medium`}>{mediumCount}</div>}
              {lowCount > 0 && <div className="h-full bg-yellow-500 rounded-sm px-1.5 flex items-center justify-center text-[10px] font-bold text-white" title={`${lowCount} Low`}>{lowCount}</div>}
              {result.findings?.length === 0 && <div className="h-full bg-emerald-500 rounded-sm px-2 flex items-center justify-center text-[10px] font-bold text-white">0</div>}
            </div>
          </div>

          <div className="flex flex-col gap-3">
            {result.findings && result.findings.length > 0 ? (
              result.findings.map((f, i) => (
                <div key={i} className="rounded-xl border border-neutral-800 bg-[#111] overflow-hidden">
                  <div 
                    className="p-4 flex items-center justify-between cursor-pointer hover:bg-[#151515] transition-colors"
                    onClick={() => setExpandedFinding(expandedFinding === i ? null : i)}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${f.severity === 'high' || f.severity === 'critical' ? 'bg-red-500' : f.severity === 'medium' ? 'bg-orange-500' : 'bg-yellow-500'}`} />
                      <div className="font-mono text-sm text-white">[{f.rule_id}] {f.message || f.name}</div>
                    </div>
                    <div className="text-xs text-neutral-500 font-mono">
                      Line {f.line}
                    </div>
                  </div>
                  <AnimatePresence>
                    {expandedFinding === i && (
                      <motion.div 
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t border-neutral-800 bg-[#0a0a0a]"
                      >
                        <div className="p-4 font-mono text-xs text-neutral-400">
                          <div className="mb-2 text-neutral-500">Evidence Snippet:</div>
                          <div className="p-3 bg-black rounded border border-neutral-800 break-all whitespace-pre-wrap">
                            {f.snippet || f.description || "No snippet available."}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))
            ) : (
              <div className="p-8 rounded-xl border border-emerald-500/20 bg-emerald-500/5 flex flex-col items-center justify-center text-center h-[200px]">
                <ShieldCheck className="w-10 h-10 text-emerald-500 mb-3" />
                <h3 className="text-emerald-400 font-medium mb-1">0 Signatures Detected</h3>
                <p className="text-sm text-emerald-500/60">No adversarial patterns, steganography, or overrides found.</p>
              </div>
            )}
          </div>

          {/* Invisible Attack Centerpiece Button */}
          {hasHidden && (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onShowAgentEye}
              className="mt-4 w-full p-4 rounded-xl border border-purple-500 bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 font-bold tracking-widest uppercase flex items-center justify-center gap-3 transition-colors shadow-[0_0_30px_rgba(168,85,247,0.2)] cursor-pointer"
            >
              <Eye className="w-5 h-5" />
              <span>X-Ray Vision: Reveal Invisible Payload</span>
            </motion.button>
          )}
        </div>

        {/* Right Col: Layer 3 Neural Reasoning */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-neutral-400" />
            <h2 className="text-xl font-bold text-white">Layer 3: Neural Reasoning</h2>
          </div>

          <div className={`p-6 rounded-xl border ${l3Status.color} h-full flex flex-col font-serif`}>
            {result.layer3_result ? (
              <>
                <div className="flex items-center justify-between mb-6 pb-4 border-b border-current/20">
                  <div className="font-sans text-sm font-bold uppercase tracking-wider">
                    Model Verdict: <span className="underline decoration-2 underline-offset-4">{l3Status.text}</span>
                  </div>
                  <div className="font-sans text-xs bg-current/10 px-2 py-1 rounded">
                    Confidence: {result.layer3_result.confidence}
                  </div>
                </div>

                <div className="mb-4">
                  <div className="font-sans text-xs font-bold uppercase mb-1 opacity-60 tracking-wider">Inferred Instruction Summary</div>
                  <p className="text-[15px] leading-relaxed italic">{result.layer3_result.agent_instruction_summary || "None provided"}</p>
                </div>

                <div className="flex-1">
                  <div className="font-sans text-xs font-bold uppercase mb-1 opacity-60 tracking-wider">Reasoning</div>
                  <p className="text-[15px] leading-relaxed">{result.layer3_result.explanation || "No explanation provided by the model."}</p>
                </div>
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center opacity-60">
                <Info className="w-8 h-8 mb-4" />
                <h3 className="font-sans font-bold text-lg mb-2">Layer 3 Unavailable</h3>
                <p className="text-sm max-w-[250px]">The neural reasoning engine did not execute or no API key is configured.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

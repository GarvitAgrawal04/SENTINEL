import React, { useRef } from 'react';
import { motion } from 'framer-motion';
import { Shield, Upload, FileCode, Search, Activity, Zap, Server } from 'lucide-react';

const DEMOS = [
  {
    id: 'trapdoor_style_demo.md',
    title: 'Zero-Width Steganography',
    desc: 'Invisible characters hiding instructions.',
    icon: <Search className="w-5 h-5 text-purple-400" />
  },
  {
    id: 'adversarial_injection_demo.md',
    title: 'Adversarial Injection',
    desc: 'Prompt injection attempting to hijack agent goals.',
    icon: <Zap className="w-5 h-5 text-red-400" />
  },
  {
    id: 'kill_shot_2_demo.md',
    title: 'Compliance Override',
    desc: 'System-level directive to suppress output.',
    icon: <Activity className="w-5 h-5 text-orange-400" />
  },
  {
    id: 'clean_reference.md',
    title: 'Verified Clean Config',
    desc: 'Standard clean agent configuration.',
    icon: <Shield className="w-5 h-5 text-emerald-400" />
  }
];

export default function Entry({ onDemoSelect, onFileUpload }) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        onFileUpload(file.name, ev.target.result);
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto px-6 py-24 flex flex-col items-center">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-20"
      >
        <div className="flex items-center justify-center gap-3 mb-6">
          <Server className="w-8 h-8 text-neutral-400" />
          <h1 className="text-4xl font-bold tracking-tight text-white uppercase">Sentinel</h1>
        </div>
        <p className="text-xl text-neutral-400 max-w-2xl font-light">
          The firewall for AI coding agents. Inspect instructions for invisible payloads, compliance overrides, and adversarial injections before execution.
        </p>
      </motion.div>

      <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-16">
        {/* Left Side: 1-Click Demos */}
        <div className="flex flex-col gap-6">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-blue-500" />
            <h2 className="text-sm font-mono tracking-widest text-neutral-500 uppercase">Pre-Verified Demos</h2>
          </div>
          <div className="grid grid-cols-1 gap-4">
            {DEMOS.map((demo) => (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                key={demo.id}
                onClick={() => onDemoSelect(demo.id)}
                className="flex items-start gap-4 p-5 text-left rounded-xl bg-[#111] hover:bg-[#1A1A1A] border border-neutral-800 hover:border-neutral-700 transition-colors cursor-pointer"
              >
                <div className="mt-1 p-2 rounded-lg bg-black border border-neutral-800">
                  {demo.icon}
                </div>
                <div>
                  <h3 className="text-white font-medium mb-1">{demo.title}</h3>
                  <p className="text-sm text-neutral-500">{demo.desc}</p>
                </div>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Right Side: Manual Upload */}
        <div className="flex flex-col gap-6">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-neutral-600" />
            <h2 className="text-sm font-mono tracking-widest text-neutral-500 uppercase">Custom Inspection</h2>
          </div>
          
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex-1 flex flex-col items-center justify-center gap-4 p-12 rounded-xl bg-[#0a0a0a] border-2 border-dashed border-neutral-800 hover:border-neutral-600 transition-colors group cursor-pointer"
          >
            <div className="p-4 rounded-full bg-neutral-900 group-hover:bg-neutral-800 transition-colors">
              <Upload className="w-8 h-8 text-neutral-400 group-hover:text-white" />
            </div>
            <div className="text-center">
              <h3 className="text-white font-medium mb-2">Upload Configuration</h3>
              <p className="text-sm text-neutral-500 max-w-[250px]">
                Drop any .md, .json, or .yaml file to scan for adversarial patterns.
              </p>
            </div>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept=".md,.json,.yaml,.yml,.txt" 
              onChange={handleFileChange}
            />
          </button>
        </div>
      </div>
    </div>
  );
}

import React from "react";
import { X, Cpu, ShieldCheck, Zap, Activity } from "lucide-react";

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AboutModal: React.FC<AboutModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl bg-darkSurface border border-white/10 rounded-2xl shadow-2xl overflow-hidden text-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-white/[0.02]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">How CodeLens Engine Works</h3>
              <p className="text-xs text-slate-400">Offline, deterministic static code analysis architecture</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto text-sm">
          <div>
            <h4 className="text-white font-semibold mb-2 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              100% Deterministic & Local
            </h4>
            <p className="text-slate-300 leading-relaxed text-xs sm:text-sm">
              CodeLens is <strong>NOT</strong> an LLM wrapper. All core analysis is executed on your local machine using
              Python’s native <code className="text-indigo-300 bg-white/5 px-1 py-0.5 rounded">ast</code> module and the
              custom 28-rule inspection engine, supplemented by Radon for Cyclomatic Complexity and Maintainability Index.
              No API keys or internet connection are required.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-white/[0.03] border border-white/5 p-3.5 rounded-xl">
              <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" /> 1. AST Parsing
              </div>
              <p className="text-xs text-slate-400">
                Traverses syntax trees, calculating nesting depth, cognitive complexity, and token patterns.
              </p>
            </div>
            <div className="bg-white/[0.03] border border-white/5 p-3.5 rounded-xl">
              <div className="text-xs font-bold text-violet-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5" /> 2. Rule Registry
              </div>
              <p className="text-xs text-slate-400">
                28 modular rules for Security, Bugs, and Maintainability with normalized penalty scoring.
              </p>
            </div>
            <div className="bg-white/[0.03] border border-white/5 p-3.5 rounded-xl">
              <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5" /> 3. Template Fixes
              </div>
              <p className="text-xs text-slate-400">
                Line/column text edits that preserve your comments and validate syntax before committing.
              </p>
            </div>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-2 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              Smart Scoring Formula
            </h4>
            <div className="bg-black/40 border border-white/5 rounded-xl p-3 font-mono text-xs text-indigo-200">
              Score = clamp(100 - (Σ capped_issue_penalties + complexity_penalty), 0, 100)
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Penalties: Critical (15 pts), High (8 pts), Medium (4 pts), Low (1.5 pts). Each rule is capped at 30 pts
              to prevent single recurring violations from zeroing out scores.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-white/10 bg-white/[0.02] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};

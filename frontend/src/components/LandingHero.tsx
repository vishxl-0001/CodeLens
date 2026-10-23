import React from "react";
import { motion } from "framer-motion";
import { ShieldCheck, Activity, Wrench, ArrowDown, Sparkles, Terminal } from "lucide-react";
import { useStore } from "../store/useStore";
import { getSamples, analyzeCode } from "../api/client";
import toast from "react-hot-toast";

interface LandingHeroProps {
  onStart: () => void;
}

export const LandingHero: React.FC<LandingHeroProps> = ({ onStart }) => {
  const { setCode, setFilename, setResult, setLoading, setBackendOffline } = useStore();

  const handleTrySample = async () => {
    onStart();
    try {
      const samples = await getSamples();
      const terribleSample = samples.find((s) => s.id === "terrible") || samples[0];
      if (terribleSample) {
        setCode(terribleSample.code);
        setFilename(terribleSample.name);
        setLoading(true);
        const res = await analyzeCode(terribleSample.code, terribleSample.name);
        setResult(res);
        setLoading(false);
        toast.success(`Loaded and analyzed '${terribleSample.name}'`);
      }
    } catch {
      setLoading(false);
      setBackendOffline(true);
      toast.error("Could not load sample from backend.");
    }
  };

  return (
    <section className="relative overflow-hidden pt-12 pb-20 border-b border-white/5 bg-gradient-to-b from-darkBg via-darkSurface/50 to-darkBg">
      {/* Background Aurora Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-gradient-to-tr from-indigo-600/15 via-violet-600/10 to-cyan-500/15 rounded-full blur-[100px] pointer-events-none" />

      {/* Floating decorative snippet chips */}
      <motion.div
        initial={{ opacity: 0, x: -40 }}
        animate={{ opacity: 0.6, x: 0 }}
        transition={{ duration: 1, delay: 0.2 }}
        className="hidden xl:flex absolute top-16 left-12 items-center gap-2 px-3 py-1.5 rounded-xl bg-white/[0.03] border border-white/10 text-xs font-mono text-indigo-300 backdrop-blur-sm shadow-xl"
      >
        <Terminal className="w-3.5 h-3.5 text-indigo-400" />
        <span>cursor.execute(f"SELECT ...") → SQLi detected</span>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, x: 40 }}
        animate={{ opacity: 0.6, x: 0 }}
        transition={{ duration: 1, delay: 0.4 }}
        className="hidden xl:flex absolute top-28 right-12 items-center gap-2 px-3 py-1.5 rounded-xl bg-white/[0.03] border border-white/10 text-xs font-mono text-cyan-300 backdrop-blur-sm shadow-xl"
      >
        <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
        <span>Auto-fix: hashlib.sha256() applied</span>
      </motion.div>

      <div className="max-w-5xl mx-auto px-4 text-center relative z-10">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.04] border border-white/10 text-xs font-medium text-slate-300 mb-6 backdrop-blur-sm"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Deterministic AST Engine • Zero LLM Tokens Required</span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white mb-6 leading-[1.15]"
        >
          Review code like a senior engineer,{" "}
          <span className="bg-gradient-to-r from-indigo-400 via-violet-300 to-cyan-400 bg-clip-text text-transparent">
            in seconds.
          </span>
        </motion.h1>

        {/* Subhead */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="max-w-2xl mx-auto text-base sm:text-lg text-slate-400 mb-10 leading-relaxed"
        >
          Comprehensive security auditing, cognitive complexity profiling, and safe template-based auto-fixes.
          Run offline at blistering speeds with zero dependencies on remote APIs.
        </motion.p>

        {/* Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-14"
        >
          <button
            onClick={onStart}
            className="w-full sm:w-auto px-7 py-3 rounded-xl bg-gradient-to-r from-indigo-500 via-violet-600 to-cyan-500 hover:from-indigo-400 hover:to-cyan-400 text-white font-semibold text-sm transition shadow-xl shadow-indigo-500/25 active:scale-95 flex items-center justify-center gap-2"
          >
            <span>Start Analyzing</span>
            <ArrowDown className="w-4 h-4 animate-bounce" />
          </button>
          <button
            onClick={handleTrySample}
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-white font-medium text-sm border border-white/10 transition active:scale-95 flex items-center justify-center gap-2"
          >
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span>Try a Vulnerable Sample</span>
          </button>
        </motion.div>

        {/* 3 Feature Chips */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-3xl mx-auto text-left"
        >
          <div className="flex items-start gap-3.5 p-4 rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm hover:border-white/15 transition">
            <div className="p-2 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20 shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-white text-xs font-semibold mb-1">Security Scan</h3>
              <p className="text-slate-400 text-xs">
                OWASP top 10 vulnerabilities: SQL injection, hardcoded secrets, shell injections, weak hashes.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3.5 p-4 rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm hover:border-white/15 transition">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-white text-xs font-semibold mb-1">Complexity Metrics</h3>
              <p className="text-slate-400 text-xs">
                Per-function Cyclomatic & Cognitive complexity with Radon maintainability indexing.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3.5 p-4 rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm hover:border-white/15 transition">
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shrink-0">
              <Wrench className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-white text-xs font-semibold mb-1">One-Click Fixes</h3>
              <p className="text-slate-400 text-xs">
                Deterministic refactorings that preserve formatting, comments, and guarantee valid syntax.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

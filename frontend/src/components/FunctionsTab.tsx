import React from "react";
import { FunctionMetric } from "../types";
import { useStore } from "../store/useStore";
import { getGradeColor } from "../utils";
import { Code, Hash, Layers, GitBranch, ArrowRight } from "lucide-react";

export const FunctionsTab: React.FC = () => {
  const { result, setHighlightedLine } = useStore();

  if (!result) return null;

  const functions = result.functions;

  if (functions.length === 0) {
    return (
      <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-12 text-center text-slate-400 space-y-2">
        <Code className="w-8 h-8 text-indigo-400 mx-auto opacity-70" />
        <div className="font-semibold text-white text-sm">No Function Definitions Detected</div>
        <p className="text-xs text-slate-500">
          This script consists entirely of top-level code or class definitions.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4 pb-8">
      {/* Header Stat Summary */}
      <div className="grid grid-cols-3 gap-3 bg-white/[0.02] border border-white/5 rounded-2xl p-4 text-xs">
        <div>
          <span className="text-slate-400">Total Functions:</span>
          <div className="text-lg font-bold text-white font-mono">{functions.length}</div>
        </div>
        <div>
          <span className="text-slate-400">Average CC:</span>
          <div className="text-lg font-bold text-white font-mono">{result.metrics.avg_complexity}</div>
        </div>
        <div>
          <span className="text-slate-400">Docstring Coverage:</span>
          <div className="text-lg font-bold text-white font-mono">
            {Math.round(result.metrics.docstring_coverage * 100)}%
          </div>
        </div>
      </div>

      {/* Function Cards */}
      <div className="space-y-3">
        {functions.map((fn: FunctionMetric) => {
          const rankColors = getGradeColor(fn.rank);
          const isHighComplexity = fn.cyclomatic_complexity > 10;

          return (
            <div
              key={`${fn.name}-${fn.line}`}
              onClick={() => setHighlightedLine(fn.line)}
              className="bg-darkSurface/90 border border-white/5 hover:border-indigo-500/30 rounded-2xl p-4 transition shadow-lg cursor-pointer group"
            >
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-sm font-bold text-white group-hover:text-indigo-300 transition">
                      {fn.name}()
                    </span>
                    <span className="text-[11px] font-mono text-slate-400 bg-black/40 px-2 py-0.5 rounded border border-white/5">
                      Lines {fn.line}–{fn.end_line}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Length: <strong>{fn.length}</strong> lines • Parameters: <strong>{fn.params}</strong>
                  </div>
                </div>

                {/* Rank Badge */}
                <div
                  className={`text-xs font-black px-2.5 py-0.5 rounded-full border ${rankColors.bg} ${rankColors.text} ${rankColors.border} shrink-0`}
                >
                  Rank {fn.rank}
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-2.5 text-xs bg-black/30 p-2.5 rounded-xl border border-white/5">
                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                    <GitBranch className="w-3 h-3 text-cyan-400" /> Cyclomatic
                  </div>
                  <div
                    className={`font-mono font-bold ${
                      isHighComplexity ? "text-red-400" : "text-emerald-400"
                    }`}
                  >
                    {fn.cyclomatic_complexity}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                    <Hash className="w-3 h-3 text-violet-400" /> Cognitive
                  </div>
                  <div className="font-mono font-bold text-slate-200">{fn.cognitive_complexity}</div>
                </div>

                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                    <Layers className="w-3 h-3 text-amber-400" /> Max Nesting
                  </div>
                  <div
                    className={`font-mono font-bold ${
                      fn.max_nesting > 4 ? "text-red-400" : "text-slate-200"
                    }`}
                  >
                    {fn.max_nesting} lvl
                  </div>
                </div>
              </div>

              {/* Mini visual complexity bar */}
              <div className="mt-3">
                <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      isHighComplexity
                        ? "bg-red-500 shadow-[0_0_8px_#EF4444]"
                        : "bg-emerald-500 shadow-[0_0_8px_#10B981]"
                    }`}
                    style={{ width: `${Math.min(100, (fn.cyclomatic_complexity / 20) * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

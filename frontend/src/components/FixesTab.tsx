import React, { useState } from "react";
import { Sparkles, Wrench, AlertCircle, CheckCircle2, RotateCcw, ArrowRight } from "lucide-react";
import { useStore } from "../store/useStore";
import { applyFix } from "../api/client";
import { getSeverityColor } from "../utils";
import toast from "react-hot-toast";

export const FixesTab: React.FC = () => {
  const { result, code, openDiffModal, historyStack, undo, setHighlightedLine } = useStore();
  const [isFixingAll, setIsFixingAll] = useState(false);

  if (!result) return null;

  const fixableIssues = result.issues.filter((i) => i.fixable);
  const nonFixableIssues = result.issues.filter((i) => !i.fixable);

  const handleFixAll = async () => {
    if (fixableIssues.length === 0) {
      toast.error("No auto-fixable issues detected in current code.");
      return;
    }

    setIsFixingAll(true);
    try {
      const fixRes = await applyFix(code, undefined, true);
      if (fixRes.applied.length > 0) {
        openDiffModal(code, fixRes.fixed_code, fixRes.applied.length, fixRes.skipped);
      } else {
        toast.error("No automated fixes could be safely applied.");
      }
    } catch {
      toast.error("Failed to generate automated batch fix.");
    } finally {
      setIsFixingAll(false);
    }
  };

  const handleFixSingle = async (issueId: string) => {
    try {
      const fixRes = await applyFix(code, issueId, false);
      if (fixRes.applied.length > 0) {
        openDiffModal(code, fixRes.fixed_code, fixRes.applied.length, fixRes.skipped);
      } else {
        toast.error(fixRes.skipped[0]?.reason || "Unable to auto-fix this issue.");
      }
    } catch {
      toast.error("Failed to generate automated fix.");
    }
  };

  return (
    <div className="space-y-6 pb-8">
      {/* Fix All Hero Card */}
      <div className="relative overflow-hidden bg-gradient-to-tr from-indigo-950/40 via-darkSurface to-violet-950/30 border border-indigo-500/30 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> Automated Code Refactoring
              </span>
            </div>
            <h3 className="text-lg font-bold text-white">
              {fixableIssues.length} Safe {fixableIssues.length === 1 ? "Fix" : "Fixes"} Ready
            </h3>
            <p className="text-xs text-slate-300 max-w-md">
              Batch applies AST-verified fixes in bottom-to-top order. Previews a side-by-side diff before
              committing.
            </p>
          </div>

          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            {historyStack.length > 0 && (
              <button
                onClick={undo}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 transition"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Undo</span>
              </button>
            )}
            <button
              onClick={handleFixAll}
              disabled={isFixingAll || fixableIssues.length === 0}
              className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-bold text-xs transition shadow-lg shadow-emerald-500/20 active:scale-95 disabled:opacity-50"
            >
              {isFixingAll ? (
                <div className="w-3.5 h-3.5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
              ) : (
                <Wrench className="w-4 h-4" />
              )}
              <span>Fix All Safe Issues</span>
            </button>
          </div>
        </div>
      </div>

      {/* Fixable Issues List */}
      <div className="space-y-3">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 px-1">
          Auto-Fixable Issues ({fixableIssues.length})
        </div>

        {fixableIssues.length === 0 ? (
          <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-6 text-center text-xs text-slate-400">
            No auto-fixable issues remaining.
          </div>
        ) : (
          fixableIssues.map((issue) => {
            const colors = getSeverityColor(issue.severity);
            return (
              <div
                key={issue.id}
                className="bg-darkSurface/90 border border-white/5 rounded-xl p-3.5 flex items-start justify-between gap-3 shadow-md"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border ${colors.bg} ${colors.text} ${colors.border}`}
                    >
                      {issue.severity}
                    </span>
                    <button
                      onClick={() => setHighlightedLine(issue.line)}
                      className="text-xs font-mono text-indigo-300 hover:underline"
                    >
                      Line {issue.line}
                    </button>
                    <span className="text-xs font-semibold text-white">{issue.title}</span>
                  </div>
                  <p className="text-xs text-slate-400 font-mono bg-black/30 p-2 rounded-lg border border-white/5">
                    Suggested: {issue.suggestion}
                  </p>
                </div>
                <button
                  onClick={() => handleFixSingle(issue.id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-semibold transition active:scale-95 shrink-0"
                >
                  <Wrench className="w-3.5 h-3.5" />
                  <span>Fix</span>
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Manual / Non-Fixable Issues */}
      {nonFixableIssues.length > 0 && (
        <div className="space-y-3 pt-2">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 px-1 flex items-center justify-between">
            <span>Requires Manual Refactoring ({nonFixableIssues.length})</span>
            <span className="text-[11px] text-slate-500 font-normal">Complex logic / architectural smells</span>
          </div>

          <div className="space-y-2">
            {nonFixableIssues.map((issue) => (
              <div
                key={issue.id}
                className="bg-black/20 border border-white/5 rounded-xl p-3 flex items-start justify-between gap-3 text-xs"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-mono text-slate-400">Line {issue.line}</span>
                    <span className="font-semibold text-slate-300">{issue.title}</span>
                  </div>
                  <p className="text-slate-400 text-[11px]">{issue.suggestion}</p>
                </div>
                <button
                  onClick={() => setHighlightedLine(issue.line)}
                  className="text-slate-400 hover:text-white transition p-1"
                  title="View in editor"
                >
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

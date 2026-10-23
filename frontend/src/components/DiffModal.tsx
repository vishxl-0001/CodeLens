import React from "react";
import { X, Check, AlertCircle, ArrowRight, Sparkles } from "lucide-react";
import { useStore } from "../store/useStore";
import { analyzeCode } from "../api/client";
import { triggerConfetti } from "../utils";
import toast from "react-hot-toast";

export const DiffModal: React.FC = () => {
  const {
    diffModal,
    closeDiffModal,
    code,
    setCode,
    pushHistory,
    setResult,
    setLoading,
    result,
  } = useStore();

  if (!diffModal.isOpen) return null;

  const originalLines = diffModal.originalCode.split("\n");
  const fixedLines = diffModal.fixedCode.split("\n");
  const maxLines = Math.max(originalLines.length, fixedLines.length);

  const handleApply = async () => {
    const oldScore = result?.score ?? 0;
    pushHistory(code);
    setCode(diffModal.fixedCode);
    closeDiffModal();

    toast.loading("Applying fixes and re-analyzing...", { id: "re-analyze" });
    setLoading(true);

    try {
      const newResult = await analyzeCode(diffModal.fixedCode);
      setResult(newResult);
      setLoading(false);
      toast.dismiss("re-analyze");

      const delta = newResult.score - oldScore;
      if (delta > 0) {
        toast.success(`Score improved by +${delta} points! (Now ${newResult.score}/100)`);
        triggerConfetti();
      } else {
        toast.success("Fixes applied successfully!");
      }
    } catch {
      setLoading(false);
      toast.dismiss("re-analyze");
      toast.error("Failed to re-analyze code after applying fixes.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-6xl max-h-[90vh] bg-darkSurface border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-white/[0.02]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-cyan-400 p-0.5">
              <div className="w-full h-full bg-darkSurface rounded-[10px] flex items-center justify-center text-cyan-400">
                <Sparkles className="w-4 h-4" />
              </div>
            </div>
            <div>
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                Review Automated Fixes
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  {diffModal.appliedCount} safe {diffModal.appliedCount === 1 ? "fix" : "fixes"} available
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Examine before & after changes. Formatting and comments are preserved.
              </p>
            </div>
          </div>
          <button
            onClick={closeDiffModal}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition"
            aria-label="Close diff modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Skipped notices if any */}
        {diffModal.skipped.length > 0 && (
          <div className="px-6 py-2.5 bg-amber-500/10 border-b border-amber-500/20 text-xs text-amber-200 flex items-center gap-2 overflow-x-auto">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <span className="font-semibold">{diffModal.skipped.length} issue(s) skipped:</span>
            <span className="text-slate-300 truncate">
              {diffModal.skipped.map((s) => `${s.rule_id || "complex"}: ${s.reason}`).join(" • ")}
            </span>
          </div>
        )}

        {/* Diff view header */}
        <div className="grid grid-cols-2 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-white/10 bg-white/[0.01]">
          <div className="px-4 py-2 border-r border-white/10">Original Code (Before)</div>
          <div className="px-4 py-2 text-emerald-400">Fixed Code (After)</div>
        </div>

        {/* Side-by-side diff code view */}
        <div className="flex-1 overflow-y-auto font-mono text-xs select-text bg-black/40">
          <div className="min-w-full">
            {Array.from({ length: maxLines }).map((_, index) => {
              const orig = originalLines[index] ?? "";
              const fixed = fixedLines[index] ?? "";
              const isDiff = orig !== fixed;
              const isAdded = !orig && fixed;
              const isRemoved = orig && !fixed;

              return (
                <div key={index} className="grid grid-cols-2 border-b border-white/[0.02] hover:bg-white/[0.02]">
                  {/* Left (Original) */}
                  <div
                    className={`flex items-start px-2 py-0.5 border-r border-white/10 ${
                      isDiff ? "bg-red-500/15 text-red-200" : "text-slate-400"
                    }`}
                  >
                    <span className="w-8 shrink-0 text-right pr-3 select-none text-slate-600">
                      {index < originalLines.length ? index + 1 : ""}
                    </span>
                    <span className="whitespace-pre overflow-x-auto">{orig}</span>
                  </div>

                  {/* Right (Fixed) */}
                  <div
                    className={`flex items-start px-2 py-0.5 ${
                      isDiff
                        ? isAdded
                          ? "bg-emerald-500/20 text-emerald-200 font-medium"
                          : "bg-emerald-500/15 text-emerald-200"
                        : "text-slate-300"
                    }`}
                  >
                    <span className="w-8 shrink-0 text-right pr-3 select-none text-slate-600">
                      {index < fixedLines.length ? index + 1 : ""}
                    </span>
                    <span className="whitespace-pre overflow-x-auto">{fixed}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-white/10 bg-white/[0.02]">
          <div className="text-xs text-slate-400">
            Clicking apply will update your editor and immediately re-score your code.
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={closeDiffModal}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-white/5 transition"
            >
              Cancel
            </button>
            <button
              onClick={handleApply}
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-bold text-xs transition shadow-lg shadow-emerald-500/20 active:scale-95"
            >
              <Check className="w-4 h-4" />
              Apply Fixes & Re-Analyze
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

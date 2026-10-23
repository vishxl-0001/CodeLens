import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  ArrowUpDown,
  ExternalLink,
  Wrench,
  Eye,
  Bot,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
} from "lucide-react";
import { useStore } from "../store/useStore";
import { Issue, CategoryType, SeverityLevel } from "../types";
import { getSeverityColor } from "../utils";
import { applyFix, explainIssue } from "../api/client";
import toast from "react-hot-toast";

export const IssuesTab: React.FC = () => {
  const {
    result,
    code,
    selectedSeverityFilter,
    toggleSeverityFilter,
    selectedCategoryFilter,
    setCategoryFilter,
    searchQuery,
    setSearchQuery,
    sortBy,
    setSortBy,
    setHighlightedLine,
    openDiffModal,
  } = useStore();

  const [expandedIssueIds, setExpandedIssueIds] = useState<Record<string, boolean>>({});
  const [aiExplanations, setAiExplanations] = useState<Record<string, { text: string; source: string; loading: boolean }>>({});

  if (!result) return null;

  const toggleExpand = (id: string) => {
    setExpandedIssueIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleFixSingle = async (issue: Issue) => {
    try {
      const fixRes = await applyFix(code, issue.id, false);
      if (fixRes.applied.length > 0) {
        openDiffModal(code, fixRes.fixed_code, fixRes.applied.length, fixRes.skipped);
      } else {
        toast.error(fixRes.skipped[0]?.reason || "Unable to auto-fix this issue.");
      }
    } catch {
      toast.error("Failed to generate automated fix.");
    }
  };

  const handleExplainAI = async (issue: Issue) => {
    setAiExplanations((prev) => ({
      ...prev,
      [issue.id]: { text: "", source: "ollama", loading: true },
    }));

    // Ensure card is expanded
    setExpandedIssueIds((prev) => ({ ...prev, [issue.id]: true }));

    try {
      const resp = await explainIssue(code, issue.id);
      setAiExplanations((prev) => ({
        ...prev,
        [issue.id]: { text: resp.explanation, source: resp.source, loading: false },
      }));
    } catch {
      setAiExplanations((prev) => ({
        ...prev,
        [issue.id]: {
          text: `${issue.why_it_matters}\n\nRecommendation: ${issue.suggestion}`,
          source: "builtin",
          loading: false,
        },
      }));
    }
  };

  // Filter & Sort
  const filteredIssues = result.issues.filter((issue) => {
    // Severity filter
    if (!selectedSeverityFilter.includes(issue.severity)) return false;
    // Category filter
    if (selectedCategoryFilter !== "all" && issue.category !== selectedCategoryFilter) return false;
    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchText = `${issue.title} ${issue.message} ${issue.rule_id} ${issue.line}`.toLowerCase();
      if (!matchText.includes(q)) return false;
    }
    return true;
  });

  const sortedIssues = [...filteredIssues].sort((a, b) => {
    if (sortBy === "line") {
      return a.line - b.line;
    }
    // Severity ordering
    const sevOrder: Record<SeverityLevel, number> = { critical: 0, high: 1, medium: 2, low: 3 };
    const diff = sevOrder[a.severity] - sevOrder[b.severity];
    if (diff !== 0) return diff;
    return a.line - b.line;
  });

  const categories: { id: "all" | CategoryType; label: string }[] = [
    { id: "all", label: "All Categories" },
    { id: "security", label: "Security" },
    { id: "bug", label: "Bugs" },
    { id: "maintainability", label: "Maintainability" },
    { id: "style", label: "Style" },
  ];

  const severities: SeverityLevel[] = ["critical", "high", "medium", "low"];

  return (
    <div className="space-y-4 pb-8">
      {/* Filters Toolbar */}
      <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-4 space-y-3">
        {/* Search & Sort Toggle */}
        <div className="flex flex-col sm:flex-row items-center gap-2.5">
          <div className="relative flex-1 w-full">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by rule, message, or line..."
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
            />
          </div>
          <button
            onClick={() => setSortBy(sortBy === "severity" ? "line" : "severity")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 text-xs border border-white/10 transition shrink-0"
          >
            <ArrowUpDown className="w-3.5 h-3.5 text-indigo-400" />
            <span>Sort: {sortBy === "severity" ? "Severity" : "Line Number"}</span>
          </button>
        </div>

        {/* Severity Multi-Select Chips & Category Select */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-white/5">
          {/* Severity Chips */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] text-slate-500 font-medium mr-1">Severity:</span>
            {severities.map((sev) => {
              const active = selectedSeverityFilter.includes(sev);
              const colors = getSeverityColor(sev);
              return (
                <button
                  key={sev}
                  onClick={() => toggleSeverityFilter(sev)}
                  className={`text-[11px] font-semibold capitalize px-2.5 py-0.5 rounded-lg border transition ${
                    active
                      ? `${colors.bg} ${colors.text} ${colors.border}`
                      : "bg-white/[0.01] text-slate-500 border-white/5 hover:border-white/10"
                  }`}
                >
                  {sev}
                </button>
              );
            })}
          </div>

          {/* Category Chips */}
          <div className="flex items-center gap-1 flex-wrap">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setCategoryFilter(cat.id)}
                className={`text-[11px] px-2.5 py-0.5 rounded-lg transition ${
                  selectedCategoryFilter === cat.id
                    ? "bg-indigo-600 text-white font-semibold"
                    : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results Header Count */}
      <div className="flex items-center justify-between px-1 text-xs text-slate-400">
        <span>
          Showing <strong>{sortedIssues.length}</strong> of {result.issues.length} detected issues
        </span>
      </div>

      {/* Issues List */}
      {sortedIssues.length === 0 ? (
        <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-12 text-center text-slate-400 space-y-2">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto opacity-70" />
          <div className="font-semibold text-white text-sm">No matching issues found</div>
          <p className="text-xs text-slate-500">
            {result.issues.length > 0
              ? "Try relaxing your severity or category filters."
              : "Great job! This code conforms to all 28 quality rules."}
          </p>
        </div>
      ) : (
        <motion.div layout className="space-y-3">
          <AnimatePresence>
            {sortedIssues.map((issue, idx) => {
              const colors = getSeverityColor(issue.severity);
              const isExpanded = !!expandedIssueIds[issue.id];
              const aiState = aiExplanations[issue.id];

              return (
                <motion.div
                  key={issue.id}
                  layout
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.25, delay: Math.min(idx * 0.04, 0.4) }}
                  className={`bg-darkSurface/90 border rounded-2xl p-4 transition shadow-lg ${
                    isExpanded ? "border-white/20" : "border-white/5 hover:border-white/10"
                  }`}
                >
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        {/* Severity Badge */}
                        <span
                          className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border ${colors.bg} ${colors.text} ${colors.border}`}
                        >
                          {issue.severity}
                        </span>

                        {/* Category */}
                        <span className="text-[11px] text-slate-400 font-mono">[{issue.category}]</span>

                        {/* Line pill */}
                        <button
                          onClick={() => setHighlightedLine(issue.line)}
                          className="text-[11px] font-mono px-2 py-0.5 rounded bg-black/40 text-indigo-300 border border-white/5 hover:border-indigo-500/40 hover:text-white transition flex items-center gap-1"
                        >
                          <Eye className="w-3 h-3 text-indigo-400" />
                          <span>Line {issue.line}</span>
                        </button>

                        {/* Reference badge */}
                        {issue.reference && (
                          <span className="text-[10px] text-slate-400 px-1.5 py-0.5 rounded bg-white/5 border border-white/5">
                            {issue.reference}
                          </span>
                        )}
                      </div>

                      {/* Title & message */}
                      <h4 className="text-white font-semibold text-sm pt-1">{issue.title}</h4>
                      <p className="text-slate-300 text-xs leading-relaxed">{issue.message}</p>
                    </div>

                    {/* Actions: Fix / Expand */}
                    <div className="flex items-center gap-1.5 shrink-0">
                      {issue.fixable && (
                        <button
                          onClick={() => handleFixSingle(issue)}
                          className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-semibold transition active:scale-95"
                          title="Generate automated fix"
                        >
                          <Wrench className="w-3.5 h-3.5" />
                          <span>Fix</span>
                        </button>
                      )}
                      <button
                        onClick={() => toggleExpand(issue.id)}
                        className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition"
                        aria-label="Toggle details"
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Accordion Expanded Details */}
                  {isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-4 pt-3.5 border-t border-white/5 space-y-3 text-xs"
                    >
                      {/* Why it matters */}
                      <div>
                        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                          Why It Matters
                        </div>
                        <p className="text-slate-300 bg-black/30 p-2.5 rounded-xl border border-white/5 leading-relaxed">
                          {issue.why_it_matters}
                        </p>
                      </div>

                      {/* How to fix suggestion */}
                      <div>
                        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                          <Wrench className="w-3.5 h-3.5 text-cyan-400" />
                          How to Fix
                        </div>
                        <p className="text-slate-300 bg-black/30 p-2.5 rounded-xl border border-white/5 leading-relaxed font-mono text-[11px]">
                          {issue.suggestion}
                        </p>
                      </div>

                      {/* AI Explanation Box */}
                      {aiState && (
                        <div className="bg-indigo-950/20 border border-indigo-500/30 rounded-xl p-3 space-y-1.5">
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="font-semibold text-indigo-300 flex items-center gap-1.5">
                              <Bot className="w-3.5 h-3.5 text-cyan-400" />
                              AI Security Analysis
                            </span>
                            <span className="text-[10px] text-slate-400 px-1.5 py-0.5 rounded bg-white/5">
                              {aiState.source === "ollama" ? "Ollama Local Model" : "Built-in Analysis"}
                            </span>
                          </div>
                          {aiState.loading ? (
                            <div className="flex items-center gap-2 text-indigo-300 text-xs py-1">
                              <div className="w-3 h-3 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
                              <span>Generating localized explanation...</span>
                            </div>
                          ) : (
                            <p className="text-slate-200 text-xs leading-relaxed whitespace-pre-wrap">
                              {aiState.text}
                            </p>
                          )}
                        </div>
                      )}

                      {/* Bottom Footer Actions inside accordion */}
                      <div className="flex items-center justify-between pt-1">
                        <button
                          onClick={() => handleExplainAI(issue)}
                          className="flex items-center gap-1.5 text-[11px] text-indigo-400 hover:text-indigo-300 transition"
                        >
                          <Bot className="w-3.5 h-3.5 text-cyan-400" />
                          <span>Explain with AI</span>
                        </button>
                        <button
                          onClick={() => setHighlightedLine(issue.line)}
                          className="text-[11px] text-slate-400 hover:text-white transition flex items-center gap-1"
                        >
                          <span>Jump to line {issue.line} in editor</span>
                          <ExternalLink className="w-3 h-3" />
                        </button>
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              );
            })}
          </AnimatePresence>
        </motion.div>
      )}
    </div>
  );
};

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  AlertTriangle,
  Code2,
  Wrench,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { useStore } from "../store/useStore";
import { OverviewTab } from "./OverviewTab";
import { IssuesTab } from "./IssuesTab";
import { FunctionsTab } from "./FunctionsTab";
import { FixesTab } from "./FixesTab";

export const RightPanel: React.FC = () => {
  const { result, isLoading, activeTab, setActiveTab } = useStore();

  const tabs = [
    {
      id: "overview" as const,
      label: "Overview",
      icon: LayoutDashboard,
    },
    {
      id: "issues" as const,
      label: "Issues",
      icon: AlertTriangle,
      badge: result ? result.issues.length : undefined,
    },
    {
      id: "functions" as const,
      label: "Functions",
      icon: Code2,
      badge: result ? result.functions.length : undefined,
    },
    {
      id: "fixes" as const,
      label: "Fixes",
      icon: Wrench,
      badge: result ? result.issues.filter((i) => i.fixable).length : undefined,
    },
  ];

  return (
    <div className="flex flex-col h-full bg-darkSurface border border-white/10 rounded-2xl overflow-hidden shadow-xl">
      {/* Tabs Header */}
      <div className="flex items-center px-4 border-b border-white/10 bg-white/[0.02] gap-1 overflow-x-auto no-scrollbar">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`relative flex items-center gap-2 px-4 py-3 text-xs font-semibold transition shrink-0 ${
                isActive ? "text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : "text-slate-500"}`} />
              <span>{tab.label}</span>
              {typeof tab.badge === "number" && (
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                    isActive
                      ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                      : "bg-white/5 text-slate-500"
                  }`}
                >
                  {tab.badge}
                </span>
              )}

              {/* Animated Sliding Underline */}
              {isActive && (
                <motion.div
                  layoutId="activeTabUnderline"
                  className="absolute bottom-0 inset-x-2 h-0.5 bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full"
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content Container */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        {isLoading ? (
          // Skeleton Loader
          <div className="space-y-4 animate-pulse">
            <div className="h-44 bg-white/5 rounded-2xl" />
            <div className="grid grid-cols-4 gap-3">
              <div className="h-20 bg-white/5 rounded-xl" />
              <div className="h-20 bg-white/5 rounded-xl" />
              <div className="h-20 bg-white/5 rounded-xl" />
              <div className="h-20 bg-white/5 rounded-xl" />
            </div>
            <div className="h-56 bg-white/5 rounded-2xl" />
          </div>
        ) : !result ? (
          // Empty State illustration
          <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400 space-y-3">
            <div className="w-16 h-16 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-2">
              <Sparkles className="w-8 h-8" />
            </div>
            <h3 className="text-base font-bold text-white">No Analysis Results Yet</h3>
            <p className="text-xs text-slate-400 max-w-sm leading-relaxed">
              Click <strong>"Analyze Code"</strong> in the top navigation or press{" "}
              <kbd className="px-1.5 py-0.5 rounded bg-black/40 text-indigo-300 font-mono text-[10px]">Ctrl+Enter</kbd>{" "}
              to run the 28-rule inspection engine on your Python code.
            </p>
          </div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15 }}
            >
              {activeTab === "overview" && <OverviewTab />}
              {activeTab === "issues" && <IssuesTab />}
              {activeTab === "functions" && <FunctionsTab />}
              {activeTab === "fixes" && <FixesTab />}
            </motion.div>
          </AnimatePresence>
        )}
      </div>
    </div>
  );
};

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { ShieldCheck, Bug, Wrench, Clock, FileText, Activity, AlertOctagon } from "lucide-react";
import { useStore } from "../store/useStore";
import { getGradeColor } from "../utils";

export const OverviewTab: React.FC = () => {
  const { result, previousScore } = useStore();
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    if (!result) return;
    const target = result.score;
    let start = 0;
    const duration = 1200; // ms
    const stepTime = 20;
    const increment = target / (duration / stepTime);

    const timer = setInterval(() => {
      start += increment;
      if (start >= target) {
        setAnimatedScore(target);
        clearInterval(timer);
      } else {
        setAnimatedScore(Math.floor(start));
      }
    }, stepTime);

    return () => clearInterval(timer);
  }, [result]);

  if (!result) return null;

  const gradeInfo = getGradeColor(result.grade);
  const scoreDelta = previousScore !== null ? result.score - previousScore : null;

  // SVG Gauge calculations
  const radius = 80;
  const strokeWidth = 14;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  // Donut chart data (by severity)
  const severityData = [
    { name: "Critical", value: result.summary.by_severity.critical, color: "#EF4444" },
    { name: "High", value: result.summary.by_severity.high, color: "#F97316" },
    { name: "Medium", value: result.summary.by_severity.medium, color: "#EAB308" },
    { name: "Low", value: result.summary.by_severity.low, color: "#38BDF8" },
  ].filter((d) => d.value > 0);

  // Category chart data
  const categoryData = [
    { name: "Security", count: result.summary.by_category.security, fill: "#EF4444" },
    { name: "Bug / Reliability", count: result.summary.by_category.bug, fill: "#F97316" },
    { name: "Maintainability", count: result.summary.by_category.maintainability, fill: "#8B5CF6" },
    { name: "Style", count: result.summary.by_category.style, fill: "#38BDF8" },
  ];

  // Function complexity data
  const functionComplexityData = result.functions.map((fn) => ({
    name: fn.name.length > 12 ? `${fn.name.slice(0, 10)}...` : fn.name,
    complexity: fn.cyclomatic_complexity,
    rank: fn.rank,
    fill: fn.cyclomatic_complexity > 10 ? "#EF4444" : "#10B981",
  }));

  return (
    <div className="space-y-6 pb-8">
      {/* Top Gauge & Subscores Section */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-center bg-white/[0.02] border border-white/5 rounded-2xl p-6 shadow-xl">
        {/* Big Circular Score Gauge */}
        <div className="md:col-span-6 flex flex-col items-center justify-center relative">
          <div className="relative w-48 h-48 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 200 200">
              {/* Background track circle */}
              <circle
                cx="100"
                cy="100"
                r={radius}
                className="stroke-white/10 fill-none"
                strokeWidth={strokeWidth}
              />
              {/* Animated Progress circle */}
              <circle
                cx="100"
                cy="100"
                r={radius}
                className="fill-none transition-all duration-1000 ease-out"
                stroke={gradeInfo.stroke}
                strokeWidth={strokeWidth}
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            </svg>

            {/* Center Content: Score number & Grade Badge */}
            <div className="absolute flex flex-col items-center justify-center text-center">
              <motion.span
                key={animatedScore}
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
                className="text-5xl font-black tracking-tight text-white font-mono"
              >
                {animatedScore}
              </motion.span>
              <span className="text-xs text-slate-400 font-medium">Health Score</span>

              {/* Letter Grade Pill */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                className={`mt-1 text-xs font-extrabold px-3 py-0.5 rounded-full border ${gradeInfo.bg} ${gradeInfo.text} ${gradeInfo.border}`}
              >
                Grade {result.grade}
              </motion.div>
            </div>
          </div>

          {/* Delta score badge if improved */}
          {scoreDelta !== null && scoreDelta !== 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`mt-2 text-xs font-bold px-2.5 py-0.5 rounded-full ${
                scoreDelta > 0
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  : "bg-red-500/20 text-red-400 border border-red-500/30"
              }`}
            >
              {scoreDelta > 0 ? `+${scoreDelta} points improvement` : `${scoreDelta} points`}
            </motion.div>
          )}
        </div>

        {/* 3 Mini Subscores */}
        <div className="md:col-span-6 flex flex-col justify-center space-y-3.5">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Health Subscores
          </div>

          {/* Security */}
          <div className="bg-black/30 border border-white/5 rounded-xl p-3 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-white">Security</div>
                <div className="text-[11px] text-slate-400">Vulnerabilities & secrets</div>
              </div>
            </div>
            <div className="text-right">
              <span className="text-base font-bold font-mono text-white">
                {result.subscores.security}
              </span>
              <span className="text-xs text-slate-400">/100</span>
            </div>
          </div>

          {/* Reliability */}
          <div className="bg-black/30 border border-white/5 rounded-xl p-3 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Bug className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-white">Reliability</div>
                <div className="text-[11px] text-slate-400">Bugs & exception flow</div>
              </div>
            </div>
            <div className="text-right">
              <span className="text-base font-bold font-mono text-white">
                {result.subscores.reliability}
              </span>
              <span className="text-xs text-slate-400">/100</span>
            </div>
          </div>

          {/* Maintainability */}
          <div className="bg-black/30 border border-white/5 rounded-xl p-3 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Wrench className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-white">Maintainability</div>
                <div className="text-[11px] text-slate-400">Complexity & code hygiene</div>
              </div>
            </div>
            <div className="text-right">
              <span className="text-base font-bold font-mono text-white">
                {result.subscores.maintainability}
              </span>
              <span className="text-xs text-slate-400">/100</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3.5">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <AlertOctagon className="w-3.5 h-3.5 text-red-400" /> Total Issues
          </div>
          <div className="text-2xl font-bold font-mono text-white">{result.summary.total_issues}</div>
        </div>
        <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3.5">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <FileText className="w-3.5 h-3.5 text-cyan-400" /> Lines of Code
          </div>
          <div className="text-2xl font-bold font-mono text-white">{result.summary.lines_of_code}</div>
        </div>
        <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3.5">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Activity className="w-3.5 h-3.5 text-violet-400" /> Avg Complexity
          </div>
          <div className="text-2xl font-bold font-mono text-white">{result.metrics.avg_complexity}</div>
        </div>
        <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3.5">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Clock className="w-3.5 h-3.5 text-emerald-400" /> Analysis Speed
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {result.summary.analysis_ms} <span className="text-xs font-normal text-slate-400">ms</span>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Donut Chart: Issues by Severity */}
        <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-5 shadow-xl flex flex-col">
          <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Issues by Severity
          </div>
          <div className="flex-1 min-h-[220px] flex items-center justify-center">
            {severityData.length === 0 ? (
              <div className="text-xs text-slate-500 italic">No issues detected 🎉</div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#12141C",
                      borderColor: "rgba(255,255,255,0.1)",
                      borderRadius: "12px",
                      fontSize: "12px",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
          {/* Legend */}
          <div className="flex items-center justify-center gap-3 text-xs flex-wrap pt-2 border-t border-white/5">
            {severityData.map((s) => (
              <div key={s.name} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: s.color }} />
                <span className="text-slate-300">{s.name}:</span>
                <span className="font-mono font-semibold text-white">{s.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Bar Chart: Issues by Category */}
        <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-5 shadow-xl flex flex-col">
          <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Issues by Category
          </div>
          <div className="flex-1 min-h-[220px]">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={categoryData} layout="vertical" margin={{ left: 20, right: 20 }}>
                <XAxis type="number" stroke="#64748B" fontSize={11} allowDecimals={false} />
                <YAxis dataKey="name" type="category" stroke="#94A3B8" fontSize={11} width={90} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#12141C",
                    borderColor: "rgba(255,255,255,0.1)",
                    borderRadius: "12px",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                  {categoryData.map((entry, index) => (
                    <Cell key={`cat-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Function Complexity Bar Chart with Threshold */}
      {result.functions.length > 0 && (
        <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-3">
            <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Cyclomatic Complexity per Function
            </div>
            <div className="text-[11px] text-red-400 flex items-center gap-1.5">
              <span className="w-2 h-0.5 bg-red-400" />
              Threshold line: 10
            </div>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={functionComplexityData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="name" stroke="#94A3B8" fontSize={11} interval={0} angle={-25} textAnchor="end" />
                <YAxis stroke="#64748B" fontSize={11} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#12141C",
                    borderColor: "rgba(255,255,255,0.1)",
                    borderRadius: "12px",
                    fontSize: "12px",
                  }}
                />
                <ReferenceLine y={10} stroke="#EF4444" strokeDasharray="3 3" />
                <Bar dataKey="complexity" radius={[6, 6, 0, 0]}>
                  {functionComplexityData.map((entry, index) => (
                    <Cell key={`fn-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

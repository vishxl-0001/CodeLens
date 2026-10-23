import React, { useEffect, useState, useRef } from "react";
import {
  Sparkles,
  Play,
  Upload,
  RotateCcw,
  Download,
  Share2,
  HelpCircle,
  Sun,
  Moon,
  ChevronDown,
  Check,
  FileCode2,
} from "lucide-react";
import { useStore } from "../store/useStore";
import { getSamples, analyzeCode, analyzeFile } from "../api/client";
import { SampleItem } from "../types";
import { exportMarkdownReport, downloadJsonFile } from "../utils";
import toast from "react-hot-toast";

interface NavbarProps {
  onOpenAbout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenAbout }) => {
  const {
    code,
    filename,
    setCode,
    setFilename,
    result,
    setResult,
    isLoading,
    setLoading,
    setBackendOffline,
    historyStack,
    undo,
    theme,
    toggleTheme,
  } = useStore();

  const [samples, setSamples] = useState<SampleItem[]>([]);
  const [isSampleOpen, setIsSampleOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getSamples()
      .then((data) => {
        setSamples(data);
        setBackendOffline(false);
      })
      .catch(() => {
        setBackendOffline(true);
      });
  }, [setBackendOffline]);

  const handleRunAnalysis = async () => {
    if (!code.trim()) {
      toast.error("Please enter or upload Python code to analyze.");
      return;
    }
    setLoading(true);
    try {
      const res = await analyzeCode(code, filename);
      setResult(res);
      setBackendOffline(false);
      toast.success(`Analysis complete: Score ${res.score}/100 (Grade ${res.grade})`);
    } catch (err: any) {
      if (err.status === 413) {
        toast.error("Code exceeds maximum 200KB limit.");
      } else {
        toast.error("Analysis server offline or returned error.");
        setBackendOffline(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSample = (sample: SampleItem) => {
    setCode(sample.code);
    setFilename(sample.name);
    setIsSampleOpen(false);
    toast.success(`Loaded demo sample: ${sample.name}`);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith(".py")) {
      toast.error("Please select a Python (.py) file.");
      return;
    }

    setFilename(file.name);
    const text = await file.text();
    setCode(text);

    setLoading(true);
    try {
      const res = await analyzeFile(file);
      setResult(res);
      setBackendOffline(false);
      toast.success(`Uploaded and analyzed ${file.name}`);
    } catch {
      toast.error("Failed to analyze uploaded file.");
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleCopyMarkdown = () => {
    if (!result) {
      toast.error("Run analysis first to generate a report.");
      return;
    }
    const md = exportMarkdownReport(result, filename);
    navigator.clipboard.writeText(md);
    setIsExportOpen(false);
    toast.success("Markdown report copied to clipboard!");
  };

  const handleDownloadJson = () => {
    if (!result) {
      toast.error("Run analysis first to generate a report.");
      return;
    }
    downloadJsonFile(result, `${filename}-review.json`);
    setIsExportOpen(false);
    toast.success("JSON report downloaded.");
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/10 bg-darkSurface/80 backdrop-blur-md">
      <div className="max-w-[1700px] mx-auto px-4 h-16 flex items-center justify-between gap-3">
        {/* Left: Brand */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20">
            <div className="w-full h-full bg-darkBg rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-indigo-400" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              CodeLens
            </span>
            <span className="hidden sm:inline-block text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              v1.0
            </span>
          </div>
        </div>

        {/* Center: Controls & Samples */}
        <div className="flex items-center gap-2">
          {/* Sample selector */}
          <div className="relative">
            <button
              onClick={() => setIsSampleOpen(!isSampleOpen)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 border border-white/10 transition"
              aria-label="Select demo sample"
            >
              <FileCode2 className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden md:inline">Sample:</span>
              <span className="font-semibold text-white">{filename}</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {isSampleOpen && (
              <div className="absolute top-full mt-2 left-0 w-72 bg-darkSurface border border-white/15 rounded-2xl shadow-2xl p-1.5 z-50">
                <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Preset Demonstrations
                </div>
                {samples.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => handleSelectSample(s)}
                    className="w-full text-left px-3 py-2 rounded-xl text-xs hover:bg-white/5 transition flex flex-col gap-0.5"
                  >
                    <div className="flex items-center justify-between text-white font-medium">
                      <span>{s.name}</span>
                      {filename === s.name && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                    </div>
                    <span className="text-[11px] text-slate-400 line-clamp-1">{s.description}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Upload file */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".py"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 border border-white/10 transition"
            title="Upload Python file"
          >
            <Upload className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Upload .py</span>
          </button>

          {/* Undo */}
          {historyStack.length > 0 && (
            <button
              onClick={undo}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-medium bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 transition"
              title="Undo applied fixes"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Undo ({historyStack.length})</span>
            </button>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {/* Export dropdown */}
          <div className="relative">
            <button
              onClick={() => setIsExportOpen(!isExportOpen)}
              className="p-2 rounded-xl text-slate-400 hover:text-white bg-white/[0.02] hover:bg-white/5 border border-white/10 transition"
              title="Export Report"
            >
              <Download className="w-4 h-4" />
            </button>
            {isExportOpen && (
              <div className="absolute right-0 top-full mt-2 w-48 bg-darkSurface border border-white/15 rounded-xl shadow-xl p-1 z-50">
                <button
                  onClick={handleCopyMarkdown}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-white/5 text-slate-200 transition flex items-center gap-2"
                >
                  <Share2 className="w-3.5 h-3.5 text-indigo-400" />
                  Copy Markdown
                </button>
                <button
                  onClick={handleDownloadJson}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-white/5 text-slate-200 transition flex items-center gap-2"
                >
                  <Download className="w-3.5 h-3.5 text-cyan-400" />
                  Download JSON
                </button>
              </div>
            )}
          </div>

          {/* About Engine */}
          <button
            onClick={onOpenAbout}
            className="p-2 rounded-xl text-slate-400 hover:text-white bg-white/[0.02] hover:bg-white/5 border border-white/10 transition"
            title="How the engine works"
          >
            <HelpCircle className="w-4 h-4" />
          </button>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl text-slate-400 hover:text-white bg-white/[0.02] hover:bg-white/5 border border-white/10 transition"
            title="Toggle color theme"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          {/* Primary Analyze Button */}
          <button
            onClick={handleRunAnalysis}
            disabled={isLoading}
            className="group relative overflow-hidden flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-500 via-violet-600 to-cyan-500 hover:from-indigo-400 hover:to-cyan-400 text-white font-semibold text-xs transition shadow-lg shadow-indigo-500/25 active:scale-95 disabled:opacity-50"
          >
            {/* Shimmer animation */}
            <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full duration-1000 bg-gradient-to-r from-transparent via-white/20 to-transparent transition-all" />
            {isLoading ? (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-current" />
            )}
            <span>{isLoading ? "Analyzing..." : "Analyze Code"}</span>
            <kbd className="hidden lg:inline-block px-1.5 py-0.5 rounded bg-black/30 text-[10px] text-white/70 font-mono">
              Ctrl+↵
            </kbd>
          </button>
        </div>
      </div>
    </header>
  );
};

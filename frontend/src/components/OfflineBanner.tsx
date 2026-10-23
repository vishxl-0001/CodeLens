import React from "react";
import { AlertTriangle, RefreshCw, Terminal } from "lucide-react";
import { useStore } from "../store/useStore";
import { checkHealth, analyzeCode } from "../api/client";
import toast from "react-hot-toast";

export const OfflineBanner: React.FC = () => {
  const { isBackendOffline, setBackendOffline, code, setResult, setLoading } = useStore();

  if (!isBackendOffline) return null;

  const handleRetry = async () => {
    try {
      await checkHealth();
      setBackendOffline(false);
      toast.success("Backend reconnected!");
      // Re-trigger analysis
      setLoading(true);
      const res = await analyzeCode(code);
      setResult(res);
      setLoading(false);
    } catch {
      toast.error("Backend is still unreachable. Make sure uvicorn is running.");
    }
  };

  return (
    <div className="bg-gradient-to-r from-red-500/20 via-amber-500/20 to-red-500/20 border-b border-red-500/30 px-4 py-2.5 backdrop-blur-md">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-sm">
        <div className="flex items-center gap-2.5 text-red-200">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>
            <strong>Backend Offline:</strong> Analysis server at{" "}
            <code className="bg-black/30 px-1.5 py-0.5 rounded text-xs text-red-300">http://localhost:8000</code> is
            unreachable.
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-1.5 bg-black/40 px-2.5 py-1 rounded text-xs font-mono text-slate-300 border border-white/5">
            <Terminal className="w-3.5 h-3.5 text-indigo-400" />
            <span>uvicorn app.main:app --reload</span>
          </div>
          <button
            onClick={handleRetry}
            className="flex items-center gap-1.5 bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-xs font-medium transition shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry Connection
          </button>
        </div>
      </div>
    </div>
  );
};

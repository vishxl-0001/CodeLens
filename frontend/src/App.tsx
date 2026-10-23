import React, { useEffect, useState, useRef } from "react";
import { Toaster } from "react-hot-toast";
import { Navbar } from "./components/Navbar";
import { OfflineBanner } from "./components/OfflineBanner";
import { LandingHero } from "./components/LandingHero";
import { EditorPanel } from "./components/EditorPanel";
import { RightPanel } from "./components/RightPanel";
import { DiffModal } from "./components/DiffModal";
import { AboutModal } from "./components/AboutModal";
import { useStore } from "./store/useStore";
import { analyzeCode } from "./api/client";

export const App: React.FC = () => {
  const { code, filename, setResult, setLoading, setBackendOffline } = useStore();
  const [isAboutOpen, setIsAboutOpen] = useState(false);
  const workspaceRef = useRef<HTMLDivElement>(null);

  // Keyboard shortcut: Ctrl+Enter or Cmd+Enter to analyze
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        setLoading(true);
        analyzeCode(code, filename)
          .then((res) => {
            setResult(res);
            setBackendOffline(false);
          })
          .catch(() => {
            setBackendOffline(true);
          })
          .finally(() => {
            setLoading(false);
          });
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [code, filename, setResult, setLoading, setBackendOffline]);

  // Initial analysis on load so workspace isn't empty
  useEffect(() => {
    setLoading(true);
    analyzeCode(code, filename)
      .then((res) => {
        setResult(res);
        setBackendOffline(false);
      })
      .catch(() => {
        setBackendOffline(true);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const scrollToWorkspace = () => {
    workspaceRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="flex flex-col min-h-screen bg-darkBg text-slate-100 relative">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#12141C",
            color: "#F8FAFC",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: "12px",
            fontSize: "12px",
          },
        }}
      />

      <OfflineBanner />
      <Navbar onOpenAbout={() => setIsAboutOpen(true)} />

      {/* Landing Hero Section */}
      <LandingHero onStart={scrollToWorkspace} />

      {/* Workspace App Section */}
      <main ref={workspaceRef} className="flex-1 max-w-[1700px] w-full mx-auto p-3 sm:p-5">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 h-[calc(100vh-5.5rem)] min-h-[680px]">
          {/* Left: Code Editor */}
          <div className="lg:col-span-6 h-full">
            <EditorPanel />
          </div>

          {/* Right: Analysis Dashboard Tabs */}
          <div className="lg:col-span-6 h-full">
            <RightPanel />
          </div>
        </div>
      </main>

      {/* Modals */}
      <DiffModal />
      <AboutModal isOpen={isAboutOpen} onClose={() => setIsAboutOpen(false)} />
    </div>
  );
};

export default App;

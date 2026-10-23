import { create } from "zustand";
import { AnalysisResult, CategoryType, SeverityLevel, SkippedFix } from "../types";

interface DiffModalState {
  isOpen: boolean;
  originalCode: string;
  fixedCode: string;
  appliedCount: number;
  skipped: SkippedFix[];
}

interface AppState {
  code: string;
  filename: string;
  result: AnalysisResult | null;
  previousScore: number | null;
  isLoading: boolean;
  isBackendOffline: boolean;
  error: string | null;
  historyStack: string[];
  theme: "dark" | "light";
  activeTab: "overview" | "issues" | "functions" | "fixes";
  selectedSeverityFilter: SeverityLevel[];
  selectedCategoryFilter: "all" | CategoryType;
  searchQuery: string;
  sortBy: "severity" | "line";
  highlightedLine: number | null;
  diffModal: DiffModalState;

  setCode: (code: string) => void;
  setFilename: (name: string) => void;
  setResult: (res: AnalysisResult | null) => void;
  setLoading: (loading: boolean) => void;
  setBackendOffline: (offline: boolean) => void;
  setError: (err: string | null) => void;
  setTheme: (theme: "dark" | "light") => void;
  toggleTheme: () => void;
  setActiveTab: (tab: "overview" | "issues" | "functions" | "fixes") => void;
  toggleSeverityFilter: (sev: SeverityLevel) => void;
  setCategoryFilter: (cat: "all" | CategoryType) => void;
  setSearchQuery: (q: string) => void;
  setSortBy: (sort: "severity" | "line") => void;
  setHighlightedLine: (line: number | null) => void;
  pushHistory: (code: string) => void;
  undo: () => void;
  openDiffModal: (originalCode: string, fixedCode: string, appliedCount: number, skipped: SkippedFix[]) => void;
  closeDiffModal: () => void;
}

const DEFAULT_STARTER_CODE = `import os
import hashlib
import requests

DEBUG = True
api_key = "AKIA1234567890SECRETKEY"

# TODO: rotate temporary tokens
def get_user_data(user_id, format=None, tags=[]):
    if user_id == None:
        return {}
    
    h = hashlib.md5(user_id.encode()).hexdigest()
    resp = requests.get("https://api.example.com/user", verify=False)
    print("User retrieved successfully")
    return {"hash": h, "status": 200}
`;

const savedTheme = (typeof window !== "undefined" && localStorage.getItem("codelens-theme") as "dark" | "light") || "dark";
if (typeof document !== "undefined") {
  if (savedTheme === "dark") {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }
}

export const useStore = create<AppState>((set, get) => ({
  code: DEFAULT_STARTER_CODE,
  filename: "sample.py",
  result: null,
  previousScore: null,
  isLoading: false,
  isBackendOffline: false,
  error: null,
  historyStack: [],
  theme: savedTheme,
  activeTab: "overview",
  selectedSeverityFilter: ["critical", "high", "medium", "low"],
  selectedCategoryFilter: "all",
  searchQuery: "",
  sortBy: "severity",
  highlightedLine: null,
  diffModal: {
    isOpen: false,
    originalCode: "",
    fixedCode: "",
    appliedCount: 0,
    skipped: [],
  },

  setCode: (code) => set({ code }),
  setFilename: (filename) => set({ filename }),
  setResult: (res) => {
    const currentScore = get().result?.score ?? null;
    set({ result: res, previousScore: currentScore });
  },
  setLoading: (isLoading) => set({ isLoading }),
  setBackendOffline: (isBackendOffline) => set({ isBackendOffline }),
  setError: (error) => set({ error }),
  setTheme: (theme) => {
    localStorage.setItem("codelens-theme", theme);
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    set({ theme });
  },
  toggleTheme: () => {
    const nextTheme = get().theme === "dark" ? "light" : "dark";
    get().setTheme(nextTheme);
  },
  setActiveTab: (activeTab) => set({ activeTab }),
  toggleSeverityFilter: (sev) => {
    const current = get().selectedSeverityFilter;
    if (current.includes(sev)) {
      if (current.length === 1) return; // Keep at least one
      set({ selectedSeverityFilter: current.filter((s) => s !== sev) });
    } else {
      set({ selectedSeverityFilter: [...current, sev] });
    }
  },
  setCategoryFilter: (selectedCategoryFilter) => set({ selectedCategoryFilter }),
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  setSortBy: (sortBy) => set({ sortBy }),
  setHighlightedLine: (highlightedLine) => set({ highlightedLine }),
  pushHistory: (code) => {
    set((state) => ({ historyStack: [...state.historyStack, code] }));
  },
  undo: () => {
    const { historyStack } = get();
    if (historyStack.length === 0) return;
    const previousCode = historyStack[historyStack.length - 1];
    set({
      code: previousCode,
      historyStack: historyStack.slice(0, -1),
    });
  },
  openDiffModal: (originalCode, fixedCode, appliedCount, skipped) => {
    set({
      diffModal: {
        isOpen: true,
        originalCode,
        fixedCode,
        appliedCount,
        skipped,
      },
    });
  },
  closeDiffModal: () => {
    set({
      diffModal: {
        isOpen: false,
        originalCode: "",
        fixedCode: "",
        appliedCount: 0,
        skipped: [],
      },
    });
  },
}));

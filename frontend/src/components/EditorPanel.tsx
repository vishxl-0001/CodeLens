import React, { useRef, useEffect } from "react";
import Editor, { Monaco, OnMount } from "@monaco-editor/react";
import { useStore } from "../store/useStore";
import { Code2, Sparkles, Layers } from "lucide-react";

export const EditorPanel: React.FC = () => {
  const {
    code,
    setCode,
    filename,
    result,
    theme,
    isLoading,
    highlightedLine,
    setHighlightedLine,
  } = useStore();

  const editorRef = useRef<any>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const decorationsRef = useRef<string[]>([]);
  const flashDecorationRef = useRef<string[]>([]);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    // Custom dark theme styling
    monaco.editor.defineTheme("codelens-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [
        { token: "comment", foreground: "64748B", fontStyle: "italic" },
        { token: "keyword", foreground: "818CF8", fontStyle: "bold" },
        { token: "string", foreground: "34D399" },
        { token: "number", foreground: "F59E0B" },
        { token: "function", foreground: "38BDF8" },
      ],
      colors: {
        "editor.background": "#0D0E15",
        "editor.foreground": "#E2E8F0",
        "editorLineNumber.foreground": "#475569",
        "editorLineNumber.activeForeground": "#818CF8",
        "editor.lineHighlightBackground": "#181B26",
        "editor.selectionBackground": "#6366F133",
        "editorGutter.background": "#0D0E15",
      },
    });

    monaco.editor.setTheme(theme === "dark" ? "codelens-dark" : "light");
  };

  useEffect(() => {
    if (monacoRef.current) {
      monacoRef.current.editor.setTheme(theme === "dark" ? "codelens-dark" : "light");
    }
  }, [theme]);

  // Update decorations when analysis issues change
  useEffect(() => {
    if (!editorRef.current || !monacoRef.current) return;
    const editor = editorRef.current;
    const monaco = monacoRef.current;

    if (!result || result.issues.length === 0) {
      decorationsRef.current = editor.deltaDecorations(decorationsRef.current, []);
      return;
    }

    const newDecorations = result.issues.map((issue) => {
      let squiggleClass = "squiggle-low";
      if (issue.severity === "critical") squiggleClass = "squiggle-critical";
      else if (issue.severity === "high") squiggleClass = "squiggle-high";
      else if (issue.severity === "medium") squiggleClass = "squiggle-medium";

      return {
        range: new monaco.Range(issue.line, issue.column + 1, issue.end_line || issue.line, 100),
        options: {
          isWholeLine: false,
          inlineClassName: squiggleClass,
          hoverMessage: {
            value: `**[${issue.severity.toUpperCase()}] ${issue.title}**\n\n${issue.message}\n\n*Suggestion:* ${issue.suggestion}`,
          },
          glyphMarginClassName: `gutter-${issue.severity}`,
          minimap: { color: issue.severity === "critical" ? "#EF4444" : "#EAB308", position: 1 },
        },
      };
    });

    decorationsRef.current = editor.deltaDecorations(decorationsRef.current, newDecorations);
  }, [result]);

  // Jump and flash animation when an issue is clicked
  useEffect(() => {
    if (!editorRef.current || !monacoRef.current || !highlightedLine) return;
    const editor = editorRef.current;
    const monaco = monacoRef.current;

    editor.revealLineInCenter(highlightedLine);
    editor.setPosition({ lineNumber: highlightedLine, column: 1 });

    // Flash highlight decoration
    const flashDecoration = [
      {
        range: new monaco.Range(highlightedLine, 1, highlightedLine, 1),
        options: {
          isWholeLine: true,
          className: "line-flash-highlight",
        },
      },
    ];

    flashDecorationRef.current = editor.deltaDecorations(flashDecorationRef.current, flashDecoration);

    const timeout = setTimeout(() => {
      if (editorRef.current) {
        flashDecorationRef.current = editorRef.current.deltaDecorations(flashDecorationRef.current, []);
      }
      setHighlightedLine(null);
    }, 1800);

    return () => clearTimeout(timeout);
  }, [highlightedLine, setHighlightedLine]);

  // Drag and drop file support
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith(".py")) {
      const text = await file.text();
      setCode(text);
    }
  };

  return (
    <div
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      className="relative flex flex-col h-full bg-darkSurface border border-white/10 rounded-2xl overflow-hidden shadow-xl"
    >
      {/* Editor top mini header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-white/[0.02]">
        <div className="flex items-center gap-2">
          <Code2 className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-mono text-slate-300 font-medium">{filename}</span>
          <span className="text-[10px] text-slate-500">• Python 3.10+</span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-slate-400">
          <span className="flex items-center gap-1">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>{code.split("\n").length} lines</span>
          </span>
        </div>
      </div>

      {/* Monaco Editor Container */}
      <div className="relative flex-1 overflow-hidden">
        {/* Scanning beam animation when loading */}
        {isLoading && (
          <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#22D3EE] z-20 pointer-events-none animate-scan" />
        )}

        <Editor
          height="100%"
          language="python"
          value={code}
          onChange={(newVal) => setCode(newVal || "")}
          onMount={handleEditorDidMount}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', monospace",
            minimap: { enabled: false },
            lineNumbers: "on",
            glyphMargin: true,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            smoothScrolling: true,
            cursorBlinking: "smooth",
            renderLineHighlight: "all",
            padding: { top: 12, bottom: 12 },
          }}
        />
      </div>
    </div>
  );
};

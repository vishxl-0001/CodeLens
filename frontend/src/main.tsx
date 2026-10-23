import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

// Suppress Monaco Editor internal cancellation noise (microsoft/monaco-editor#5458)
// In WebKit/Safari, Monaco registers a click/keydown listener on document.body
// for its async clipboard workaround which aborts a DeferredPromise on each click
// and erroneously logs 'ERR Canceled: Canceled' via its internal ConsoleLogger.
if (typeof window !== "undefined") {
  window.addEventListener("unhandledrejection", (event) => {
    if (
      event.reason?.name === "Canceled" ||
      event.reason?.message === "Canceled" ||
      event.reason?.toString()?.includes("Canceled")
    ) {
      event.preventDefault();
    }
  });

  const originalConsoleError = console.error;
  console.error = (...args: any[]) => {
    const isMonacoCancel = args.some(
      (arg) =>
        arg?.name === "Canceled" ||
        arg?.message === "Canceled" ||
        (typeof arg === "string" && arg.includes("Canceled"))
    );
    if (isMonacoCancel) {
      return;
    }
    originalConsoleError.apply(console, args);
  };
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);


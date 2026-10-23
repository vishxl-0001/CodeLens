/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        darkBg: "#0A0B10",
        darkSurface: "#12141C",
        darkSurface2: "#191C27",
        darkBorder: "rgba(255, 255, 255, 0.08)",
        lightBg: "#F8FAFC",
        lightSurface: "#FFFFFF",
        lightSurface2: "#F1F5F9",
        lightBorder: "rgba(0, 0, 0, 0.08)",
        critical: "#EF4444",
        high: "#F97316",
        medium: "#EAB308",
        low: "#38BDF8",
        success: "#22C55E",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        glow: "0 0 25px -5px rgba(99, 102, 241, 0.25)",
        card: "0 10px 30px -10px rgba(0, 0, 0, 0.5)",
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        float: "float 6s ease-in-out infinite",
        scan: "scan 2s ease-in-out infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        scan: {
          "0%": { top: "0%", opacity: "0" },
          "50%": { opacity: "0.8" },
          "100%": { top: "100%", opacity: "0" },
        },
      },
    },
  },
  plugins: [],
};

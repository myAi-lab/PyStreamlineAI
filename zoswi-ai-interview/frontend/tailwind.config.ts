import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        background: "#f6f8f4",
        surface: "#ffffff",
        ink: "#101828",
        accent: "#0f766e",
        accentSoft: "#ccfbf1"
      },
      boxShadow: {
        panel: "0 18px 38px rgba(16, 24, 40, 0.1)"
      }
    }
  },
  plugins: []
};

export default config;


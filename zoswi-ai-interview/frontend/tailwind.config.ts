import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./services/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        heading: ["var(--font-heading)"],
        body: ["var(--font-body)"]
      },
      colors: {
        surface: "#081323",
        card: "#11213a",
        brand: {
          50: "#edfdfe",
          100: "#cff9fb",
          200: "#a2f0f6",
          300: "#67e2ef",
          400: "#2bcadf",
          500: "#14a8c0",
          600: "#14869f",
          700: "#166c81",
          800: "#1a5869",
          900: "#1b4a58"
        }
      },
      boxShadow: {
        soft: "0 20px 45px -18px rgba(8, 19, 35, 0.55)"
      }
    }
  },
  plugins: []
};

export default config;

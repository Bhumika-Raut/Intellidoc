/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Outfit", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Fraunces", "Georgia", "serif"],
      },
      colors: {
        ink: {
          50: "#f7f5f1",
          100: "#ece7de",
          800: "#2a2620",
          900: "#161410",
        },
        moss: {
          500: "#0f6b5c",
          400: "#2a9a84",
          300: "#5dcaa9",
        },
      },
      boxShadow: {
        card: "0 1px 2px rgba(22,20,16,0.06), 0 12px 32px -16px rgba(22,20,16,0.18)",
      },
    },
  },
  plugins: [],
};

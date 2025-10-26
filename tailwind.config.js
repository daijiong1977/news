/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./genweb/**/*.html",
    "./website/main/**/*.html",
    "./website/generated/**/*.html",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: "#359EFF",
        secondary: "#14b8a6",
        "background-light": "#f5f7f8",
        "background-dark": "#0f1923",
        "text-light": "#09090b",
        "text-dark": "#fafafa",
        "subtle-light": "#71717a",
        "subtle-dark": "#a1a1aa",
        "border-light": "#e4e4e7",
        "border-dark": "#27272a",
        "card-light": "#f4f4f5",
        "card-dark": "#27272a",
      },
      fontFamily: {
        display: "Literata",
        sans: ["Inter", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        lg: "1rem",
        xl: "1.5rem",
        full: "9999px",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/container-queries"),
  ],
}

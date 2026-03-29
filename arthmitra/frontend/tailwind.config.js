/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        mentor: {
          bg: "#070b14",
          panel: "#0f172a",
          neon: "#22d3ee",
          gold: "#fbbf24",
        },
      },
    },
  },
  plugins: [],
};


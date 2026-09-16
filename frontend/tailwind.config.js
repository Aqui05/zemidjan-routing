/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js}"],
  theme: {
    extend: {
      colors: {
        primary: "#1B8A5A",
        secondary: "#2E7DD1",
        warning: "#E0A100",
        danger: "#D34C4C",
      },
    },
  },
  plugins: [],
};

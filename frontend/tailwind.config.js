/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#0f0f0f",
        panel: "#171717",
        border: "#262626",
        accent: {
          DEFAULT: "#7c3aed",
          hover: "#6d28d9",
        },
      },
    },
  },
  plugins: [],
}


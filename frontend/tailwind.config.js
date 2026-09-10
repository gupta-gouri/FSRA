/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "#0f172a", // Slate 900
          foreground: "#f8fafc",
        },
        secondary: {
          DEFAULT: "#334155", // Slate 700
          foreground: "#f8fafc",
        },
        accent: {
          DEFAULT: "#2563eb", // Blue 600
          foreground: "#ffffff",
        },
        success: {
          DEFAULT: "#059669", // Emerald 600
          light: "#d1fae5",
        },
        warning: {
          DEFAULT: "#d97706", // Amber 600
          light: "#fef3c7",
        },
        danger: {
          DEFAULT: "#dc2626", // Red 600
          light: "#fee2e2",
        }
      },
    },
  },
  plugins: [],
}

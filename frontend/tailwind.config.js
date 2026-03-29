/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'trust-blue': '#2563eb',
        'engagement-blue': '#3b82f6',
        'growth-green': '#10b981',
        'caution-orange': '#f59e0b',
        'alert-red': '#ef4444',
      }
    },
  },
  plugins: [],
}
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        intel: {
          bg: '#f8f9fa',
          sidebar: '#ffffff',
          primary: '#2563eb', // blue-600
          text: '#1f2937', // gray-800
          muted: '#6b7280', // gray-500
        }
      }
    },
  },
  plugins: [],
}

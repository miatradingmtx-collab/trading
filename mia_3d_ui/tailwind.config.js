/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'mia-magenta': '#e91e63',
        'mia-cyan': '#00ffa3',
        'mia-dark': '#08080c',
        'mia-panel': 'rgba(15, 15, 20, 0.75)',
      }
    },
  },
  plugins: [],
}

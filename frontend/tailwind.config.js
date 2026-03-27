/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: '#1e3a5f',
        School: {
          DEFAULT: '#FF8200',
          50: '#FFF7ED',
          100: '#FFEDD5',
          600: '#EA7600',
          700: '#C05E00',
        },
      },
    },
  },
  plugins: [],
}

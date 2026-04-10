/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: '#1e3a5f',
        primary: {
          DEFAULT: 'rgb(var(--color-primary, 255 130 0) / <alpha-value>)',
          50: 'rgb(var(--color-primary-50, 255 247 237) / <alpha-value>)',
          100: 'rgb(var(--color-primary-100, 255 237 213) / <alpha-value>)',
          600: 'rgb(var(--color-primary-600, 234 118 0) / <alpha-value>)',
          700: 'rgb(var(--color-primary-700, 192 94 0) / <alpha-value>)',
        },
      },
    },
  },
  plugins: [],
}

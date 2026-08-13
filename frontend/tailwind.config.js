/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eef4ff',
          100: '#d9e7ff',
          200: '#bcd3ff',
          300: '#8eb5ff',
          400: '#598bff',
          500: '#3366ff',
          600: '#1a47f5',
          700: '#1335e1',
          800: '#162cb6',
          900: '#182b8f',
          950: '#111a57',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        lg: '0.625rem',
        md: '0.5rem',
        sm: '0.375rem',
      },
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        aegis: {
          bg: '#0a0e1a',
          panel: '#131826',
          panel2: '#1a2033',
          border: '#252b3d',
          accent: '#00d4ff',
          accent2: '#7c3aed',
          success: '#10b981',
          danger: '#ef4444',
          warning: '#f59e0b',
          text: '#e5e7eb',
          muted: '#9ca3af',
        },
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

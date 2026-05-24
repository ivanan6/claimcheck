/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: { '2xl': '1400px' },
    },
    extend: {
      colors: {
        // shadcn HSL CSS variables (for ui/* components)
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        // Aegis custom tokens (for existing custom components)
        aegis: {
          bg: '#f7f8fb',
          panel: '#ffffff',
          panel2: '#f1f4f9',
          border: '#e5e9f0',
          'border-strong': '#cdd5e0',
          primary: '#0b1f4d',
          'primary-soft': '#1e3a8a',
          accent: '#f97316',
          accent2: '#fb923c',
          'accent-soft': '#fff1e6',
          success: '#0b8a4a',
          'success-soft': '#dcf2e6',
          danger: '#dc2626',
          'danger-soft': '#fde8e8',
          warning: '#d97706',
          'warning-soft': '#fef4e3',
          text: '#0f172a',
          'text-soft': '#334155',
          muted: '#64748b',
          'muted-soft': '#94a3b8',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'aegis-card': '0 1px 2px 0 rgba(11, 31, 77, 0.04), 0 1px 6px -1px rgba(11, 31, 77, 0.06)',
        'aegis-card-hover': '0 6px 16px -4px rgba(11, 31, 77, 0.1), 0 2px 6px -1px rgba(11, 31, 77, 0.06)',
        'aegis-ring-primary': '0 0 0 4px rgba(11, 31, 77, 0.1)',
        'aegis-ring-accent': '0 0 0 4px rgba(249, 115, 22, 0.15)',
        'aegis-ring-danger': '0 0 0 4px rgba(220, 38, 38, 0.12)',
        'aegis-ring-success': '0 0 0 4px rgba(11, 138, 74, 0.12)',
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

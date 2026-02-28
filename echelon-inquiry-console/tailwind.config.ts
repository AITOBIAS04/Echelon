import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        echelon: {
          bg: '#FAFBFC',
          surface: '#FFFFFF',
          border: '#E2E8F0',
          navy: '#1E3A5F',
          blue: '#2563EB',
          success: '#059669',
          warning: '#D97706',
          error: '#DC2626',
          'data-text': '#334155',
          'data-bg': '#F1F5F9',
        },
      },
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      maxWidth: {
        container: '1200px',
      },
      keyframes: {
        fadeSlideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulse: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(30, 58, 95, 0.4)' },
          '50%': { boxShadow: '0 0 0 6px rgba(30, 58, 95, 0)' },
        },
        bgPulse: {
          '0%, 100%': { backgroundColor: 'rgb(241 245 249)' },
          '50%': { backgroundColor: 'rgb(226 232 240)' },
        },
      },
      animation: {
        'fade-slide-up': 'fadeSlideUp 150ms ease-out forwards',
        'step-pulse': 'pulse 2s ease-in-out infinite',
        'bg-pulse': 'bgPulse 600ms ease-in-out',
      },
    },
  },
  plugins: [],
} satisfies Config;

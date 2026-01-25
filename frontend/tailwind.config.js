/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      screens: {
        'laptop-compact': { 'raw': '(max-height: 800px)' },
      },
      colors: {
        // Professional trading terminal palette (BullX-style)
        'terminal': {
          'bg': '#0B0C0E',        // Deep charcoal (not pure black)
          'panel': '#151719',     // Slate gray for cards
          'card': '#1A1D21',      // Slightly lighter for hover states
          'border': '#2A2D33',    // Subtle borders
          'border-light': '#363A40', // Hover states
          'text': '#F1F5F9',      // Off-white for readability
          'text-secondary': '#94A3B8',  // Muted text
          'text-muted': '#64748B', // Deeper muted
        },
        // Functional colours (muted, not neon)
        'status': {
          'success': '#10B981',   // Emerald - growth, active
          'warning': '#F59E0B',   // Muted amber - at risk
          'danger': '#EF4444',    // Crimson - breaches, critical
          'info': '#3B82F6',      // Blue - neutral info
          'paradox': '#8B5CF6',   // Soft purple - paradox events
        },
        // Agent archetype colours (more refined)
        'agent': {
          'shark': '#EF4444',     // Crimson - aggressive
          'spy': '#8B5CF6',       // Soft purple - mysterious
          'diplomat': '#3B82F6',  // Blue - calm, cooperative
          'saboteur': '#F59E0B',  // Amber - disruptive
          'whale': '#10B981',     // Emerald - capital
          'degen': '#F97316',     // Orange - high risk
        },
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}

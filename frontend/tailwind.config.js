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
        // Cool grey with dark slate accents (ECHELON Signal Intelligence style)
        'slate': {
          '950': '#0B0C0E', // Deepest layer - main content areas
          '900': '#121417', // Card/Section surface
          '850': '#151719', // Panel backgrounds
          '800': '#1A1D21', // Header & elevated elements - cool grey main
          '750': '#26292E', // Borders & dividers
          '700': '#363A40', // Hover states
          '600': '#4B5563', // Secondary borders
          '500': '#6B7280', // Muted text
          '400': '#9CA3AF', // Secondary text
          '300': '#D1D5DB', // Primary text
          '200': '#E5E7EB', // High contrast text
          '100': '#F3F4F6', // brightest text
        },
        // Professional trading terminal palette (BullX-style) - cool grey scheme
        'terminal': {
          'bg': '#1A1D21',      // Cool grey main background (slate-800)
          'panel': '#151719',   // Panel backgrounds (slate-850)
          'card': '#121417',    // Card surfaces (slate-900)
          'border': '#26292E',  // Borders (slate-750)
          'border-light': '#363A40',  // Hover states (slate-700)
          'text': '#F1F5F9',    // Primary text
          'text-secondary': '#94A3B8',  // Secondary text
          'text-muted': '#64748B',  // Muted text
        },
        // Functional colours (muted, not neon)
        'status': {
          'success': '#4ADE80',   // Emerald green - growth, positive
          'warning': '#FACC15',   // Gold - at risk, evidence flip
          'danger': '#FB7185',    // Rose red - breaches, negative
          'info': '#3B82F6',      // Blue - neutral info
          'paradox': '#8B5CF6',   // Soft purple - paradox events
          'vrf': '#8B5CF6',       // VRF verification - purple
          'entropy': '#06B6D4',   // Entropy quality - cyan
          'cyan': '#22D3EE',      // Cyan for RLMF
        },
        // Echelon accent colours (semantic aliases for cross-page use)
        'echelon': {
          'cyan': '#22D3EE',
          'green': '#4ADE80',
          'red': '#EF4444',
          'amber': '#F59E0B',
          'purple': '#A855F7',
          'blue': '#3B82F6',
        },
        // Agent archetype colours (more refined)
        'agent': {
          'shark': '#FB7185',     // Rose red - aggressive
          'spy': '#8B5CF6',       // Soft purple - mysterious
          'diplomat': '#3B82F6',  // Blue - calm, cooperative
          'saboteur': '#FACC15',  // Gold - disruptive
          'whale': '#4ADE80',     // Emerald - capital
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

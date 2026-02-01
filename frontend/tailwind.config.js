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
        // Glassmorphism System (New Deck Aligned)
        'glass': {
          'bg': '#030305',      // Deep Charcoal Background
          'card': 'rgba(255, 255, 255, 0.03)', // Semi-transparent card
          'border': 'rgba(255, 255, 255, 0.1)', // Razor-thin border
          'border-light': 'rgba(255, 255, 255, 0.2)',
          'text': '#F3F4F6',
          'text-secondary': '#9CA3AF',
          'text-muted': '#6B7280',
        },
        // Signal System (Functional Meaning)
        'signal': {
          'action': '#3B82F6',   // Electric Blue (Primary Actions)
          'success': '#10B981',  // Emerald Green (Profit/Success)
          'risk': '#F59E0B',     // Amber (Risk)
          'sabotage': '#EF4444', // Red (Sabotage/Danger)
          'muted': '#6B7280',    // Grey (Secondary/Borders)
        },
        // Professional trading terminal palette (Legacy compatibility mapped to new style)
        'terminal': {
          'bg': '#030305',      // Deep Charcoal
          'panel': 'rgba(255, 255, 255, 0.03)',
          'card': 'rgba(255, 255, 255, 0.03)',
          'border': 'rgba(255, 255, 255, 0.1)',
          'border-light': 'rgba(255, 255, 255, 0.2)',
          'text': '#F3F4F6',    // Primary text
          'text-secondary': '#9CA3AF',  // Secondary text
          'text-muted': '#6B7280',  // Muted text
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
        // Echelon accent colours (used across agents, analytics, etc.)
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

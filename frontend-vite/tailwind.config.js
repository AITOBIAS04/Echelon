/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Core terminal colours
        'terminal': {
          'bg': '#0a0a0f',
          'panel': '#12121a',
          'border': '#1e1e2e',
          'text': '#e0e0e0',
          'muted': '#6b7280',
        },
        // Status colours
        'echelon': {
          'green': '#00ff88',      // Stable, success
          'red': '#ff3366',        // Critical, danger
          'amber': '#ffaa00',      // Warning
          'blue': '#00aaff',       // Info, neutral
          'purple': '#aa66ff',     // Paradox, special
          'cyan': '#00ffff',       // Highlight
        },
        // Agent archetype colours
        'agent': {
          'shark': '#ff3366',      // Aggressive red
          'spy': '#aa66ff',        // Mysterious purple
          'diplomat': '#00aaff',   // Calm blue
          'saboteur': '#ffaa00',   // Warning amber
          'whale': '#00ff88',      // Money green
        },
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
        'display': ['Orbitron', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan': 'scan 2s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px currentColor' },
          '100%': { boxShadow: '0 0 20px currentColor' },
        },
      },
    },
  },
  plugins: [],
}


import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    '__BUILD_ID__': JSON.stringify(
      new Date().toISOString().slice(0, 16).replace('T', ' ') + ' UTC'
    ),
    '__BUILD_HASH__': JSON.stringify(
      Math.random().toString(36).slice(2, 8)
    ),
  },
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        // Add timestamp to bundle filename to force cache busting
        entryFileNames: `assets/[name]-[hash]-${Date.now()}.js`,
        chunkFileNames: `assets/[name]-[hash]-${Date.now()}.js`,
        assetFileNames: `assets/[name]-[hash]-${Date.now()}.[ext]`,
      },
    },
  },
})

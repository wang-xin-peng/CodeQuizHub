import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ['decimal.js', 'decimal.js-light', 'recharts'],
    esbuild: {
      target: 'es2020',
    },
  },
  server: {
    port: 5173,
    watch: {
      usePolling: process.env.VITE_USE_POLLING === 'true',
      interval: 1000,
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY || 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: process.env.VITE_WS_PROXY || 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})

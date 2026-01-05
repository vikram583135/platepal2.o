import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  // Ensure the app root is this folder (not the repo root)
  root: __dirname,
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '../../'),
      '@/packages': path.resolve(__dirname, '../../packages'),
    },
  },
  server: {
    port: 3022,
    host: true,
    open: false,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['framer-motion', 'lucide-react'],
          maps: ['leaflet', 'react-leaflet'],
        },
      },
    },
  },
  preview: {
    port: 3022,
    host: true,
  },
})



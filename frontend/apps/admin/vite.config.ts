import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '../../'),
      '@/packages': path.resolve(__dirname, '../../packages'),
    },
  },
  server: {
    port: 3023,
  },
  build: {
    outDir: 'dist',
  },
})


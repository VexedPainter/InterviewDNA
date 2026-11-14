import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    host: 'localhost',
    watch: {
      ignored: [
        '**/node_modules/**',
        '**/.git/**',
        '**/chroma_db/**',
        '**/data/**',
        '**/*.db',
        '**/*.pdf',
        '**/*.csv',
        '**/logs/**',
        '**/venv/**',
        '**/.pytest_cache/**',
      ],
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})

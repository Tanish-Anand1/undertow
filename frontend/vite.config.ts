import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/watchlists': 'http://127.0.0.1:8000',
      '/feed': 'http://127.0.0.1:8000',
      '/digest': 'http://127.0.0.1:8000',
      '/stats': 'http://127.0.0.1:8000',
      '/posts': 'http://127.0.0.1:8000',
      '/ingest': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})

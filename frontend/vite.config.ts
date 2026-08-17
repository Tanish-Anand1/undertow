import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

const root = path.dirname(fileURLToPath(import.meta.url))

function appHtml(): Plugin {
  return {
    name: 'app-html',
    configureServer(server) {
      server.middlewares.use((req, _res, next) => {
        const url = (req.url || '').split('?')[0]
        if (url === '/app' || url.startsWith('/app/') || url === '/ledger' || url.startsWith('/ledger/')) {
          req.url = '/app.html'
        }
        next()
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), appHtml()],
  build: {
    target: 'es2022',
    cssMinify: true,
    modulePreload: { polyfill: false },
    rollupOptions: {
      input: {
        index: path.resolve(root, 'index.html'),
        app: path.resolve(root, 'app.html'),
      },
    },
  },
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
      '/admin': 'http://127.0.0.1:8000',
      '/presence': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})

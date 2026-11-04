import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { proxyOriginDiagnostics } from './dev/proxyOriginDiagnostics.ts'

const target = process.env.KEVIN_TEST_BACKEND_URL || 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  server: { proxy: { '/api': { target, changeOrigin: true,
    configure: process.env.KEVIN_TEST_BACKEND_URL ? proxyOriginDiagnostics : undefined,
  } } },
  plugins: [
    react(),
    tailwindcss(),
  ],
})

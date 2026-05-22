import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import mkcert from 'vite-plugin-mkcert'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  plugins: [vue(), mkcert({
    hosts: ['192.168.0.190']
  })],
  server: {
    https: true,
    port: 5173,
    host: true,
    proxy: {
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/companies': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/employees': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/calculate-payroll': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/calculate-reverse-payroll': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/payroll-runs': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/payroll-records': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/payroll': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/generate-payslip': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/dashboard': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/reports': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/audit': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/me': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/leave': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/compliance': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})

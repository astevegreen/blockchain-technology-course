import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  // Base path configuration:
  // - Dev: / (localhost)
  // - Build: Use VITE_BASE_PATH env var, default to / for Docker
  // - For GitHub Pages, set VITE_BASE_PATH=/ethereum-lab/ during build
  base: command === 'build' ? (process.env.VITE_BASE_PATH || '/') : '/',
  server: {
    host: true,
    port: 5173,
    // Avoid silently switching ports (breaks our PowerShell automation + student setup redirect)
    strictPort: true,
    proxy: {
      '/lab-api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            const forwarded = req.headers['x-forwarded-for'] || req.socket?.remoteAddress || '';
            if (forwarded) proxyReq.setHeader('X-Forwarded-For', forwarded);
          });
        }
      },
      '/ws/terminal': {
        target: 'ws://localhost:3002',
        ws: true
      }
    }
  }
}))

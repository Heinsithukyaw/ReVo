import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 12000,  // ✅ CONSISTENT
    host: '0.0.0.0',
    strictPort: false,  // ✅ FIXED: Allow port flexibility
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:12001',  // ✅ FIXED: Consistent with backend
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('Proxy error:', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
      '/ws': {
        target: 'ws://localhost:12001',  // ✅ FIXED: Consistent WebSocket
        ws: true,
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:12001',  // ✅ ADDED: Health check proxy
        changeOrigin: true,
        secure: false,
      }
    },
  },
  // ADDED: Environment variable configuration
  define: {
    'process.env': process.env,
    __DEV__: JSON.stringify(true),
  },
  // ADDED: Build configuration for production
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['framer-motion', 'lucide-react'],
        }
      }
    }
  },
})

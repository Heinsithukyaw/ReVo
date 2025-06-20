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
  // ADDED: Environment variable configuration (SECURITY FIX)
  define: {
    'process.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || 'http://localhost:12001'),
    'process.env.VITE_WS_URL': JSON.stringify(process.env.VITE_WS_URL || 'ws://localhost:12001'),
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
    'process.env.VITE_ENABLE_LLM_FEATURES': JSON.stringify(process.env.VITE_ENABLE_LLM_FEATURES || 'true'),
    'process.env.VITE_ENABLE_FALLBACK_SYSTEM': JSON.stringify(process.env.VITE_ENABLE_FALLBACK_SYSTEM || 'true'),
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

import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

const apiTarget = process.env.VITE_STEEL_REALTIME_PROXY_TARGET || 'http://127.0.0.1:8019';

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': apiTarget,
      '/risk': apiTarget,
      '/identify': apiTarget,
      '/assets': apiTarget,
    },
  },
  preview: {
    host: '127.0.0.1',
    port: 5174,
  },
});

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // 10/12 통합 시 백엔드 API 프록시가 필요하면 여기에 추가
    // proxy: { '/api': 'http://localhost:8000' },
  },
});

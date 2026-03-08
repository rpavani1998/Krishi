import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'https://zngsqikkpa.execute-api.ap-south-1.amazonaws.com/dev', // AWS API Gateway
        // target: 'http://localhost:8000', // Local Backend
        changeOrigin: true,
        secure: false,
      }
    }
  }
})

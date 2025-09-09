import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
const path = require('path')

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  build: {
    outDir: 'dist',
    lib: {
      entry: path.resolve(__dirname, 'src/main.js'),
      name: 'OneLms',
      fileName: 'one-lms'
    },
    rollupOptions: {
      external: ['vue', 'frappe-ui'],
      output: {
        globals: {
          vue: 'Vue',
          'frappe-ui': 'FrappeUI'
        }
      }
    }
  }
})

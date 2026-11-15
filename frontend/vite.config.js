import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon.svg'],
      manifest: {
        name: 'BASAL · Monitoreo de salud autónomo',
        short_name: 'BASAL',
        description: 'Monitoreo de salud de astronautas sin conexión con la Tierra',
        theme_color: '#0b3d91',
        background_color: '#f4f6fa',
        display: 'standalone',
        lang: 'es',
        icons: [{ src: 'icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' }]
      },
      workbox: {
        navigateFallbackDenylist: [/^\/api/, /^\/docs/],
        globPatterns: ['**/*.{js,css,html,svg,jpg,png,woff,woff2,webmanifest}']
      }
    })
  ],
  build: { chunkSizeWarningLimit: 1200 },
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } }
})

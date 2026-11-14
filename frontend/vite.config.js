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
        theme_color: '#081525',
        background_color: '#081525',
        display: 'standalone',
        lang: 'es',
        icons: [{ src: 'icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' }]
      },
      workbox: { navigateFallbackDenylist: [/^\/api/] }
    })
  ],
  build: { chunkSizeWarningLimit: 1200 },
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } }
})

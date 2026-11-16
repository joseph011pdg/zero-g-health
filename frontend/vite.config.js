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
        name: 'Zero G Health · Autonomous crew health monitoring',
        short_name: 'Zero G Health',
        description: 'Astronaut health monitoring without a link to Earth',
        theme_color: '#0a1f44',
        background_color: '#f4f6fa',
        display: 'standalone',
        lang: 'en',
        icons: [{ src: 'icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' }]
      },
      workbox: {
        //ACTUALIZACIÓN inmediata: el jurado nunca ve una versión vieja en caché
        skipWaiting: true,
        clientsClaim: true,
        cleanupOutdatedCaches: true,
        navigateFallbackDenylist: [/^\/api/, /^\/docs/, /\.pdf$/],
        globPatterns: ['**/*.{js,css,html,svg,jpg,png,woff,woff2,webmanifest}']
      }
    })
  ],
  build: { chunkSizeWarningLimit: 1200 },
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } }
})

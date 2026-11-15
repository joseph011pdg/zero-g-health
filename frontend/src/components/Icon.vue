<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" :stroke-width="stroke"
       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" class="ic" v-html="PATHS[name] || ''" />
</template>

<script setup>
defineProps({ name: String, size: { type: [Number, String], default: 16 }, stroke: { type: Number, default: 2 } })

// Iconos de trazo propios (sin dependencias ni CDN)
const PATHS = {
  check: '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.6 2.5L16 9.5"/>',
  triangle: '<path d="M12 3.5 2.8 19.5h18.4z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
  octagon: '<path d="M8.2 3h7.6L21 8.2v7.6L15.8 21H8.2L3 15.8V8.2z"/><path d="M12 8v5"/><path d="M12 16h.01"/>',
  dashed: '<path d="M12 3a9 9 0 0 1 3 .5M19 6.5a9 9 0 0 1 1.7 3M21 14a9 9 0 0 1-1.5 3.4M16 20.1a9 9 0 0 1-3.5.9M8 20.1a9 9 0 0 1-3-2.2M3.2 14.5A9 9 0 0 1 3 12M3.6 8.5A9 9 0 0 1 6 5"/>',
  minus: '<circle cx="12" cy="12" r="9"/><path d="M8 12h8"/>',
  heart: '<path d="M19.5 12.6 12 20l-7.5-7.4A4.8 4.8 0 0 1 12 6.6a4.8 4.8 0 0 1 7.5 6z"/>',
  activity: '<path d="M3 12h4l2.5-6 4 12 2.5-6H21"/>',
  moon: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
  radiation: '<circle cx="12" cy="12" r="1.6"/><path d="M12 3.5a8.5 8.5 0 0 1 7.4 4.3l-4.6 2.6A3.2 3.2 0 0 0 12 8.8z"/><path d="M4.6 7.8A8.5 8.5 0 0 1 12 3.5v5.3a3.2 3.2 0 0 0-2.8 1.6z" opacity=".0"/><path d="M4.6 16.2a8.5 8.5 0 0 1 0-8.4l4.6 2.6a3.2 3.2 0 0 0 0 3.2z"/><path d="M19.4 16.2A8.5 8.5 0 0 1 12 20.5v-5.3a3.2 3.2 0 0 0 2.8-1.6z"/>',
  target: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r=".8"/>',
  smile: '<circle cx="12" cy="12" r="9"/><path d="M8.5 14.5a4.5 4.5 0 0 0 7 0"/><path d="M9 9.5h.01M15 9.5h.01"/>',
  satellite: '<path d="m13 7 4 4"/><path d="m4.5 13.5 6-6 6 6-6 6z"/><path d="M15 3.5a5.5 5.5 0 0 1 5.5 5.5"/><path d="M15 6.5A2.5 2.5 0 0 1 17.5 9"/>',
  signalOff: '<path d="M3 3l18 18"/><path d="M8.5 16.5a5 5 0 0 1 7 0"/><path d="M5 12.8a10 10 0 0 1 3.4-2.2M19 12.8a10 10 0 0 0-5.1-2.7"/><path d="M12 20h.01"/>',
  server: '<rect x="3.5" y="4" width="17" height="7" rx="2"/><rect x="3.5" y="13" width="17" height="7" rx="2"/><path d="M7 7.5h.01M7 16.5h.01"/>',
  play: '<path d="M7 4.5v15l12-7.5z"/>',
  pause: '<path d="M8 5v14M16 5v14"/>',
  next: '<path d="M6 5l8 7-8 7z"/><path d="M18 5v14"/>',
  prev: '<path d="M18 5l-8 7 8 7z"/><path d="M6 5v14"/>',
  reset: '<path d="M4 12a8 8 0 1 0 2.3-5.7"/><path d="M4 4v4.5h4.5"/>',
  file: '<path d="M14 3.5H7a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8.5z"/><path d="M14 3.5v5h5"/><path d="M9 13h6M9 16.5h4"/>',
  download: '<path d="M12 4v11"/><path d="m7.5 10.5 4.5 4.5 4.5-4.5"/><path d="M4.5 19.5h15"/>',
  upload: '<path d="M12 20V9"/><path d="m7.5 13.5 4.5-4.5 4.5 4.5"/><path d="M4.5 4.5h15"/>',
  send: '<path d="M21 3 10 14"/><path d="M21 3l-7 18-4-7-7-4z"/>',
  flask: '<path d="M9.5 3.5h5"/><path d="M10.5 3.5v5.5L5 18.5a1.5 1.5 0 0 0 1.3 2.2h11.4a1.5 1.5 0 0 0 1.3-2.2L13.5 9V3.5"/><path d="M7.5 14.5h9"/>',
  book: '<path d="M4.5 5.5A2 2 0 0 1 6.5 3.5H19.5v15H6.5a2 2 0 0 0-2 2z"/><path d="M4.5 20.5v-15"/><path d="M8.5 7.5h7"/>',
  user: '<circle cx="12" cy="8" r="3.8"/><path d="M4.5 20.5a7.5 7.5 0 0 1 15 0"/>',
  users: '<circle cx="9" cy="8.5" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M15.5 5.2a3.5 3.5 0 0 1 0 6.6"/><path d="M18 14.2a6.5 6.5 0 0 1 3.5 5.8"/>',
  clipboard: '<rect x="5" y="4.5" width="14" height="16.5" rx="2"/><path d="M9 4.5V3.2h6v1.3"/><path d="M8.5 11h7M8.5 14.5h7M8.5 18h4"/>',
  stethoscope: '<path d="M5 3.5v5a5 5 0 0 0 10 0v-5"/><path d="M10 13.5v2a4.5 4.5 0 0 0 9 0v-2"/><circle cx="19" cy="11.5" r="2"/>',
  cpu: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9.5 9.5h5v5h-5z"/><path d="M9 2.5v3M15 2.5v3M9 18.5v3M15 18.5v3M2.5 9h3M2.5 15h3M18.5 9h3M18.5 15h3"/>',
  chevron: '<path d="m9 6 6 6-6 6"/>',
  close: '<path d="M6 6l12 12M18 6 6 18"/>',
  compass: '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5z"/>',
  layers: '<path d="m12 3.5 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
  printer: '<path d="M7 8.5V3.5h10v5"/><rect x="3.5" y="8.5" width="17" height="8" rx="2"/><path d="M7 14h10v6.5H7z"/>',
  trendUp: '<path d="M3.5 17 9.5 11l4 4 7-7.5"/><path d="M15 7.5h5.5V13"/>',
  trendDown: '<path d="M3.5 7 9.5 13l4-4 7 7.5"/><path d="M15 16.5h5.5V11"/>',
  trendFlat: '<path d="M3.5 12h17"/><path d="m16 7.5 4.5 4.5-4.5 4.5"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5"/><path d="M12 7.8h.01"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  bell: '<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
  spark: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/>'
}
</script>

<style scoped>
.ic { flex: none; display: inline-block; vertical-align: middle; }
</style>

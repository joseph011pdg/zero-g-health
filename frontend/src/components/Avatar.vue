<template>
  <img class="avatar-img" :src="src" :alt="`Retrato ilustrado de ${name}`" :width="size" :height="size" @error="fallback" />
</template>

<script setup>
import { ref, watch } from 'vue'
// Retratos ilustrados de la tripulación ficticia (public/img/crew). Perfiles nuevos: casco genérico.
const KNOWN = ['A1', 'A2', 'A3', 'A4']
const props = defineProps({ id: String, name: { type: String, default: '' }, size: { type: Number, default: 56 } })
const src = ref('')
watch(() => props.id, (id) => { src.value = `/img/crew/${KNOWN.includes(id) ? id : 'default'}.svg` }, { immediate: true })
function fallback() { src.value = '/img/crew/default.svg' }
</script>

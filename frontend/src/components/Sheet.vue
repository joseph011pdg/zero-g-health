<template>
  <div class="overlay" @click.self="$emit('close')">
    <div class="sheet" role="dialog" aria-modal="true" :aria-label="title" ref="box" tabindex="-1">
      <header class="row between">
        <h2>{{ title }}</h2>
        <button class="btn ghost sm" @click="$emit('close')" aria-label="Close"><Icon name="close" :size="16" /></button>
      </header>
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import Icon from './Icon.vue'
defineProps({ title: String })
const emit = defineEmits(['close'])
const box = ref(null)
const onKey = (e) => { if (e.key === 'Escape') emit('close') }
onMounted(() => { box.value?.focus(); window.addEventListener('keydown', onKey) })
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.overlay { position: fixed; inset: 0; background: rgba(11, 27, 51, 0.35); display: grid; place-items: center; z-index: 60; padding: 16px; }
.sheet { background: var(--surface); border-radius: 18px; padding: 20px 22px; width: min(560px, 100%); max-height: calc(100vh - 32px); overflow-y: auto; display: grid; gap: 16px; box-shadow: 0 24px 60px rgba(11, 27, 51, 0.25); outline: none; }
</style>

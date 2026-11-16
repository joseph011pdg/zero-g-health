<template>
  <Sheet :title="`Check-in: ${astro.nombre}`" @close="$emit('close')">
    <form class="grid" @submit.prevent="save" @input="start">
      <label class="field"><span>How is your mood? <strong class="num big">{{ animo }}</strong>/10</span>
        <input type="range" min="1" max="10" step="0.5" v-model.number="animo" aria-label="Mood from 1 to 10" />
        <div class="row between tiny muted"><span>Very low</span><span>Excellent</span></div></label>
      <div class="field"><span>How did you sleep last night?</span>
        <div class="seg" role="radiogroup" aria-label="Sleep quality">
          <button v-for="q in Q" :key="q.v" type="button" role="radio" :aria-checked="sueno === q.v" :class="{ on: sueno === q.v }" @click="sueno = q.v; start()">
            <strong>{{ q.v }}</strong><span class="tiny">{{ q.l }}</span></button>
        </div></div>
      <label class="field"><span>Notes (optional)</span>
        <textarea class="input" v-model="notas" maxlength="500" placeholder="Symptoms or anything you want to share" /></label>
      <button class="btn primary full" type="submit" :disabled="!sueno || busy">Save check-in</button>
    </form>
  </Sheet>
</template>

<script setup>
import { ref } from 'vue'
import Sheet from './Sheet.vue'
import { api, useStore } from '../store.js'
const props = defineProps({ astro: Object })
const emit = defineEmits(['close', 'saved'])
const s = useStore()
const Q = [{ v: 1, l: 'Very bad' }, { v: 2, l: 'Bad' }, { v: 3, l: 'Fair' }, { v: 4, l: 'Good' }, { v: 5, l: 'Very good' }]
const animo = ref(7)
const sueno = ref(null)
const notas = ref('')
const busy = ref(false)
let t0 = null
const start = () => { if (!t0) t0 = performance.now() }
async function save() {
  busy.value = true
  try {
    await s.run(() => api(`/astronauts/${props.astro.id}/checkin`, { method: 'POST', body: {
      animo: animo.value, calidad_sueno: sueno.value, notas: notas.value || null,
      segundos: t0 ? (performance.now() - t0) / 1000 : null } }), s.publico ? 'Check-in received (public demo: not saved)' : `Check-in saved (day ${s.day})`)
    await s.refresh()
    emit('saved')
    emit('close')
  } finally { busy.value = false }
}
</script>

<style scoped>
.big { font-size: 1.2rem; color: var(--blue); }
.seg { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; }
.seg button { display: grid; gap: 2px; padding: 10px 4px; min-height: 56px; border-radius: 12px; background: var(--surface-2); border: 1px solid var(--line-soft); cursor: pointer; color: var(--text); }
.seg button.on { border-color: var(--blue); background: var(--blue-soft); color: var(--blue); }
.full { justify-content: center; min-height: 48px; }
</style>

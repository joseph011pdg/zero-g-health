<template>
  <Sheet :title="`Check-in · ${astro.nombre}`" @close="$emit('close')">
    <form class="grid" @submit.prevent="save" @input="start">
      <label class="field"><span>¿Cómo está su ánimo? <strong class="num big">{{ animo }}</strong>/10</span>
        <input type="range" min="1" max="10" step="0.5" v-model.number="animo" aria-label="Ánimo de 1 a 10" />
        <div class="row between tiny muted"><span>Muy bajo</span><span>Excelente</span></div></label>
      <div class="field"><span>¿Cómo durmió anoche?</span>
        <div class="seg" role="radiogroup" aria-label="Calidad del sueño">
          <button v-for="q in Q" :key="q.v" type="button" role="radio" :aria-checked="sueno === q.v" :class="{ on: sueno === q.v }" @click="sueno = q.v; start()">
            <strong>{{ q.v }}</strong><span class="tiny">{{ q.l }}</span></button>
        </div></div>
      <label class="field"><span>Notas (opcional)</span>
        <textarea class="input" v-model="notas" maxlength="500" placeholder="Síntomas o algo que quiera contar" /></label>
      <button class="btn primary full" type="submit" :disabled="!sueno || busy">Guardar check-in</button>
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
const Q = [{ v: 1, l: 'Muy mal' }, { v: 2, l: 'Mal' }, { v: 3, l: 'Regular' }, { v: 4, l: 'Bien' }, { v: 5, l: 'Muy bien' }]
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
      segundos: t0 ? (performance.now() - t0) / 1000 : null } }), `Check-in guardado (día ${s.day})`)
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

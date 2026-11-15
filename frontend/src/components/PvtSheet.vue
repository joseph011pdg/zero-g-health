<template>
  <Sheet :title="`Attention test · ${astro.nombre}`" @close="close">
    <div v-if="phase === 'idle'" class="grid">
      <div class="tabs">
        <button :class="{ on: mode === 'pvtb_3min' }" @click="mode = 'pvtb_3min'">3 minutes</button>
        <button :class="{ on: mode === 'abreviada_60s' }" @click="mode = 'abreviada_60s'">60 s (demo)</button>
      </div>
      <p class="small">Tap the box or press <kbd>Space</kbd> as soon as the number appears. Do not jump the gun.</p>
      <p v-if="mode === 'abreviada_60s'" class="notice warn tiny">Short demo version: not equivalent to the 3-minute PVT-B.</p>
    </div>

    <div class="stage" :class="phase" @pointerdown.prevent="hit" role="button" tabindex="0" aria-label="Response area">
      <button v-if="phase === 'idle'" class="btn primary" @pointerdown.stop @click="start"><Icon name="play" :size="14" /> Start</button>
      <span v-else-if="phase === 'wait'" class="muted">Wait…</span>
      <span v-else-if="phase === 'go'" class="counter num">{{ counter }}</span>
      <span v-else-if="phase === 'early'" class="early">Too early</span>
      <div v-else-if="phase === 'done'" class="result">
        <div class="cols-3">
          <div class="kpi"><span class="v">{{ medianRt }} <small>ms</small></span><span class="tiny muted">Typical reaction</span></div>
          <div class="kpi"><span class="v">{{ lapses }}</span><span class="tiny muted">Lapses (≥ 355 ms)</span></div>
          <div class="kpi"><span class="v">{{ falseStarts + fastCount }}</span><span class="tiny muted">False starts</span></div>
        </div>
        <p v-if="interruptions" class="tiny c-amarillo">Window switched {{ interruptions }} time(s): it will be saved as invalid.</p>
      </div>
    </div>

    <div v-if="['wait', 'go', 'early'].includes(phase)" class="row between small muted">
      <span>{{ remaining }} s left</span>
      <button class="btn ghost sm" @pointerdown.stop @click="cancel">Cancel</button>
    </div>
    <div v-if="phase === 'done'" class="row between">
      <button class="btn" @click="phase = 'idle'">Repeat</button>
      <button class="btn primary" @click="save" :disabled="busy">Save result</button>
    </div>
  </Sheet>
</template>

<script setup>
// PVT-B: intervalos de 2–5 s, lapso ≥ 355 ms, anticipación < 100 ms (Basner et al., 2011). Reloj monotónico.
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import Sheet from './Sheet.vue'
import Icon from './Icon.vue'
import { api, useStore, plural } from '../store.js'

const props = defineProps({ astro: Object })
const emit = defineEmits(['close', 'saved'])
const s = useStore()
const LAPSE = 355
const FAST = 100
const TIMEOUT = 3000
const mode = ref('pvtb_3min')
const phase = ref('idle')
const busy = ref(false)
const rts = ref([])
const falseStarts = ref(0)
const noResp = ref(0)
const interruptions = ref(0)
const counter = ref(0)
const remaining = ref(0)
let onset = 0
let endAt = 0
let timer = null
let raf = null
let durS = 180

const lapses = computed(() => rts.value.filter((r) => r >= LAPSE).length + noResp.value)
const fastCount = computed(() => rts.value.filter((r) => r < FAST).length)
const medianRt = computed(() => {
  const v = rts.value.filter((r) => r >= FAST).sort((a, b) => a - b)
  return v.length ? Math.round(v[Math.floor(v.length / 2)]) : '—'
})

function stop() { clearTimeout(timer); cancelAnimationFrame(raf) }
function start() {
  durS = mode.value === 'pvtb_3min' ? 180 : 60
  rts.value = []; falseStarts.value = 0; noResp.value = 0; interruptions.value = 0
  endAt = performance.now() + durS * 1000
  next()
}
function next() {
  stop()
  remaining.value = Math.max(0, Math.ceil((endAt - performance.now()) / 1000))
  if (performance.now() >= endAt) { phase.value = 'done'; return }
  phase.value = 'wait'
  timer = setTimeout(show, 2000 + Math.random() * 3000)
}
function show() {
  phase.value = 'go'
  counter.value = 0
  raf = requestAnimationFrame(() => {
    onset = performance.now()
    const tick = () => { counter.value = Math.round(performance.now() - onset); if (phase.value === 'go') raf = requestAnimationFrame(tick) }
    tick()
  })
  timer = setTimeout(() => { if (phase.value === 'go') { noResp.value++; next() } }, TIMEOUT)
}
function hit() {
  if (phase.value === 'go' && onset) { rts.value.push(Math.round(performance.now() - onset)); onset = 0; next() }
  else if (phase.value === 'wait') { falseStarts.value++; stop(); phase.value = 'early'; timer = setTimeout(next, 800) }
}
function cancel() { stop(); phase.value = 'idle' }
function close() { stop(); emit('close') }
const onKey = (e) => { if (e.code === 'Space' && ['wait', 'go'].includes(phase.value)) { e.preventDefault(); hit() } }
const onHide = () => { if (['wait', 'go', 'early'].includes(phase.value)) interruptions.value++ }
const onVis = () => { if (document.hidden) onHide() }

async function save() {
  busy.value = true
  try {
    const r = await s.run(() => api(`/astronauts/${props.astro.id}/pvt`, { method: 'POST', body: {
      modo: mode.value, duracion_s: durS, rts: rts.value, anticipaciones: falseStarts.value,
      sin_respuesta: noResp.value, interrupciones: interruptions.value } }))
    s.toast(r.valido ? `${s.publico ? 'Test scored (public demo: not saved)' : 'Test saved'}: ${plural(r.errores, 'lapse', 'lapses')}` : `Invalid test: ${r.motivo_invalido}`, r.valido ? 'ok' : 'err')
    await s.refresh()
    emit('saved')
    emit('close')
  } finally { busy.value = false }
}
onMounted(() => { window.addEventListener('keydown', onKey); window.addEventListener('blur', onHide); document.addEventListener('visibilitychange', onVis) })
onBeforeUnmount(() => { stop(); window.removeEventListener('keydown', onKey); window.removeEventListener('blur', onHide); document.removeEventListener('visibilitychange', onVis) })
</script>

<style scoped>
.stage { height: 260px; display: grid; place-items: center; user-select: none; touch-action: manipulation; border-radius: 16px; background: var(--surface-2); border: 2px solid var(--line-soft); }
.stage.go { border-color: var(--blue); background: var(--blue-soft); }
.counter { font-size: 4rem; font-weight: 700; color: var(--blue); }
.early { color: var(--warn); font-weight: 700; font-size: 1.3rem; }
.result { width: 100%; padding: 0 16px; display: grid; gap: 10px; text-align: center; }
kbd { font-family: var(--mono); background: var(--surface-2); border: 1px solid var(--line); border-radius: 4px; padding: 0 5px; }
</style>

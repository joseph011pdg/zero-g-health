<template>
  <aside class="guided panel no-print" role="dialog" aria-label="Guided demo">
    <div class="row between">
      <div>
        <div class="label">Guided demo, step {{ i + 1 }} of {{ STEPS.length }}</div>
        <h3>{{ step.title }}</h3>
      </div>
      <button class="btn sm ghost" @click="$emit('close')" aria-label="Close"><Icon name="close" :size="14" /></button>
    </div>
    <p class="small">{{ step.text }}</p>
    <p class="tiny muted">Real action: {{ step.action }}</p>
    <div class="dots"><span v-for="(x, j) in STEPS" :key="j" :class="{ on: j === i, done: j < i }" /></div>
    <div class="row between">
      <button class="btn sm" @click="go(i - 1)" :disabled="i === 0 || busy">Back</button>
      <button class="btn sm primary" @click="go(i + 1)" :disabled="i === STEPS.length - 1 || busy">Next <Icon name="chevron" :size="13" /></button>
    </div>
  </aside>
</template>

<script setup>
// Cada paso ejecuta acciones REALES de la API (mover el día, abrir una pantalla). No falsea estados.
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from '../store.js'
import Icon from './Icon.vue'

defineEmits(['close'])
const s = useStore()
const router = useRouter()
const i = ref(0)
const busy = ref(false)

const STEPS = [
  { title: 'Four astronauts, four baselines', day: 40, to: '/', role: 'oficial', action: 'go to day 40 and open the crew view',
    text: 'Each fictional crew member has their own usual values. The system learned the first 14 days of each person.' },
  { title: 'Stable starting point', day: 40, to: '/crew/A1', select: 'A1', role: 'astronauta', action: 'Astronaut role: open Cmdr. Rivera',
    text: 'Six indicators within their usual range. Below, each indicator against this person\'s own usual values.' },
  { title: 'A gradual change begins', day: 49, to: '/crew/A1', select: 'A1', action: 'move to day 49',
    text: 'The simulator injected progressive fatigue from day 44: sleep slowly shortens and PVT-B lapses increase.' },
  { title: 'Relevant deviation, explained alert', day: 54, to: '/crew/A1', select: 'A1', action: 'move to day 54',
    text: 'The alert says what changed, by how much (robust z vs. their baseline), how it was detected, which follow-up is suggested and which source supports it.' },
  { title: 'Another pattern: physiological stress', day: 72, to: '/crew/A3', select: 'A3', action: 'open Eng. Lindqvist on day 72',
    text: 'Resting HR ↑ and variability ↓ at the same time. The fixed population threshold misses it because his resting HR is low.' },
  { title: 'The link with Earth is lost', day: 97, to: '/', action: 'move to day 97 (blackout 95–104)',
    text: 'The header shows NO LINK. Monitoring, alerts and storage keep working on board.' },
  { title: 'The Medical Officer reviews', day: 97, to: '/', action: 'Medical Officer role → Alerts → Acknowledge',
    text: 'Alerts by priority: acknowledge or snooze 24 h; if an Act alert stays unacknowledged for 2 days, it is escalated.', role: 'oficial' },
  { title: 'Report for Earth, queued', day: 97, to: '/reports', action: 'open Reports',
    text: 'Generate the report: it waits in the onboard queue. When the link returns (day 105) it can be transmitted (simulated).' },
  { title: 'How do we know it works?', day: 97, to: '/lab/validation', action: 'open the Validation lab',
    text: 'Compared with a fixed population threshold on 40 missions independent from those used for tuning, including the cases where we do not win.' }
]
const step = computed(() => STEPS[i.value])

async function apply(st) {
  busy.value = true
  try {
    if (st.select) s.select(st.select)
    if (st.role) s.setRole(st.role)
    if (st.day !== undefined && s.day !== st.day) await s.setDay(st.day)
    await router.push(st.to)
  } finally { busy.value = false }
}
async function go(j) { i.value = j; await apply(STEPS[j]) }
onMounted(() => apply(STEPS[0]))
</script>

<style scoped>
.guided { position: fixed; background: #fff; color: var(--ink); right: 18px; bottom: 18px; width: min(380px, calc(100vw - 36px)); z-index: 40; display: grid; gap: 10px; border: 2px solid var(--blue); box-shadow: 0 20px 50px rgba(11,27,51,.2); }
.dots { display: flex; gap: 5px; }
.dots span { width: 18px; height: 4px; border-radius: 2px; background: var(--line); }
.dots span.done { background: var(--blue); opacity: .5; }
.dots span.on { background: var(--blue); }
</style>

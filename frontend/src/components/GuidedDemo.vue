<template>
  <aside class="guided panel no-print" role="dialog" aria-label="Demo guiada">
    <div class="row between">
      <div>
        <div class="label">Demo guiada · paso {{ i + 1 }} de {{ STEPS.length }}</div>
        <h3>{{ step.title }}</h3>
      </div>
      <button class="btn sm ghost" @click="$emit('close')" aria-label="Cerrar"><Icon name="close" :size="14" /></button>
    </div>
    <p class="small">{{ step.text }}</p>
    <p class="tiny muted">Acción real: {{ step.action }}</p>
    <div class="dots"><span v-for="(x, j) in STEPS" :key="j" :class="{ on: j === i, done: j < i }" /></div>
    <div class="row between">
      <button class="btn sm" @click="go(i - 1)" :disabled="i === 0 || busy">Anterior</button>
      <button class="btn sm primary" @click="go(i + 1)" :disabled="i === STEPS.length - 1 || busy">Siguiente <Icon name="chevron" :size="13" /></button>
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
  { title: 'Cuatro astronautas, cuatro líneas base', day: 38, to: '/', role: 'oficial', action: 'ir al día 38 y abrir la vista de misión',
    text: 'Cada tripulante ficticio tiene sus propios valores habituales. El sistema aprendió los primeros 14 días de cada uno.' },
  { title: 'Situación inicial estable', day: 38, to: '/persona/A1', select: 'A1', role: 'astronauta', action: 'rol Astronauta: abrir a la Cmdte. Rivera',
    text: 'Seis indicadores dentro de su rango habitual. Debajo, cada indicador frente a su propio normal.' },
  { title: 'Comienza un cambio progresivo', day: 49, to: '/persona/A1', select: 'A1', action: 'avanzar al día 49',
    text: 'El simulador inyectó una fatiga progresiva desde el día 44: el sueño baja poco a poco y aumentan los errores de la PVT.' },
  { title: 'Desviación relevante y alerta explicada', day: 54, to: '/persona/A1', select: 'A1', action: 'avanzar al día 54',
    text: 'La alerta dice qué cambió, cuánto (z robusto frente a su línea base), cómo se detectó, qué seguimiento se sugiere y con qué fuente.' },
  { title: 'Otro patrón: estrés fisiológico', day: 72, to: '/persona/A3', select: 'A3', action: 'abrir al Ing. Lindqvist en el día 72',
    text: 'FC en reposo ↑ y variabilidad ↓ a la vez. El umbral poblacional fijo no lo marca porque su FC basal es baja.' },
  { title: 'Se pierde el enlace con la Tierra', day: 97, to: '/', action: 'avanzar al día 97 (apagón 95–104)',
    text: 'El encabezado muestra SIN ENLACE. El monitoreo, las alertas y el almacenamiento siguen funcionando a bordo.' },
  { title: 'El oficial médico revisa', day: 97, to: '/', action: 'rol Oficial médico → Alarmas → Reconocer',
    text: 'Alarmas por prioridad: reconocer o posponer 24 h; si una roja lleva 2 días sin reconocer, el sistema pide escalarla.', role: 'oficial' },
  { title: 'Reporte para la Tierra en cola', day: 97, to: '/tierra', action: 'abrir Reportes',
    text: 'Genere el reporte: queda pendiente en la cola local. Al volver el enlace (día 105) se puede transmitir (envío simulado).' },
  { title: '¿Cómo sabemos que funciona?', day: 97, to: '/laboratorio/validacion', action: 'abrir el Validation Lab',
    text: 'Comparación con un umbral poblacional fijo en 40 misiones independientes de las usadas para ajustar, incluidos los casos donde no ganamos.' }
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

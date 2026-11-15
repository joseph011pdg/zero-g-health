<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2 class="title">Simulador de misión</h2>
        <p>Datos <strong>simulados</strong> y reproducibles (semilla) con eventos conocidos. No son predicciones clínicas.</p>
      </div>
    </div>

    <section class="panel ctl">
      <div class="row wrap">
        <button class="btn primary" @click="toggle" :aria-pressed="playing">
          <Icon :name="playing ? 'pause' : 'play'" :size="14" />{{ playing ? 'Pausar' : 'Iniciar' }}</button>
        <button class="btn" @click="step(1)" :disabled="playing"><Icon name="next" :size="14" /> +1 día</button>
        <button class="btn" @click="step(7)" :disabled="playing">+7 días</button>
        <label class="row small">Velocidad
          <select class="input sm" v-model.number="speed"><option :value="1500">lenta</option><option :value="700">normal</option><option :value="250">rápida</option></select></label>
        <div class="daybig mono">D{{ String(s.day).padStart(3, '0') }}<span class="muted small"> / {{ s.mission.dias - 1 }}</span></div>
      </div>
      <div class="row wrap">
        <label v-if="!s.publico" class="row small">Semilla <input class="input sm num" type="number" v-model.number="seed" min="0" /></label>
        <button class="btn danger" @click="resetDemo"><Icon name="reset" :size="14" /> {{ s.publico ? 'Restablecer demo' : 'Reiniciar misión demo' }}</button>
      </div>
    </section>

    <section class="cols-2">
      <div class="panel grid">
        <h2><Icon name="cpu" /> Escenario por astronauta</h2>
        <div class="cols-2">
          <label class="field"><span>Astronauta</span>
            <select class="input" v-model="sa.astro_id"><option v-for="c in s.crew" :key="c.id" :value="c.id">{{ c.id }} · {{ c.nombre }}</option></select></label>
          <label class="field"><span>Escenario</span>
            <select class="input" v-model="sa.escenario">
              <option v-for="(v, k) in scen.escenarios" :key="k" :value="k">{{ k }} · {{ v.nombre }}</option></select></label>
          <label class="field"><span>Día de inicio</span><input class="input" type="number" min="15" max="115" v-model.number="sa.inicio" :disabled="!scen.con_evento?.includes(sa.escenario)" /></label>
          <label class="field"><span>Intensidad ({{ fmt(sa.intensidad, 1) }}×)</span><input type="range" min="0.3" max="2" step="0.1" v-model.number="sa.intensidad" :disabled="!scen.con_evento?.includes(sa.escenario)" /></label>
        </div>
        <p class="small muted">{{ scen.escenarios?.[sa.escenario]?.desc }}</p>
        <div class="row"><button class="btn primary" @click="applyScenario" :disabled="s.publico"><Icon name="spark" :size="14" /> Aplicar (regenera sus datos sintéticos)</button></div>
        <p v-if="s.publico" class="tiny c-amarillo">En la demo pública no se regeneran datos (afectaría a todos). Pruebe los escenarios ya cargados desde la portada: fatiga (B), estrés (C) y evento solar (D).</p>
        <p class="tiny faint">Se conservan los registros manuales de la persona. Los datos pasan por la misma ingesta validada.</p>
      </div>

      <div class="panel grid">
        <h2><Icon name="signalOff" /> Escenario F · interrupción de comunicaciones</h2>
        <div class="cols-2">
          <label class="field"><span>Inicio del apagón</span><input class="input" type="number" min="0" max="119" v-model.number="bo.inicio" /></label>
          <label class="field"><span>Fin del apagón</span><input class="input" type="number" min="0" max="119" v-model.number="bo.fin" /></label>
        </div>
        <div class="row wrap">
          <button class="btn" @click="setBlackout(false)" :disabled="s.publico">Aplicar ventana</button>
          <button class="btn ghost" @click="setBlackout(true)" :disabled="s.publico">Sin apagón</button>
        </div>
        <div class="notice small" :class="s.mission.comunicacion.apagon ? 'err' : 'info'">
          <Icon :name="s.mission.comunicacion.apagon ? 'signalOff' : 'satellite'" />
          <span>Hoy: <strong>{{ s.mission.comunicacion.estado }}</strong>{{ s.mission.comunicacion.apagon ? '' : ` · ${fmt(s.mission.comunicacion.retraso_min, 1)} min por sentido (${fmt(s.mission.comunicacion.ida_vuelta_min, 1)} min ida y vuelta)` }}.
            Ventana actual: {{ s.mission.apagon[0] ?? '—' }}–{{ s.mission.apagon[1] ?? '—' }}. Durante el apagón el detector sigue
            calculando y los reportes quedan en cola.</span></div>
        <p class="tiny faint">Retraso modelado de forma simplificada (3 → 20 min por sentido). No hay integración real con
          comunicaciones espaciales.</p>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h2><Icon name="activity" /> Respuesta del detector frente a la verdad simulada</h2>
        <div class="row wrap">
          <select class="input sm" v-model="viewId"><option v-for="c in s.crew" :key="c.id" :value="c.id">{{ c.id }} · {{ c.nombre }}</option></select>
          <select class="input sm" v-model="viewInd"><option v-for="(c, k) in s.indicators" :key="k" :value="k">{{ c.corto }}</option></select>
        </div>
      </div>
      <div v-if="astro" class="strip-wrap">
        <div class="strip" v-for="(c, k) in s.indicators" :key="k">
          <span class="tiny muted name">{{ c.corto }}</span>
          <div class="cells" :style="{ gridTemplateColumns: `repeat(${s.mission.dias}, 1fr)` }">
            <span v-for="d in s.mission.dias" :key="d" class="cellx"
                  :class="[cellLevel(k, d - 1), { truth: inEvent(k, d - 1) }]" :title="`Día ${d - 1}: ${cellLevel(k, d - 1)}`" />
          </div>
        </div>
        <div class="row wrap tiny muted legend">
          <span><i class="sw verde" />normal</span><span><i class="sw amarillo" />vigilar</span><span><i class="sw rojo" />actuar</span>
          <span><i class="sw sin_dato" />sin dato / calibrando</span><span><i class="sw future" />futuro (aún no revelado)</span>
          <span><i class="sw truthsw" />evento inyectado (verdad)</span>
        </div>
      </div>
      <TrendChart v-if="astro" :data="astro.series[viewInd]" :unidad="s.indicators[viewInd].unidad" :nombre="s.indicators[viewInd].corto"
                  :decimales="s.indicators[viewInd].decimales" :fijo="s.indicators[viewInd].umbral_fijo"
                  :events="events.filter((e) => e.astro_id === viewId && e.afecta.split(',').includes(viewInd))" :height="260" />
    </section>

    <section class="panel">
      <div class="panel-head"><h2><Icon name="clipboard" /> Eventos inyectados (la "respuesta correcta")</h2>
        <span class="tiny muted">solo visibles aquí y en la validación; el astronauta no los ve</span></div>
      <div class="table-wrap">
        <table class="table">
          <thead><tr><th>Astronauta</th><th>Escenario</th><th>Inicio</th><th>Fin</th><th>Indicadores</th><th>Intensidad</th><th>Estado hoy</th></tr></thead>
          <tbody>
            <tr v-for="(e, i) in events" :key="i">
              <td>{{ e.astro_id }}</td><td><span class="tag">{{ e.escenario }}</span> {{ e.nombre }}</td>
              <td class="mono">D{{ e.start }}</td><td class="mono">D{{ e.end }}</td><td class="tiny">{{ e.afecta }}</td>
              <td class="num">{{ fmt(e.intensidad, 1) }}×</td>
              <td class="tiny">{{ s.day < e.start ? 'futuro' : s.day <= e.end ? 'en curso' : 'terminado' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onBeforeUnmount } from 'vue'
import { api, useStore, fmt } from '../store.js'
import Icon from '../components/Icon.vue'
import TrendChart from '../components/TrendChart.vue'

const s = useStore()
const playing = ref(false)
const speed = ref(700)
const seed = ref(s.mission.semilla)
const scen = ref({})
const events = ref([])
const astro = ref(null)
const viewId = ref(s.selected)
const viewInd = ref('sleep')
const sa = reactive({ astro_id: s.selected, escenario: 'B', inicio: Math.min(s.day + 3, 110), intensidad: 1 })
const bo = reactive({ inicio: s.mission.apagon[0] ?? 95, fin: s.mission.apagon[1] ?? 104 })
let timer = null

api('/sim/scenarios').then((r) => { scen.value = r })
async function loadEvents() { events.value = await api('/events') }
async function loadAstro() { astro.value = await api(`/astronauts/${viewId.value}`) }
watch(() => [viewId.value, s.tick], () => { loadAstro(); loadEvents() }, { immediate: true })

function toggle() {
  playing.value = !playing.value
  if (playing.value) loop()
  else clearTimeout(timer)
}
async function loop() {
  if (!playing.value) return
  if (s.day >= s.mission.dias - 1) { playing.value = false; return }
  try { await s.advance(1) } catch { playing.value = false; return }
  timer = setTimeout(loop, speed.value)
}
async function step(n) { await s.run(() => s.advance(n)) }
async function resetDemo() {
  if (s.publico) { playing.value = false; await s.run(() => s.resetDemo(), 'Demo restablecida en este navegador'); return }
  if (!confirm('¿Reiniciar la misión de demostración? Se borran check-ins, pruebas, revisiones y reportes de esta base local.')) return
  playing.value = false
  await s.run(() => api('/sim/reset', { method: 'POST', body: { seed: seed.value } }), `Misión reiniciada (semilla ${seed.value})`)
  await s.refresh()
}
async function applyScenario() {
  const item = { escenario: sa.escenario }
  if (scen.value.con_evento.includes(sa.escenario)) { item.inicio = sa.inicio; item.intensidad = sa.intensidad }
  const r = await s.run(() => api('/sim/astronaut', { method: 'POST', body: { astro_id: sa.astro_id, plan: [item] } }),
    `Escenario ${sa.escenario} aplicado a ${sa.astro_id}`)
  if (r.rechazados.length) s.toast(`${r.rechazados.length} registro(s) inválido(s) rechazado(s) por la ingesta`, 'err')
  viewId.value = sa.astro_id
  await s.refresh()
}
async function setBlackout(none) {
  const body = none ? { inicio: null, fin: null } : { inicio: bo.inicio, fin: bo.fin }
  await s.run(() => api('/sim/blackout', { method: 'POST', body }), none ? 'Apagón eliminado' : 'Ventana de apagón actualizada')
  await s.refresh()
}
function cellLevel(k, d) {
  if (d > s.day) return 'future'
  return astro.value?.series[k][d]?.nivel || 'sin_dato'
}
function inEvent(k, d) {
  return events.value.some((e) => e.astro_id === viewId.value && e.afecta.split(',').includes(k) && d >= e.start && d <= e.end)
}
onBeforeUnmount(() => clearTimeout(timer))
</script>

<style scoped>
.ctl { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px; align-items: center; }
.input.sm { width: auto; padding: 5px 8px; }
.daybig { font-size: 1.5rem; font-weight: 700; margin-left: 8px; }
.strip-wrap { display: grid; gap: 4px; margin-bottom: 12px; }
.strip { display: grid; grid-template-columns: 90px 1fr; align-items: center; gap: 8px; }
.cells { display: grid; gap: 1px; height: 16px; }
.cellx { display: block; height: 100%; border-radius: 1px; background: var(--ok); opacity: .75; position: relative; }
.cellx.amarillo { background: var(--warn); opacity: 1; }
.cellx.rojo { background: var(--red); opacity: 1; }
.cellx.sin_dato, .cellx.calibrando { background: var(--gray); opacity: .45; }
.cellx.future { background: var(--surface-3); opacity: .5; }
.cellx.truth { box-shadow: inset 0 -4px 0 #6a4fc4; }
.legend { gap: 14px; margin-top: 4px; }
.sw { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 5px; vertical-align: -1px; }
.sw.verde { background: var(--ok); } .sw.amarillo { background: var(--warn); } .sw.rojo { background: var(--red); }
.sw.sin_dato { background: var(--gray); } .sw.future { background: var(--surface-3); } .sw.truthsw { background: #6a4fc4; }
</style>

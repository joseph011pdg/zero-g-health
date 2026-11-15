<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2 class="title">Mission simulator</h2>
        <p><strong>Simulated</strong>, reproducible data (seeded) with known events. Not clinical predictions.</p>
      </div>
    </div>

    <section class="panel ctl">
      <div class="row wrap">
        <button class="btn primary" @click="toggle" :aria-pressed="playing">
          <Icon :name="playing ? 'pause' : 'play'" :size="14" />{{ playing ? 'Pause' : 'Play' }}</button>
        <button class="btn" @click="step(1)" :disabled="playing"><Icon name="next" :size="14" /> +1 day</button>
        <button class="btn" @click="step(7)" :disabled="playing">+7 days</button>
        <label class="row small">Speed
          <select class="input sm" v-model.number="speed"><option :value="1500">slow</option><option :value="700">normal</option><option :value="250">fast</option></select></label>
        <div class="daybig mono">D{{ String(s.day).padStart(3, '0') }}<span class="muted small"> / {{ s.mission.dias - 1 }}</span></div>
      </div>
      <div class="row wrap">
        <label v-if="!s.publico" class="row small">Seed <input class="input sm num" type="number" v-model.number="seed" min="0" /></label>
        <button class="btn danger" @click="resetDemo"><Icon name="reset" :size="14" /> {{ s.publico ? 'Reset demo' : 'Restart demo mission' }}</button>
      </div>
    </section>

    <section class="cols-2">
      <div class="panel grid">
        <h2><Icon name="cpu" /> Scenario per astronaut</h2>
        <div class="cols-2">
          <label class="field"><span>Astronaut</span>
            <select class="input" v-model="sa.astro_id"><option v-for="c in s.crew" :key="c.id" :value="c.id">{{ c.id }} · {{ c.nombre }}</option></select></label>
          <label class="field"><span>Scenario</span>
            <select class="input" v-model="sa.escenario">
              <option v-for="(v, k) in scen.escenarios" :key="k" :value="k">{{ k }} · {{ v.nombre }}</option></select></label>
          <label class="field"><span>Start day</span><input class="input" type="number" min="15" max="115" v-model.number="sa.inicio" :disabled="!scen.con_evento?.includes(sa.escenario)" /></label>
          <label class="field"><span>Intensity ({{ fmt(sa.intensidad, 1) }}×)</span><input type="range" min="0.3" max="2" step="0.1" v-model.number="sa.intensidad" :disabled="!scen.con_evento?.includes(sa.escenario)" /></label>
        </div>
        <p class="small muted">{{ scen.escenarios?.[sa.escenario]?.desc }}</p>
        <div class="row"><button class="btn primary" @click="applyScenario" :disabled="s.publico"><Icon name="spark" :size="14" /> Apply (regenerates their synthetic data)</button></div>
        <p v-if="s.publico" class="tiny c-amarillo">The public demo does not regenerate data (it would affect everyone). Try the preloaded scenarios from the home page: fatigue (B), stress (C) and solar event (D).</p>
        <p class="tiny faint">The person's manual records are kept. Data goes through the same validated ingestion.</p>
      </div>

      <div class="panel grid">
        <h2><Icon name="signalOff" /> Scenario F · communication outage</h2>
        <div class="cols-2">
          <label class="field"><span>Blackout start</span><input class="input" type="number" min="0" max="119" v-model.number="bo.inicio" /></label>
          <label class="field"><span>Blackout end</span><input class="input" type="number" min="0" max="119" v-model.number="bo.fin" /></label>
        </div>
        <div class="row wrap">
          <button class="btn" @click="setBlackout(false)" :disabled="s.publico">Apply window</button>
          <button class="btn ghost" @click="setBlackout(true)" :disabled="s.publico">No blackout</button>
        </div>
        <div class="notice small" :class="s.mission.comunicacion.apagon ? 'err' : 'info'">
          <Icon :name="s.mission.comunicacion.apagon ? 'signalOff' : 'satellite'" />
          <span>Today: <strong>{{ s.mission.comunicacion.estado }}</strong>{{ s.mission.comunicacion.apagon ? '' : ` · ${fmt(s.mission.comunicacion.retraso_min, 1)} min each way (${fmt(s.mission.comunicacion.ida_vuelta_min, 1)} min round trip)` }}.
            Current window: {{ s.mission.apagon[0] ?? '—' }}–{{ s.mission.apagon[1] ?? '—' }}. During the blackout the detector keeps
            running and reports stay queued.</span></div>
        <p class="tiny faint">Simplified delay model (3 → 20 min each way). No real integration with
          space communications.</p>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h2><Icon name="activity" /> Detector response vs. simulated ground truth</h2>
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
                  :class="[cellLevel(k, d - 1), { truth: inEvent(k, d - 1) }]" :title="`Day ${d - 1}: ${CELL[cellLevel(k, d - 1)] || cellLevel(k, d - 1)}`" />
          </div>
        </div>
        <div class="row wrap tiny muted legend">
          <span><i class="sw verde" />normal</span><span><i class="sw amarillo" />Watch</span><span><i class="sw rojo" />Act</span>
          <span><i class="sw sin_dato" />no data / calibrating</span><span><i class="sw future" />future (not revealed yet)</span>
          <span><i class="sw truthsw" />injected event (ground truth)</span>
        </div>
      </div>
      <TrendChart v-if="astro" :data="astro.series[viewInd]" :unidad="s.indicators[viewInd].unidad" :nombre="s.indicators[viewInd].corto"
                  :decimales="s.indicators[viewInd].decimales" :fijo="s.indicators[viewInd].umbral_fijo"
                  :events="events.filter((e) => e.astro_id === viewId && e.afecta.split(',').includes(viewInd))" :height="260" />
    </section>

    <section class="panel">
      <div class="panel-head"><h2><Icon name="clipboard" /> Injected events (the "right answer")</h2>
        <span class="tiny muted">only visible here and in validation; the astronaut does not see them</span></div>
      <div class="table-wrap">
        <table class="table">
          <thead><tr><th>Astronaut</th><th>Scenario</th><th>Start</th><th>End</th><th>Indicators</th><th>Intensity</th><th>Status today</th></tr></thead>
          <tbody>
            <tr v-for="(e, i) in events" :key="i">
              <td>{{ e.astro_id }}</td><td><span class="tag">{{ e.escenario }}</span> {{ e.nombre }}</td>
              <td class="mono">D{{ e.start }}</td><td class="mono">D{{ e.end }}</td><td class="tiny">{{ e.afecta }}</td>
              <td class="num">{{ fmt(e.intensidad, 1) }}×</td>
              <td class="tiny">{{ s.day < e.start ? 'future' : s.day <= e.end ? 'ongoing' : 'finished' }}</td>
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
const CELL = { verde: 'normal', amarillo: 'Watch', rojo: 'Act', sin_dato: 'no data', calibrando: 'calibrating', future: 'future' }
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
  if (s.publico) { playing.value = false; await s.run(() => s.resetDemo(), 'Demo reset in this browser'); return }
  if (!confirm('Restart the demo mission? Check-ins, tests, reviews and reports in this local database will be deleted.')) return
  playing.value = false
  await s.run(() => api('/sim/reset', { method: 'POST', body: { seed: seed.value } }), `Mission restarted (seed ${seed.value})`)
  await s.refresh()
}
async function applyScenario() {
  const item = { escenario: sa.escenario }
  if (scen.value.con_evento.includes(sa.escenario)) { item.inicio = sa.inicio; item.intensidad = sa.intensidad }
  const r = await s.run(() => api('/sim/astronaut', { method: 'POST', body: { astro_id: sa.astro_id, plan: [item] } }),
    `Scenario ${sa.escenario} applied to ${sa.astro_id}`)
  if (r.rechazados.length) s.toast(`${r.rechazados.length} invalid record(s) rejected by ingestion`, 'err')
  viewId.value = sa.astro_id
  await s.refresh()
}
async function setBlackout(none) {
  const body = none ? { inicio: null, fin: null } : { inicio: bo.inicio, fin: bo.fin }
  await s.run(() => api('/sim/blackout', { method: 'POST', body }), none ? 'Blackout removed' : 'Blackout window updated')
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

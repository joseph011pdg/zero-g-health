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
      <!-- MATRIZ DE PUNTOS: cada día es un punto; el tamaño crece con la desviación (z) y el color es el nivel -->
      <div v-if="astro" class="dotmap">
        <div class="dm-scroll"><svg :viewBox="`0 0 ${DM.W} ${dm.h}`" width="100%" role="img" :aria-label="`Day map for ${astro.nombre}: dot size grows with deviation`">
          <g v-for="r in dm.rows" :key="r.k">
            <text x="0" :y="r.y + 4" class="dm-lab">{{ r.label }}</text>
            <rect v-for="(e, ei) in r.evs" :key="'e' + ei" :x="e.x" :y="r.y - 15" :width="e.w" height="30" rx="15" class="dm-ev">
              <title>Injected event {{ e.code }}: days {{ e.start }}–{{ e.end }}</title>
            </rect>
            <circle v-for="d in r.dots" :key="d.i" :cx="d.cx" :cy="r.y" :r="d.r" :class="['dm-dot', d.lv, { pick: d.lv !== 'future' }]"
                    :tabindex="d.lv !== 'future' ? 0 : -1" @click="pick(r.k, d.i)" @keydown.enter="pick(r.k, d.i)">
              <title>Day {{ d.i }}: {{ CELL[d.lv] || d.lv }}{{ d.z !== null ? ` · z ${fmt(d.z, 1)}` : '' }}</title>
            </circle>
          </g>
          <circle v-if="selDot" :cx="selDot.cx" :cy="selDot.cy" :r="selDot.r + 5" class="dm-sel" />
          <line :x1="dm.tx" :x2="dm.tx" y1="4" :y2="dm.axisY - 8" class="dm-now" />
          <text v-for="t in dm.ticks" :key="t.v" :x="t.x" :y="dm.axisY + 8" class="dm-tick">{{ t.v }}</text>
          <rect :x="dm.tx - 36" :y="dm.axisY - 6" width="72" height="20" rx="10" class="dm-pill" />
          <text :x="dm.tx" :y="dm.axisY + 8" class="dm-pill-t">Day {{ s.day }}</text>
        </svg></div>
        <!-- DETALLE: al hacer clic en un punto, dice si ese día hubo anomalía y si coincide con la verdad simulada -->
        <div class="dm-info" :class="info ? info.tone : 'idle'" aria-live="polite">
          <template v-if="!info">
            <span class="dm-hint">Click any dot to check that day for an anomaly.</span>
            <button class="btn sm" @click="pickLatest">Show the latest anomaly</button>
          </template>
          <template v-else>
            <div class="dm-info-main">
              <span class="dm-badge">{{ info.badge }}</span>
              <div>
                <strong>{{ info.title }}</strong>
                <span class="dm-meta">{{ s.indicators[sel.k].corto }} · day {{ sel.d }}</span>
              </div>
            </div>
            <dl v-if="info.p" class="dm-facts">
              <div><dt>Value</dt><dd>{{ fmt(info.p.valor, info.dec) }} {{ info.unit }}</dd></div>
              <div><dt>Their usual</dt><dd>{{ fmt(info.p.normal, info.dec) }} {{ info.unit }}</dd></div>
              <div><dt>Deviation (z)</dt><dd>{{ fmt(info.p.z, 1) }}</dd></div>
              <div><dt>Watch from</dt><dd>z ≥ {{ fmt(s.mission.parametros.yellow, 1) }}</dd></div>
            </dl>
            <p class="dm-truth"><b>Ground truth:</b> {{ info.truth }} <span class="dm-verdict">{{ info.verdict }}</span></p>
            <div class="row wrap">
              <router-link class="btn sm" :to="`/crew/${viewId}`">Open profile</router-link>
              <button class="btn sm ghost" @click="sel = null">Close</button>
            </div>
          </template>
        </div>
        <div class="dm-legend">
          <span><i class="sw verde" />Normal</span><span><i class="sw amarillo" />Watch</span><span><i class="sw rojo" />Act</span>
          <span><i class="sw sin_dato" />No data / calibrating</span><span><i class="sw future" />Not revealed yet</span>
          <span><i class="sw truthsw" />Injected event</span><span class="dm-note">Dot size grows with z (distance from their usual)</span>
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
import { computed, ref, reactive, watch, onBeforeUnmount } from 'vue'
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
//MATRIZ DE PUNTOS: geometría en un lienzo SVG de 1000 de ancho
const DM = { W: 1000, L: 118, R: 10, row: 40, top: 24 }
const dm = computed(() => {
  const n = s.mission.dias, dx = (DM.W - DM.L - DM.R) / n, keys = Object.keys(s.indicators)
  const xOf = (d) => DM.L + d * dx + dx / 2
  const rows = keys.map((k, i) => {
    const y = DM.top + i * DM.row
    const dots = []
    for (let d = 0; d < n; d++) {
      if (d > s.day) { dots.push({ i: d, cx: xOf(d), r: 1.4, lv: 'future', z: null }); continue }
      const p = astro.value?.series[k]?.[d]
      const z = p?.z ?? null
      dots.push({ i: d, cx: xOf(d), r: Math.max(2.2, Math.min(13, 2.2 + Math.abs(z ?? 0) * 2.3)), lv: p?.nivel || 'sin_dato', z })
    }
    const evs = events.value.filter((e) => e.astro_id === viewId.value && e.afecta.split(',').includes(k))
      .map((e) => ({ x: DM.L + e.start * dx, w: (e.end - e.start + 1) * dx, start: e.start, end: e.end, code: e.escenario }))
    return { k, label: s.indicators[k].corto, y, dots, evs }
  })
  const axisY = DM.top + keys.length * DM.row
  const tx = DM.L + (s.day + 1) * dx
  const ticks = [0, 30, 60, 90, n - 1].filter((v) => Math.abs(v - s.day) > 7).map((v) => ({ v, x: xOf(v) }))
  return { rows, axisY, tx, ticks, h: axisY + 22 }
})
//DETALLE DE UN DÍA: ¿hubo anomalía? y ¿coincide con un evento inyectado?
const sel = ref(null)
function pick(k, d) { if (d <= s.day) sel.value = { k, d } }
function pickLatest() {
  let best = null
  for (const k of Object.keys(s.indicators)) {
    (astro.value?.series[k] || []).forEach((p, d) => {
      if (d <= s.day && (p?.nivel === 'amarillo' || p?.nivel === 'rojo') && (!best || d > best.d || (d === best.d && p.nivel === 'rojo'))) best = { k, d }
    })
  }
  sel.value = best || { k: Object.keys(s.indicators)[0], d: s.day }
}
watch(viewId, () => { sel.value = null })
const selDot = computed(() => {
  if (!sel.value) return null
  const row = dm.value.rows.find((r) => r.k === sel.value.k)
  const dot = row?.dots[sel.value.d]
  return dot ? { cx: dot.cx, cy: row.y, r: dot.r } : null
})
const info = computed(() => {
  if (!sel.value || !astro.value) return null
  const { k, d } = sel.value
  const p = astro.value.series[k]?.[d]
  const lv = p?.nivel || 'sin_dato'
  const ev = events.value.find((e) => e.astro_id === viewId.value && e.afecta.split(',').includes(k) && d >= e.start && d <= e.end)
  const anomaly = lv === 'amarillo' || lv === 'rojo'
  const base = { p: p && p.valor !== null && p.valor !== undefined ? p : null, dec: s.indicators[k].decimales, unit: s.indicators[k].unidad }
  const truth = ev ? `inside injected event ${ev.escenario} (${ev.nombre}, days ${ev.start}–${ev.end}).` : 'no injected event on this day.'
  if (lv === 'sin_dato' || lv === 'calibrando') {
    return { ...base, tone: 'muted', badge: lv === 'calibrando' ? 'Calibrating' : 'No data', title: lv === 'calibrando' ? 'Not enough days yet to judge this indicator' : 'No measurement this day: never read as normal', truth, verdict: '' }
  }
  const verdict = anomaly ? (ev ? 'Correct detection.' : 'False alarm (no event behind it).') : (ev ? 'Not flagged on this day.' : 'Correct: nothing to flag.')
  if (lv === 'rojo') return { ...base, tone: 'act', badge: 'Act', title: 'Anomaly detected: notify the Medical Officer', truth, verdict }
  if (lv === 'amarillo') return { ...base, tone: 'watch', badge: 'Watch', title: 'Anomaly detected: repeat the measurement', truth, verdict }
  return { ...base, tone: 'ok', badge: 'Normal', title: 'No anomaly: within their usual range', truth, verdict }
})
function inEvent(k, d) {
  return events.value.some((e) => e.astro_id === viewId.value && e.afecta.split(',').includes(k) && d >= e.start && d <= e.end)
}
onBeforeUnmount(() => clearTimeout(timer))
</script>

<style scoped>
.ctl { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px; align-items: center; background: var(--blue-soft); border-color: #cfdcf0; }
.daybig { color: var(--navy); font-weight: 600; }
.input.sm { width: auto; padding: 5px 8px; }
.daybig { font-size: 1.5rem; font-weight: 700; margin-left: 8px; }
/* MATRIZ DE PUNTOS: fondo blanco, puntos por nivel, eventos en cápsula morada, hoy en línea marino */
.dotmap { margin-bottom: 14px; padding: 6px 4px 10px; }
.dotmap svg { display: block; overflow: visible; }
/* En pantallas estrechas el mapa conserva un ancho legible y se desplaza en horizontal */
.dm-scroll { overflow-x: auto; }
@media (max-width: 720px) { .dotmap svg { min-width: 680px; } }
.dm-lab { font-size: 13px; font-weight: 500; fill: var(--ink); font-family: var(--sans); }
.dm-ev { fill: rgba(124, 92, 255, .12); stroke: #7c5cff; stroke-width: 1.2; }
.dm-dot { fill: #22a06b; fill-opacity: .78; transition: transform 150ms var(--ease-out); transform-box: fill-box; transform-origin: center; }
.dm-dot.amarillo { fill: #f2b632; fill-opacity: .95; }
.dm-dot.rojo { fill: #f07a1a; fill-opacity: .95; }
.dm-dot.sin_dato, .dm-dot.calibrando { fill: #c3cddd; fill-opacity: 1; }
.dm-dot.future { fill: #d3dbe7; fill-opacity: 1; }
@media (hover: hover) and (pointer: fine) { .dm-dot:hover { transform: scale(1.35); } }
.dm-dot.pick { cursor: pointer; }
.dm-dot.pick:focus { outline: none; stroke: var(--navy); stroke-width: 2; }
.dm-sel { fill: none; stroke: var(--navy); stroke-width: 2; pointer-events: none; }
/* PANEL DE DETALLE */
.dm-info { margin-top: 10px; border: 1px solid var(--line-soft); border-radius: var(--radius); padding: 12px 14px; display: grid; gap: 10px; background: #f8fafd; }
.dm-info.idle { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
/* Tono del panel según el resultado: fondo suave del mismo color que el nivel */
.dm-info.ok { background: #f1f8f4; border-color: #cfe7da; } .dm-info.watch { background: #fdf8ea; border-color: #f0e0b0; }
.dm-info.act { background: #fdf3ea; border-color: #f2d2b4; } .dm-info.muted { background: #f5f7fa; }
.dm-hint { font-size: 0.88rem; color: var(--text-2); }
.dm-info-main { display: flex; align-items: center; gap: 12px; }
.dm-info-main strong { display: block; font-size: 1rem; color: var(--ink); }
.dm-meta { font-size: 0.8rem; color: var(--muted); }
.dm-badge { font-size: 0.74rem; font-weight: 700; padding: 4px 9px; border-radius: 3px; background: #e4e9f1; color: var(--text-2); white-space: nowrap; }
.ok .dm-badge { background: var(--ok-soft); color: var(--ok); }
.watch .dm-badge { background: var(--warn-soft); color: var(--warn); }
.act .dm-badge { background: var(--red-soft); color: var(--red); }
.dm-facts { margin: 0; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.dm-facts div { background: #fff; border: 1px solid var(--line-soft); border-radius: var(--radius-sm); padding: 6px 10px; }
.dm-facts dt { font-size: 0.72rem; color: var(--muted); }
.dm-facts dd { margin: 0; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums; }
.dm-truth { font-size: 0.86rem; color: var(--text-2); margin: 0; }
.dm-verdict { font-weight: 600; color: var(--navy); }
@media (max-width: 640px) { .dm-facts { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.dm-now { stroke: var(--navy); stroke-width: 2; stroke-dasharray: 4 3; }
.dm-tick { font-size: 11px; fill: var(--muted); text-anchor: middle; font-family: var(--sans); }
.dm-pill { fill: var(--navy); }
.dm-pill-t { font-size: 11px; font-weight: 600; fill: #fff; text-anchor: middle; font-family: var(--sans); }
.dm-legend { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 0.78rem; color: var(--text-2); margin-top: 6px; }
.dm-legend span { display: inline-flex; align-items: center; }
.dm-note { color: var(--muted); }
.sw { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
.sw.verde { background: #22a06b; } .sw.amarillo { background: #f2b632; } .sw.rojo { background: #f07a1a; }
.sw.sin_dato { background: #c3cddd; } .sw.future { background: #d3dbe7; width: 5px; height: 5px; }
.sw.truthsw { background: rgba(124, 92, 255, .12); border: 1.5px solid #7c5cff; border-radius: 6px; width: 16px; }
@media (prefers-reduced-motion: reduce) { .dm-dot:hover { transform: none; } }
</style>

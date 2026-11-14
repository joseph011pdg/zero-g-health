<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="eyebrow">03 · Daily Check-in · Cognitive Test · Ingesta</div>
        <h1>Registro a bordo — día {{ s.day }}</h1>
        <p>Los registros se guardan en la base local, pasan por la misma validación que los sensores y actualizan la línea base
          de la persona seleccionada.</p>
      </div>
      <label class="field who no-print"><span>Astronauta</span>
        <select class="input" :value="s.selected" @change="s.select($event.target.value)">
          <option v-for="c in s.crew" :key="c.id" :value="c.id">{{ c.id }} · {{ c.nombre }}</option>
        </select></label>
    </div>

    <div class="tabs" role="tablist">
      <button v-for="t in TABS" :key="t.k" :class="{ on: tab === t.k }" @click="tab = t.k"><Icon :name="t.icon" :size="14" />{{ t.l }}</button>
    </div>

    <!-- F4 Check-in -->
    <section v-if="tab === 'checkin'" class="two">
      <form class="panel grid" @submit.prevent="sendCheckin" @input="startTimer">
        <h2>Check-in diario <span class="muted small">(&lt; 1 minuto)</span></h2>
        <label class="field"><span>¿Cómo está su ánimo hoy? <strong class="num">{{ ck.animo }}</strong>/10</span>
          <input type="range" min="1" max="10" step="0.5" v-model.number="ck.animo" aria-label="Ánimo de 1 a 10" />
          <div class="row between tiny muted"><span>1 · muy bajo</span><span>10 · excelente</span></div></label>
        <div class="field"><span>Calidad percibida del sueño de anoche</span>
          <div class="seg" role="radiogroup">
            <button v-for="q in SLEEP_Q" :key="q.v" type="button" role="radio" :aria-checked="ck.calidad_sueno === q.v"
                    :class="{ on: ck.calidad_sueno === q.v }" @click="ck.calidad_sueno = q.v; startTimer()">
              <strong>{{ q.v }}</strong><span class="tiny">{{ q.l }}</span></button>
          </div></div>
        <label class="field"><span>Observaciones (opcional)</span>
          <textarea class="input" v-model="ck.notas" maxlength="500" placeholder="Síntomas, eventos del día, comentarios…" /></label>
        <div class="row between">
          <span class="tiny muted">Tiempo: {{ elapsed }} s</span>
          <button class="btn primary" type="submit" :disabled="!ck.calidad_sueno || busy">Guardar check-in</button>
        </div>
        <p class="tiny faint">El autorreporte alimenta el indicador de ánimo. No se usa para diagnosticar condiciones psicológicas.
          La duración del sueño la mide la actigrafía; aquí solo se registra la calidad percibida.</p>
      </form>
      <div class="panel">
        <h2>Historial de check-ins</h2>
        <table class="table" v-if="astro?.checkins.length">
          <thead><tr><th>Día</th><th>Ánimo</th><th>Sueño percibido</th><th>Notas</th><th>s</th></tr></thead>
          <tbody><tr v-for="c in astro.checkins" :key="c.id"><td class="mono">D{{ c.day }}</td><td class="num">{{ c.animo }}</td>
            <td>{{ c.calidad_sueno }}/5</td><td class="small">{{ c.notas || '—' }}</td><td class="num tiny">{{ fmt(c.segundos, 0) }}</td></tr></tbody>
        </table>
        <p v-else class="small muted">Sin check-ins registrados para esta persona.</p>
        <TrendChart v-if="astro" class="mt" :data="astro.series.mood.slice(-30)" unidad="/10" nombre="Ánimo" :fijo="s.indicators.mood.umbral_fijo" :height="190" />
      </div>
    </section>

    <!-- F3 PVT-B -->
    <section v-if="tab === 'pvt'" class="two">
      <div class="panel grid">
        <div class="panel-head"><h2>Prueba de vigilancia psicomotora (PVT-B)</h2>
          <div class="tabs" v-if="phase === 'idle'">
            <button :class="{ on: mode === 'pvtb_3min' }" @click="mode = 'pvtb_3min'">3 min</button>
            <button :class="{ on: mode === 'abreviada_60s' }" @click="mode = 'abreviada_60s'">60 s (demo)</button>
          </div></div>
        <p class="small muted" v-if="phase === 'idle'">Cuando aparezca el contador, pulse <kbd>Espacio</kbd> o toque el recuadro lo
          antes posible. No se adelante. Intervalos aleatorios de 2 a 5 s. Lapso = respuesta ≥ 355 ms; anticipación = respuesta antes
          del estímulo o en menos de 100 ms (definiciones de PVT-B, Basner et al., 2011).</p>
        <div v-if="mode === 'abreviada_60s' && phase === 'idle'" class="notice warn small"><Icon name="info" />
          Versión abreviada para demostración: NO equivale al protocolo PVT-B de 3 minutos. Sus errores se escalan a 3 min y se
          guardan marcados como “PVT abreviada”.</div>

        <div class="stage" :class="phase" @pointerdown.prevent="hit" tabindex="0" role="button"
             aria-label="Zona de respuesta de la prueba">
          <template v-if="phase === 'idle'"><button class="btn primary" @pointerdown.stop @click="start"><Icon name="play" :size="14" /> Iniciar prueba</button></template>
          <template v-else-if="phase === 'wait'"><span class="muted">Espere…</span></template>
          <template v-else-if="phase === 'go'"><span class="counter mono">{{ counter }}</span></template>
          <template v-else-if="phase === 'early'"><span class="early">¡Anticipación!</span></template>
          <template v-else-if="phase === 'done'">
            <div class="result">
              <div class="label">Resultado</div>
              <div class="cols-3 res">
                <div class="kpi"><span class="v">{{ medianRt }}<small>ms</small></span><span class="tiny muted">RT mediana</span></div>
                <div class="kpi"><span class="v">{{ lapses }}</span><span class="tiny muted">lapsos ≥ 355 ms</span></div>
                <div class="kpi"><span class="v">{{ falseStarts + fastCount }}</span><span class="tiny muted">anticipaciones</span></div>
              </div>
              <p class="small">{{ rts.length + noResp }} estímulos · {{ noResp }} sin respuesta ·
                <span :class="interruptions ? 'c-amarillo' : 'c-verde'">{{ interruptions ? `${interruptions} interrupción(es): se marcará inválida` : 'sin interrupciones' }}</span></p>
              <div class="row center-row">
                <button class="btn primary" @pointerdown.stop @click="savePvt" :disabled="saved || busy">{{ saved ? 'Guardada' : 'Guardar resultado' }}</button>
                <button class="btn" @pointerdown.stop @click="reset">Repetir</button>
              </div>
            </div>
          </template>
        </div>
        <div v-if="['wait', 'go', 'early'].includes(phase)" class="row between small muted">
          <span>Quedan {{ remaining }} s</span><span>Respuestas {{ rts.length }} · lapsos {{ lapses }} · anticip. {{ falseStarts + fastCount }}</span>
          <button class="btn sm ghost" @pointerdown.stop @click="abort">Cancelar</button>
        </div>
        <p class="tiny faint">Tiempo medido con <code>performance.now()</code> (reloj monotónico) desde el primer cuadro en que se
          dibuja el estímulo. La latencia de pantalla y teclado de cada equipo no se corrige: esta implementación web no está validada
          como el dispositivo PVT-B original. Cambiar de ventana durante la prueba se registra como interrupción.</p>
      </div>
      <div class="panel">
        <h2>Pruebas anteriores</h2>
        <table class="table" v-if="astro?.pvt.length">
          <thead><tr><th>Día</th><th>Modo</th><th>RT med.</th><th>Lapsos</th><th>Antic.</th><th>Err. 3 min</th><th>Válida</th></tr></thead>
          <tbody><tr v-for="p in astro.pvt" :key="p.id"><td class="mono">D{{ p.day }}</td><td class="tiny">{{ p.modo }}</td>
            <td class="num">{{ fmt(p.rt_mediana, 0) }}</td><td class="num">{{ p.lapsos }}</td><td class="num">{{ p.anticipaciones }}</td>
            <td class="num">{{ p.errores_3min }}</td><td :class="p.valido ? 'c-verde' : 'c-amarillo'">{{ p.valido ? 'sí' : 'no' }}</td></tr></tbody>
        </table>
        <p v-else class="small muted">Sin pruebas en esta sesión. El indicador muestra datos sintéticos del simulador.</p>
        <TrendChart v-if="astro" class="mt" :data="astro.series.pvt.slice(-30)" unidad="errores" nombre="Errores PVT" :decimales="0" :fijo="s.indicators.pvt.umbral_fijo" :height="190" />
      </div>
    </section>

    <!-- F2 Medición manual -->
    <section v-if="tab === 'manual'" class="two">
      <form class="panel grid" @submit.prevent="sendManual">
        <h2>Medición manual</h2>
        <div class="cols-2">
          <label class="field"><span>Indicador</span>
            <select class="input" v-model="mm.indicator" @change="mm.unit = s.indicators[mm.indicator].unidad">
              <option v-for="(c, k) in s.indicators" :key="k" :value="k">{{ c.nombre }}</option></select></label>
          <label class="field"><span>Valor</span><input class="input" type="number" step="any" v-model.number="mm.value" required /></label>
          <label class="field"><span>Unidad</span><input class="input" v-model="mm.unit" /></label>
          <label class="field"><span>Día</span><input class="input" type="number" min="0" :max="s.mission.dias - 1" v-model.number="mm.day" /></label>
          <label class="field"><span>Origen</span><select class="input" v-model="mm.source">
            <option value="manual">manual</option><option value="real">real (sensor)</option></select></label>
        </div>
        <div class="row"><button class="btn primary" :disabled="busy">Validar y guardar</button>
          <span class="tiny muted">Rango plausible: {{ s.indicators[mm.indicator].limites.join(' – ') }} {{ s.indicators[mm.indicator].unidad }}</span></div>
        <p class="tiny faint">Una medición manual reemplaza el valor del sensor de ese día y queda registrada con su origen.</p>
      </form>
      <IngestLog :key="logKey" />
    </section>

    <!-- F2 CSV -->
    <section v-if="tab === 'csv'" class="two">
      <div class="panel grid">
        <h2>Importar CSV</h2>
        <p class="small muted">Cabecera obligatoria: <code>astro_id,day,indicator,value,unit[,source]</code>. Indicadores:
          <code>{{ Object.keys(s.indicators).join(', ') }}</code>. Se rechazan: astronauta o indicador desconocido, unidad incorrecta,
          día fuera de misión, valores ausentes o imposibles y duplicados.</p>
        <div class="row wrap">
          <label class="btn"><Icon name="upload" :size="14" /> Elegir archivo<input type="file" accept=".csv,text/csv" hidden @change="readFile" /></label>
          <button class="btn ghost" @click="example">Cargar ejemplo con errores</button>
        </div>
        <textarea class="input mono csv" v-model="csvText" placeholder="astro_id,day,indicator,value,unit" />
        <label class="row small"><input type="checkbox" v-model="overwrite" /> Sobrescribir valores existentes</label>
        <button class="btn primary" @click="sendCsv" :disabled="!csvText.trim() || busy">Validar e importar</button>
        <div v-if="csvRes" class="sub grid">
          <div class="row wrap small"><span class="c-verde">✓ {{ csvRes.insertados }} insertados</span>
            <span>↻ {{ csvRes.reemplazados }} reemplazados</span><span class="c-amarillo">✕ {{ csvRes.rechazados.length }} rechazados</span></div>
          <table class="table" v-if="csvRes.rechazados.length"><thead><tr><th>Fila</th><th>Motivo</th></tr></thead>
            <tbody><tr v-for="(r, i) in csvRes.rechazados" :key="i"><td class="mono tiny">{{ r.astro_id }} · {{ r.day }} · {{ r.indicator }} · {{ r.value }}</td><td class="small">{{ r.motivo }}</td></tr></tbody></table>
        </div>
      </div>
      <IngestLog :key="logKey" />
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onBeforeUnmount, onMounted } from 'vue'
import { api, useStore, fmt } from '../store.js'
import Icon from '../components/Icon.vue'
import TrendChart from '../components/TrendChart.vue'
import IngestLog from '../components/IngestLog.vue'

const s = useStore()
const TABS = [{ k: 'checkin', l: 'Check-in', icon: 'smile' }, { k: 'pvt', l: 'Prueba PVT-B', icon: 'target' },
  { k: 'manual', l: 'Medición manual', icon: 'file' }, { k: 'csv', l: 'Importar CSV', icon: 'upload' }]
const SLEEP_Q = [{ v: 1, l: 'muy mala' }, { v: 2, l: 'mala' }, { v: 3, l: 'regular' }, { v: 4, l: 'buena' }, { v: 5, l: 'muy buena' }]
const tab = ref('checkin')
const busy = ref(false)
const astro = ref(null)
const logKey = ref(0)

async function loadAstro() { try { astro.value = await api(`/astronauts/${s.selected}`) } catch { astro.value = null } }
watch(() => [s.selected, s.tick], loadAstro, { immediate: true })

async function act(fn, msg) {
  busy.value = true
  try { const r = await s.run(fn, msg); await s.refresh(); logKey.value++; return r } finally { busy.value = false }
}

// ---------- Check-in
const ck = reactive({ animo: 7, calidad_sueno: null, notas: '' })
let t0 = null
const elapsed = ref(0)
let tmr = null
function startTimer() { if (!t0) { t0 = performance.now(); tmr = setInterval(() => { elapsed.value = Math.round((performance.now() - t0) / 1000) }, 500) } }
async function sendCheckin() {
  const secs = t0 ? (performance.now() - t0) / 1000 : null
  await act(() => api(`/astronauts/${s.selected}/checkin`, { method: 'POST', body: { animo: ck.animo, calidad_sueno: ck.calidad_sueno, notas: ck.notas || null, segundos: secs } }),
    `Check-in guardado (día ${s.day})`)
  clearInterval(tmr); t0 = null; elapsed.value = 0; ck.notas = ''; ck.calidad_sueno = null
}

// ---------- PVT-B
const LAPSE = 355, FAST = 100, TIMEOUT = 3000
const mode = ref('pvtb_3min')
const phase = ref('idle')
const rts = ref([]); const falseStarts = ref(0); const noResp = ref(0); const interruptions = ref(0)
const counter = ref(0); const remaining = ref(0); const saved = ref(false)
let onset = 0, endAt = 0, timer = null, raf = null, durS = 180
const lapses = computed(() => rts.value.filter((r) => r >= LAPSE).length + noResp.value)
const fastCount = computed(() => rts.value.filter((r) => r < FAST).length)
const medianRt = computed(() => {
  const v = rts.value.filter((r) => r >= FAST).sort((a, b) => a - b)
  return v.length ? Math.round(v[Math.floor(v.length / 2)]) : '—'
})
function start() {
  durS = mode.value === 'pvtb_3min' ? 180 : 60
  rts.value = []; falseStarts.value = 0; noResp.value = 0; interruptions.value = 0; saved.value = false
  endAt = performance.now() + durS * 1000
  next()
}
function next() {
  clearTimeout(timer); cancelAnimationFrame(raf)
  remaining.value = Math.max(0, Math.ceil((endAt - performance.now()) / 1000))
  if (performance.now() >= endAt) { phase.value = 'done'; return }
  phase.value = 'wait'
  timer = setTimeout(show, 2000 + Math.random() * 3000)
}
function show() {
  phase.value = 'go'; counter.value = 0
  raf = requestAnimationFrame((ts) => {
    onset = performance.now()
    const tick = () => { counter.value = Math.round(performance.now() - onset); if (phase.value === 'go') raf = requestAnimationFrame(tick) }
    tick()
  })
  timer = setTimeout(() => { if (phase.value === 'go') { noResp.value++; next() } }, TIMEOUT)
}
function hit() {
  if (phase.value === 'go' && onset) {
    rts.value.push(Math.round(performance.now() - onset)); onset = 0; next()
  } else if (phase.value === 'wait') {
    falseStarts.value++; clearTimeout(timer); phase.value = 'early'; timer = setTimeout(next, 800)
  }
}
function onKey(e) { if (e.code === 'Space' && tab.value === 'pvt' && ['wait', 'go'].includes(phase.value)) { e.preventDefault(); hit() } }
function onHide() { if (['wait', 'go', 'early'].includes(phase.value)) interruptions.value++ }
function onVis() { if (document.hidden) onHide() }
function abort() { clearTimeout(timer); cancelAnimationFrame(raf); phase.value = 'idle' }
function reset() { phase.value = 'idle' }
async function savePvt() {
  const r = await act(() => api(`/astronauts/${s.selected}/pvt`, { method: 'POST', body: {
    modo: mode.value, duracion_s: durS, rts: rts.value, anticipaciones: falseStarts.value, sin_respuesta: noResp.value, interrupciones: interruptions.value
  } }))
  saved.value = true
  s.toast(r.valido ? `PVT guardada: ${r.errores} errores (${r.errores_equivalentes_3min} equivalentes a 3 min)` : `PVT inválida: ${r.motivo_invalido}`, r.valido ? 'ok' : 'err')
}
onMounted(() => { window.addEventListener('keydown', onKey); window.addEventListener('blur', onHide); document.addEventListener('visibilitychange', onVis) })
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey); window.removeEventListener('blur', onHide); document.removeEventListener('visibilitychange', onVis)
  clearTimeout(timer); cancelAnimationFrame(raf); clearInterval(tmr)
})

// ---------- Manual
const mm = reactive({ indicator: 'rhr', value: null, unit: 'lpm', day: s.day, source: 'manual' })
watch(() => s.day, (d) => { mm.day = d })
async function sendManual() {
  await act(() => api('/measurements', { method: 'POST', body: { astro_id: s.selected, ...mm } }), 'Medición validada y guardada')
}

// ---------- CSV
const csvText = ref(''); const overwrite = ref(false); const csvRes = ref(null)
function readFile(e) {
  const f = e.target.files[0]
  if (!f) return
  if (f.size > 2_000_000) { s.toast('Archivo demasiado grande (máx. 2 MB)', 'err'); return }
  const r = new FileReader(); r.onload = () => { csvText.value = r.result }; r.readAsText(f)
}
function example() {
  const a = s.selected, d = s.day
  csvText.value = `astro_id,day,indicator,value,unit,source\n${a},${d},rhr,64,bpm,csv\n${a},${d},sleep,6.2,h,csv\n${a},${d},hrv,40,lpm,csv\n${a},${d},sleep,30,h,csv\nZZ9,${d},mood,6,/10,csv\n${a},${d},mood,,/10,csv`
}
async function sendCsv() {
  csvRes.value = await act(() => api('/ingest/csv', { method: 'POST', body: { csv: csvText.value, sobrescribir: overwrite.value } }))
}
</script>

<style scoped>
.who { min-width: 260px; }
.two { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 14px; align-items: start; }
.two > * { min-width: 0; }
@media (max-width: 960px) { .two { grid-template-columns: 1fr; } }
.seg { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; }
.seg button { display: grid; gap: 2px; padding: 8px 4px; border-radius: 8px; background: var(--bg-2); border: 1px solid var(--line); cursor: pointer; color: var(--text); }
.seg button.on { border-color: var(--mars); background: rgba(207,115,73,.15); }
.stage { height: 300px; display: grid; place-items: center; user-select: none; touch-action: manipulation; border-radius: var(--radius); border: 1px solid var(--line); background: #050e1a; }
.stage.go { border-color: var(--mars); }
.counter { font-size: 4.2rem; font-weight: 700; color: var(--mars); }
.early { color: var(--warn); font-weight: 700; font-size: 1.4rem; }
.result { display: grid; gap: 10px; text-align: center; padding: 10px; }
.res { gap: 18px; }
.center-row { justify-content: center; }
.csv { min-height: 160px; font-size: 0.8rem; }
.mt { margin-top: 10px; }
kbd { font-family: var(--mono); background: var(--surface-3); border: 1px solid var(--line); border-radius: 4px; padding: 0 5px; }
code { font-family: var(--mono); font-size: 0.8rem; background: var(--bg-2); padding: 1px 5px; border-radius: 4px; }
</style>

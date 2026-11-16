<template>
  <div class="page">
    <section class="head panel no-print">
      <img class="planet" src="/img/tierra.jpg" alt="Earth" width="72" height="72" />
      <div class="grow">
        <h1>Reports for Earth</h1>
        <p class="small" :class="link.apagon ? 'c-rojo strong' : 'muted'">
          {{ link.apagon ? 'No link: reports wait in the onboard queue.' : `Delayed link: ${fmt(link.retraso_min, 1)} min per message (simulated transmission).` }}</p>
      </div>
      <div class="kpi right"><span class="v">{{ pending }}</span><span class="tiny muted">queued</span></div>
      <button class="btn primary" @click="transmit" :disabled="!pending || busy"><Icon name="send" :size="15" /> Send queue</button>
    </section>

    <section class="layout">
      <aside class="grid no-print">
        <form class="panel grid" @submit.prevent="create">
          <h2>New report</h2>
          <label class="field"><span>For</span><select class="input" v-model="f.astro_id">
            <option :value="null">Whole crew</option>
            <option v-for="c in s.crew" :key="c.id" :value="c.id">{{ c.nombre }}</option></select></label>
          <div class="cols-2">
            <label class="field"><span>From day</span><input class="input" type="number" min="0" :max="s.day" v-model.number="f.desde" /></label>
            <label class="field"><span>To day</span><input class="input" type="number" min="0" :max="s.day" v-model.number="f.hasta" /></label>
          </div>
          <button class="btn primary" :disabled="busy">{{ s.publico ? 'Preview report' : 'Generate and queue' }}</button>
          <p class="tiny muted">What the flight surgeon on Earth would see: summary per person, alerts, actions taken and what is still unacknowledged.</p>
        </form>
        <div class="panel list">
          <button v-for="r in reports" :key="r.id" class="ritem" :class="{ sel: cur?.id === r.id }" @click="open(r.id)">
            <span class="strong small">#{{ r.id }} · {{ r.astro_id ? crewName(r.astro_id) : 'Crew' }}</span>
            <span class="tag" :class="r.estado === 'pendiente' ? '' : 'manual'">{{ r.estado === 'pendiente' ? 'queued' : repState(r.estado) }}</span>
            <span class="tiny muted">Days {{ r.desde }}–{{ r.hasta }}</span>
          </button>
          <p v-if="!reports.length" class="small muted">No reports yet.</p>
        </div>
      </aside>

      <article v-if="cur" class="panel report">
        <div class="row between wrap no-print">
          <span class="tag">{{ cur.estado === 'pendiente' ? 'queued · will be sent when the link is available' : repState(cur.estado) }}</span>
          <div class="row wrap">
            <button class="btn sm" @click="exportJson"><Icon name="download" :size="13" /> JSON</button>
            <button v-if="cur.id" class="btn sm" @click="exportCsv"><Icon name="download" :size="13" /> CSV</button>
            <button class="btn sm" @click="print"><Icon name="printer" :size="13" /> PDF</button>
          </div>
        </div>
        <header>
          <h2>{{ c.mision }}</h2>
          <p class="small muted">{{ cur.id ? `Report #${cur.id}` : 'Preview (public demo: not saved)' }} · days {{ c.periodo.desde }}–{{ c.periodo.hasta }} · generated on day {{ c.generado_dia }}</p>
        </header>
        <section v-for="p in c.tripulantes" :key="p.astronauta.id" class="person">
          <div class="row wrap phead" :class="'n-' + p.nivel_final">
            <Avatar :id="p.astronauta.id" :name="p.astronauta.nombre" :size="40" />
            <h3 class="grow">{{ p.astronauta.nombre }} <span class="muted small">· {{ p.astronauta.rol }}</span></h3>
            <LevelBadge :level="p.nivel_final" />
          </div>
          <div class="table-wrap"><table class="table">
            <thead><tr><th>Indicator</th><th class="right">Mean</th><th class="right">Latest</th><th class="right">Their usual</th><th class="right">Days Watch / Act</th><th class="right">Data</th></tr></thead>
            <tbody><tr v-for="(x, k) in p.indicadores" :key="k"><td>{{ x.nombre }}</td><td class="num right">{{ fmt(x.media, 2) }}</td>
              <td class="num right">{{ fmt(x.ultimo_valor, 2) }}</td><td class="num right">{{ fmt(x.linea_base_final, 2) }}</td>
              <td class="num right"><span class="dchip" :class="{ w: x.dias_amarillo }">{{ x.dias_amarillo }}</span> <span class="dchip" :class="{ a: x.dias_rojo }">{{ x.dias_rojo }}</span></td>
              <td class="num right"><span class="dbar"><i :style="{ width: Math.min(100, x.completitud_pct || 0) + '%' }" :class="{ low: (x.completitud_pct || 0) < 70 }"></i></span> {{ nn(x.completitud_pct) }}%</td></tr></tbody>
          </table></div>
          <div class="chips">
            <span class="chip ok">{{ p.seguimiento.alertas_revisadas }} alerts reviewed</span>
            <span class="chip" :class="p.seguimiento.alertas_pendientes ? 'warn' : 'ok'">{{ p.seguimiento.alertas_pendientes }} unacknowledged</span>
            <span class="chip">{{ p.seguimiento.checkins }} check-ins</span>
            <span class="chip">{{ p.seguimiento.pruebas_pvt }} PVT tests</span>
            <span class="chip" :class="{ warn: p.calidad_datos.registros_rechazados }">{{ p.calidad_datos.registros_rechazados }} rejected records</span>
            <span class="chip rad">radiation {{ fmt(p.radiacion.acumulada_medida_mgy, 1) }} mGy</span>
          </div>
        </section>
      </article>
      <div v-else class="panel muted small">Generate a report to see it here.</div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api, useStore, fmt, nn, download } from '../store.js'
import Icon from '../components/Icon.vue'
import Avatar from '../components/Avatar.vue'
import LevelBadge from '../components/LevelBadge.vue'

const s = useStore()
const busy = ref(false)
const reports = ref([])
const cur = ref(null)
const f = ref({ astro_id: null, desde: Math.max(0, s.day - 13), hasta: s.day })
const c = computed(() => cur.value?.contenido)
const link = computed(() => s.mission.comunicacion)
const pending = computed(() => reports.value.filter((r) => r.estado === 'pendiente').length)
//ESTADO del reporte (identificador interno en español)
const repState = (e) => ({ 'enviado (simulado)': 'sent (simulated)', 'vista previa': 'preview' }[e] || e)
const crewName = (id) => s.crew.find((a) => a.id === id)?.nombre || id

async function load() { reports.value = await api('/reports') }
onMounted(async () => { await load(); if (reports.value.length) open(reports.value[0].id) })
async function open(id) { cur.value = await api(`/reports/${id}`) }
async function create() {
  busy.value = true
  try {
    f.value.hasta = Math.min(f.value.hasta, s.day)
    cur.value = await s.run(() => api('/reports', { method: 'POST', body: f.value }), s.publico ? 'Preview generated' : 'Report queued')
    if (!s.publico) await load()
  } finally { busy.value = false }
}
async function transmit() {
  busy.value = true
  try {
    const r = await s.run(() => api('/reports/transmit', { method: 'POST' }))
    s.toast(r.mensaje, r.enviados ? 'ok' : 'err')
    await load(); if (cur.value) await open(cur.value.id)
  } finally { busy.value = false }
}
function exportJson() { download(`report_${cur.value.id ?? 'preview'}.json`, JSON.stringify(cur.value, null, 2)) }
async function exportCsv() { download(`report_${cur.value.id}.csv`, await api(`/reports/${cur.value.id}/csv`), 'text/csv') }
function print() { window.print() }
</script>

<style scoped>
.head { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.planet { border-radius: 50%; object-fit: cover; clip-path: circle(46%); }
.grow { flex: 1; min-width: 0; }
.layout { display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 14px; align-items: start; }
.layout > * { min-width: 0; }
@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }
.list { display: grid; gap: 6px; }
.ritem { text-align: left; background: var(--surface-2); border: 1px solid var(--line-soft); border-radius: 10px; padding: 9px 11px; cursor: pointer; color: var(--text); display: grid; grid-template-columns: 1fr auto; gap: 3px 8px; }
.ritem.sel { border-color: var(--navy); background: var(--navy); color: #fff; }
.ritem.sel .muted { color: #c9d8f2; }
.phead { background: var(--blue-soft); border-left: 4px solid var(--blue); padding: 8px 12px; border-radius: 0; }
.phead.n-amarillo { background: var(--warn-soft); border-left-color: #c08a00; }
.phead.n-rojo { background: var(--red-soft); border-left-color: var(--red); }
.phead.n-verde { background: var(--ok-soft); border-left-color: var(--ok); }
.dchip { display: inline-block; min-width: 24px; text-align: center; padding: 1px 6px; border-radius: 3px; background: #eef1f5; color: var(--muted); font-weight: 500; }
.dchip.w { background: var(--warn-soft); color: var(--warn); font-weight: 700; }
.dchip.a { background: var(--red-soft); color: var(--red); font-weight: 700; }
.dbar { display: inline-block; width: 46px; height: 6px; background: #e4e9f1; border-radius: 3px; vertical-align: middle; margin-right: 6px; overflow: hidden; }
.dbar i { display: block; height: 100%; background: var(--ok); }
.dbar i.low { background: #c08a00; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { font-size: 0.78rem; padding: 3px 9px; border-radius: 3px; background: var(--blue-soft); color: var(--blue); font-weight: 500; }
.chip.ok { background: var(--ok-soft); color: var(--ok); }
.chip.warn { background: var(--warn-soft); color: var(--warn); }
.chip.rad { background: #efecfa; color: #4a3a8c; }
.report { display: grid; gap: 16px; }
.person { display: grid; gap: 10px; border-top: 1px solid var(--line-soft); padding-top: 14px; }
@media print { .layout { display: block; } }
</style>

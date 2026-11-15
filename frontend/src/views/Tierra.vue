<template>
  <div class="page">
    <section class="head panel no-print">
      <img class="planet" src="/img/tierra.jpg" alt="La Tierra" width="72" height="72" />
      <div class="grow">
        <h1>Reportes para la Tierra</h1>
        <p class="small" :class="link.apagon ? 'c-rojo strong' : 'muted'">
          {{ link.apagon ? 'Sin enlace: los reportes esperan en la cola de a bordo.' : `Enlace diferido: ${fmt(link.retraso_min, 1)} min por mensaje (envío simulado).` }}</p>
      </div>
      <div class="kpi right"><span class="v">{{ pending }}</span><span class="tiny muted">en cola</span></div>
      <button class="btn primary" @click="transmit" :disabled="!pending || busy"><Icon name="send" :size="15" /> Enviar cola</button>
    </section>

    <section class="layout">
      <aside class="grid no-print">
        <form class="panel grid" @submit.prevent="create">
          <h2>Nuevo reporte</h2>
          <label class="field"><span>Para</span><select class="input" v-model="f.astro_id">
            <option :value="null">Toda la tripulación</option>
            <option v-for="c in s.crew" :key="c.id" :value="c.id">{{ c.nombre }}</option></select></label>
          <div class="cols-2">
            <label class="field"><span>Desde el día</span><input class="input" type="number" min="0" :max="s.day" v-model.number="f.desde" /></label>
            <label class="field"><span>Hasta el día</span><input class="input" type="number" min="0" :max="s.day" v-model.number="f.hasta" /></label>
          </div>
          <button class="btn primary" :disabled="busy">{{ s.publico ? 'Previsualizar reporte' : 'Generar y poner en cola' }}</button>
          <p class="tiny muted">Lo que vería la oficial médica en Tierra: resumen por persona, alarmas, acciones y lo que quedó sin reconocer.</p>
        </form>
        <div class="panel list">
          <button v-for="r in reports" :key="r.id" class="ritem" :class="{ sel: cur?.id === r.id }" @click="open(r.id)">
            <span class="strong small">#{{ r.id }} · {{ r.astro_id ? crewName(r.astro_id) : 'Tripulación' }}</span>
            <span class="tag" :class="r.estado === 'pendiente' ? '' : 'manual'">{{ r.estado === 'pendiente' ? 'en cola' : r.estado }}</span>
            <span class="tiny muted">Días {{ r.desde }}–{{ r.hasta }}</span>
          </button>
          <p v-if="!reports.length" class="small muted">Aún no hay reportes.</p>
        </div>
      </aside>

      <article v-if="cur" class="panel report">
        <div class="row between wrap no-print">
          <span class="tag">{{ cur.estado === 'pendiente' ? 'en cola · se enviará cuando haya enlace' : cur.estado }}</span>
          <div class="row wrap">
            <button class="btn sm" @click="exportJson"><Icon name="download" :size="13" /> JSON</button>
            <button v-if="cur.id" class="btn sm" @click="exportCsv"><Icon name="download" :size="13" /> CSV</button>
            <button class="btn sm" @click="print"><Icon name="printer" :size="13" /> PDF</button>
          </div>
        </div>
        <header>
          <h2>{{ c.mision }}</h2>
          <p class="small muted">{{ cur.id ? `Reporte #${cur.id}` : 'Vista previa (demo pública: no se guarda)' }} · días {{ c.periodo.desde }}–{{ c.periodo.hasta }} · generado el día {{ c.generado_dia }}</p>
        </header>
        <section v-for="p in c.tripulantes" :key="p.astronauta.id" class="person">
          <div class="row wrap">
            <Avatar :id="p.astronauta.id" :name="p.astronauta.nombre" :size="40" />
            <h3 class="grow">{{ p.astronauta.nombre }} <span class="muted small">· {{ p.astronauta.rol }}</span></h3>
            <LevelBadge :level="p.nivel_final" />
          </div>
          <div class="table-wrap"><table class="table">
            <thead><tr><th>Indicador</th><th class="right">Media</th><th class="right">Último</th><th class="right">Su normal</th><th class="right">Días vigilar / actuar</th><th class="right">Datos</th></tr></thead>
            <tbody><tr v-for="(x, k) in p.indicadores" :key="k"><td>{{ x.nombre }}</td><td class="num right">{{ fmt(x.media, 2) }}</td>
              <td class="num right">{{ fmt(x.ultimo_valor, 2) }}</td><td class="num right">{{ fmt(x.linea_base_final, 2) }}</td>
              <td class="num right">{{ x.dias_amarillo }} / {{ x.dias_rojo }}</td><td class="num right">{{ nn(x.completitud_pct) }} %</td></tr></tbody>
          </table></div>
          <p class="small muted">{{ p.seguimiento.alertas_revisadas }} alertas revisadas, {{ p.seguimiento.alertas_pendientes }} pendientes ·
            {{ p.seguimiento.checkins }} check-ins · {{ p.seguimiento.pruebas_pvt }} pruebas PVT · {{ p.calidad_datos.registros_rechazados }} datos rechazados ·
            radiación {{ fmt(p.radiacion.acumulada_medida_mgy, 1) }} mGy</p>
        </section>
      </article>
      <div v-else class="panel muted small">Genere un reporte para verlo aquí.</div>
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
const crewName = (id) => s.crew.find((a) => a.id === id)?.nombre || id

async function load() { reports.value = await api('/reports') }
onMounted(async () => { await load(); if (reports.value.length) open(reports.value[0].id) })
async function open(id) { cur.value = await api(`/reports/${id}`) }
async function create() {
  busy.value = true
  try {
    f.value.hasta = Math.min(f.value.hasta, s.day)
    cur.value = await s.run(() => api('/reports', { method: 'POST', body: f.value }), s.publico ? 'Vista previa generada' : 'Reporte en cola')
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
function exportJson() { download(`reporte_${cur.value.id ?? 'vista_previa'}.json`, JSON.stringify(cur.value, null, 2)) }
async function exportCsv() { download(`reporte_${cur.value.id}.csv`, await api(`/reports/${cur.value.id}/csv`), 'text/csv') }
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
.ritem.sel { border-color: var(--blue); background: var(--blue-soft); }
.report { display: grid; gap: 16px; }
.person { display: grid; gap: 10px; border-top: 1px solid var(--line-soft); padding-top: 14px; }
@media print { .layout { display: block; } }
</style>

<template>
  <div class="page">
    <div class="page-head no-print">
      <div>
        <div class="eyebrow">06 · Earth Reports · About the Science</div>
        <h1>{{ tab === 'rep' ? 'Reportes para la Tierra' : 'Sobre la ciencia' }}</h1>
        <p v-if="tab === 'rep'">Los reportes se guardan en la base local y quedan <strong>pendientes</strong> en una cola de envío diferido.
          La transmisión es simulada: no existe integración real con comunicaciones espaciales.</p>
        <p v-else>Método, datos, fuentes y limitaciones. Prototipo educativo y de investigación; no es un dispositivo médico.</p>
      </div>
      <div class="tabs"><button :class="{ on: tab === 'rep' }" @click="tab = 'rep'"><Icon name="send" :size="14" />Reportes</button>
        <button :class="{ on: tab === 'sci' }" @click="tab = 'sci'"><Icon name="book" :size="14" />Ciencia</button></div>
    </div>

    <template v-if="tab === 'rep'">
      <section class="cols-2 no-print">
        <form class="panel grid" @submit.prevent="create">
          <h2><Icon name="file" /> Generar reporte</h2>
          <div class="cols-3">
            <label class="field"><span>Alcance</span><select class="input" v-model="f.astro_id">
              <option :value="null">Toda la tripulación</option>
              <option v-for="c in s.crew" :key="c.id" :value="c.id">{{ c.id }} · {{ c.nombre }}</option></select></label>
            <label class="field"><span>Desde el día</span><input class="input" type="number" min="0" :max="s.day" v-model.number="f.desde" /></label>
            <label class="field"><span>Hasta el día</span><input class="input" type="number" min="0" :max="s.day" v-model.number="f.hasta" /></label>
          </div>
          <div class="row wrap"><button class="btn primary" :disabled="busy"><Icon name="file" :size="14" /> Generar y poner en cola</button>
            <button type="button" class="btn ghost" @click="f.desde = Math.max(0, s.day - 6); f.hasta = s.day">Últimos 7 días</button></div>
        </form>
        <div class="panel grid">
          <h2><Icon :name="s.mission.comunicacion.apagon ? 'signalOff' : 'satellite'" /> Cola de envío diferido</h2>
          <div class="notice small" :class="s.mission.comunicacion.apagon ? 'err' : 'info'">
            {{ s.mission.comunicacion.apagon ? 'SIN ENLACE: los reportes permanecen en la cola local hasta que vuelva la comunicación.'
              : `Enlace diferido: ~${s.mission.comunicacion.retraso_min} min por sentido.` }}</div>
          <div class="row between"><span class="kpi"><span class="v">{{ pending }}</span><span class="tiny muted">pendiente(s)</span></span>
            <button class="btn blue" @click="transmit" :disabled="!pending || busy"><Icon name="send" :size="14" /> Transmitir cola (simulado)</button></div>
        </div>
      </section>

      <section class="layout">
        <div class="panel list no-print">
          <h2>Reportes</h2>
          <p v-if="!reports.length" class="small muted">Aún no hay reportes.</p>
          <button v-for="r in reports" :key="r.id" class="ritem" :class="{ sel: cur?.id === r.id }" @click="open(r.id)">
            <div class="row between"><strong class="small">#{{ r.id }} · {{ r.astro_id || 'Tripulación' }}</strong>
              <span class="tag" :class="r.estado === 'pendiente' ? '' : 'manual'">{{ r.estado }}</span></div>
            <div class="tiny muted">Días {{ r.desde }}–{{ r.hasta }} · creado el día {{ r.dia_creacion }}{{ r.dia_envio !== null ? ` · enviado el día ${r.dia_envio}` : '' }}</div>
          </button>
        </div>

        <article v-if="cur" class="panel report">
          <div class="row between wrap no-print">
            <span class="tag">{{ cur.estado }}</span>
            <div class="row wrap">
              <button class="btn sm" @click="exportJson"><Icon name="download" :size="13" /> JSON</button>
              <button class="btn sm" @click="exportCsv"><Icon name="download" :size="13" /> CSV</button>
              <button class="btn sm" @click="print"><Icon name="printer" :size="13" /> PDF (imprimir)</button>
            </div>
          </div>
          <header>
            <div class="label">{{ c.tipo }}</div>
            <h2>{{ c.mision }}</h2>
            <p class="small muted">Reporte #{{ cur.id }} · periodo días {{ c.periodo.desde }}–{{ c.periodo.hasta }} · generado el día {{ c.generado_dia }} ·
              detector: vigilar ≥ {{ c.parametros_detector.yellow }}, actuar ≥ {{ c.parametros_detector.red }}, ventana {{ c.parametros_detector.window }} d</p>
            <p class="tiny faint">{{ c.aviso }}</p>
          </header>
          <section v-for="p in c.tripulantes" :key="p.astronauta.id" class="person">
            <div class="row between wrap">
              <h3>{{ p.astronauta.nombre }} <span class="muted small">· {{ p.astronauta.rol }}</span></h3>
              <div class="row"><LevelBadge :level="p.nivel_final" /><span class="small muted">índice {{ p.indice_final ?? '—' }}/100</span></div>
            </div>
            <div class="table-wrap"><table class="table">
              <thead><tr><th>Indicador</th><th>Media</th><th>Mín–máx</th><th>Último</th><th>Línea base</th><th>z máx</th><th>Días ámbar/rojo</th><th>Completitud</th></tr></thead>
              <tbody><tr v-for="(x, k) in p.indicadores" :key="k"><td>{{ x.nombre }}</td><td class="num">{{ fmt(x.media, 2) }}</td>
                <td class="num">{{ fmt(x.min, 1) }}–{{ fmt(x.max, 1) }}</td><td class="num">{{ fmt(x.ultimo_valor, 2) }}</td>
                <td class="num">{{ fmt(x.linea_base_final, 2) }}</td><td class="num">{{ fmt(x.z_max, 1) }}</td>
                <td class="num">{{ x.dias_amarillo }} / {{ x.dias_rojo }}</td><td class="num">{{ x.completitud_pct }} %</td></tr></tbody>
            </table></div>
            <div class="cols-3 facts small">
              <div><div class="label">Cambios relevantes</div><ul><li v-for="(x, i) in p.cambios_relevantes" :key="i">{{ x }}</li>
                <li v-if="!p.cambios_relevantes.length" class="muted">Ninguno sobre el corte "vigilar".</li></ul></div>
              <div><div class="label">Calidad de datos</div><ul><li>Completitud media {{ p.calidad_datos.completitud_media_pct }} %</li>
                <li>{{ p.calidad_datos.registros_rechazados }} registro(s) rechazado(s) en la ingesta</li></ul></div>
              <div><div class="label">Seguimiento realizado</div><ul><li>{{ p.seguimiento.alertas_revisadas }} alertas revisadas · {{ p.seguimiento.alertas_pendientes }} pendientes</li>
                <li>{{ p.seguimiento.checkins }} check-ins · {{ p.seguimiento.pruebas_pvt }} pruebas PVT</li>
                <li>Radiación medida: {{ p.radiacion.acumulada_medida_mgy }} mGy ({{ p.radiacion.porcentaje_del_presupuesto }} % del presupuesto del escenario)</li></ul></div>
            </div>
            <details v-if="p.alertas.length"><summary class="label">Alertas del periodo ({{ p.alertas.length }})</summary>
              <ul class="small alerts"><li v-for="a in p.alertas.slice(0, 40)" :key="a.id">D{{ a.dia }} · <span :class="'c-' + a.nivel">{{ a.nivel }}</span> ·
                {{ a.titulo }} · <em>{{ a.estado }}</em><span v-if="a.nota"> — “{{ a.nota }}”</span></li></ul></details>
          </section>
        </article>
        <div v-else class="panel muted small no-print">Seleccione o genere un reporte para verlo.</div>
      </section>
    </template>

    <template v-else>
      <section class="cols-2">
        <div class="panel grid">
          <h2>Pregunta y propuesta</h2>
          <p class="small">¿Cómo puede un astronauta identificar cambios importantes en su salud y decidir qué seguimiento realizar
            cuando no puede comunicarse de inmediato con la Tierra? BASAL compara a cada persona <strong>consigo misma</strong>:
            aprende su línea base y avisa cuando un indicador deja de comportarse como de costumbre.</p>
          <div class="sub mono small formula">z = (valor de hoy − mediana de los días previos) / (1,4826 × MAD)</div>
          <ul class="small defs">
            <li>Ventana: {{ s.mission.parametros.window }} días previos válidos (mín. {{ s.mission.parametros.min_periods }}); el valor de hoy nunca entra en su referencia.</li>
            <li>Los días en alerta se excluyen de la línea base para que un deterioro persistente no se normalice.</li>
            <li>También se compara con los primeros 14 días válidos de misión (deterioros lentos) y se usa el mayor de los dos z.</li>
            <li>MAD casi cero: se usa una dispersión mínima por indicador (resolución práctica de la medida).</li>
            <li>Cortes experimentales: vigilar |z| ≥ {{ s.mission.parametros.yellow }}, actuar ≥ {{ s.mission.parametros.red }} o {{ s.mission.parametros.persist }} días seguidos en vigilar ({{ s.mission.parametros.origen }}). No son límites médicos.</li>
            <li>Sin medición → “sin dato”; con menos de 7 observaciones → “calibrando”. Nunca se asume normalidad.</li>
          </ul>
        </div>
        <div class="panel grid">
          <h2>Qué es real y qué es simulado</h2>
          <table class="table">
            <tbody>
              <tr><td class="strong">Simulado</td><td class="small">Todas las mediciones de la demo (simulador con semilla), astronautas ficticios, eventos de salud, apagón y transmisión de reportes.</td></tr>
              <tr><td class="strong">De la literatura</td><td class="small">Orden de magnitud de la tasa de dosis (~0,4 mGy/día; Patel et al., 2020), definición de lapso PVT-B ≥ 355 ms (Basner et al., 2011), recomendación de sueño ≥ 7 h (Watson et al., 2015), inspiración del método (AnomalyDetect; Mishra et al., 2020).</td></tr>
              <tr><td class="strong">Decisiones de ingeniería</td><td class="small">Ventana de 14 días, dispersiones mínimas, rangos de plausibilidad, cortes ajustados con el simulador, reglas de recomendación.</td></tr>
              <tr><td class="strong">Hipótesis</td><td class="small">Que la línea base individual detecta antes y con menos falsas alarmas cuando las diferencias entre personas son grandes. Se pone a prueba en el Validation Lab; no se asume.</td></tr>
              <tr><td class="strong">Datos NASA</td><td class="small">No se incluyen mediciones individuales de OSDR / Inspiration4 ni de Mars-520 en el MVP. Integrarlas (vía CSV con el esquema documentado) es trabajo pendiente.</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="panel">
        <h2>Indicadores</h2>
        <div class="table-wrap"><table class="table">
          <thead><tr><th>Indicador</th><th>Sensor</th><th>Unidad</th><th>Empeora si</th><th>Umbral fijo (comparador)</th><th>Referencia clínica</th></tr></thead>
          <tbody><tr v-for="(c, k) in s.indicators" :key="k"><td class="strong"><Icon :name="IND_ICON[k]" :size="14" /> {{ c.nombre }}</td>
            <td class="small">{{ c.sensor }}</td><td class="mono small">{{ c.unidad }}</td><td>{{ c.direction > 0 ? '↑ sube' : '↓ baja' }}</td>
            <td class="num">{{ c.umbral_fijo }}</td><td class="small muted">{{ c.clinical }}</td></tr></tbody>
        </table></div>
      </section>

      <section class="cols-2">
        <div class="panel">
          <h2>Fuentes y nivel de evidencia</h2>
          <ul class="refs small">
            <li v-for="e in ev" :key="e.id"><span>{{ e.cita }}</span> <a :href="e.url" class="faint tiny" target="_blank" rel="noopener">{{ e.url }}</a>
              <div class="tiny muted"><span class="tag">{{ e.tipo }}</span> {{ e.nivel }}<span v-if="!e.en_propuesta"> · añadida (no estaba en la propuesta)</span></div></li>
          </ul>
        </div>
        <div class="panel">
          <h2>Limitaciones</h2>
          <ul class="small defs">
            <li>Validado solo con datos sintéticos; sin validación clínica ni con datos reales de astronautas.</li>
            <li>Las recomendaciones son orientaciones de seguimiento generadas por reglas; no diagnostican ni prescriben. Las alertas rojas remiten al oficial médico y a los protocolos autorizados.</li>
            <li>La PVT-B en navegador no corrige la latencia del equipo; la versión de 60 s no equivale al protocolo de 3 minutos.</li>
            <li>El ánimo es un autorreporte de una sola pregunta, no un instrumento psicológico validado.</li>
            <li>La línea base inicial puede dar avisos tardíos si la persona se adapta legítimamente a un nuevo estado (p. ej., adaptación a la microgravedad); falta un mecanismo de “aceptar nueva línea base” por el oficial médico.</li>
            <li>La dosis acumulada se compara con un presupuesto del escenario simulado, no con límites de exposición de NASA.</li>
            <li>Uso operacional requeriría: sensores reales certificados, validación con datos de vuelo/análogos, revisión médica de las reglas, ciberseguridad y control de acceso, y aprobación regulatoria.</li>
          </ul>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api, useStore, fmt, download, IND_ICON } from '../store.js'
import Icon from '../components/Icon.vue'
import LevelBadge from '../components/LevelBadge.vue'

const s = useStore()
const tab = ref('rep')
const busy = ref(false)
const reports = ref([])
const cur = ref(null)
const ev = ref([])
const f = ref({ astro_id: null, desde: 0, hasta: s.day })

const c = computed(() => cur.value?.contenido)
const pending = computed(() => reports.value.filter((r) => r.estado === 'pendiente').length)

async function load() { reports.value = await api('/reports') }
onMounted(async () => { await load(); if (reports.value.length) open(reports.value[0].id); ev.value = await api('/evidence') })
async function open(id) { cur.value = await api(`/reports/${id}`) }
async function create() {
  busy.value = true
  try {
    f.value.hasta = Math.min(f.value.hasta, s.day)
    const r = await s.run(() => api('/reports', { method: 'POST', body: f.value }), 'Reporte generado y en cola')
    await load(); cur.value = r
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
function exportJson() { download(`reporte_${cur.value.id}.json`, JSON.stringify(cur.value, null, 2)) }
async function exportCsv() { download(`reporte_${cur.value.id}.csv`, await api(`/reports/${cur.value.id}/csv`), 'text/csv') }
function print() { window.print() }
</script>

<style scoped>
.layout { display: grid; grid-template-columns: 280px minmax(0, 1fr); gap: 14px; align-items: start; }
.layout > * { min-width: 0; }
@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }
.list { display: grid; gap: 6px; }
.ritem { text-align: left; background: var(--surface-2); border: 1px solid var(--line-soft); border-radius: 8px; padding: 9px 11px; cursor: pointer; color: var(--text); display: grid; gap: 3px; }
.ritem.sel { border-color: var(--blue); }
.report { display: grid; gap: 16px; }
.person { display: grid; gap: 10px; border-top: 1px solid var(--line-soft); padding-top: 14px; }
.facts ul, .alerts { margin: 4px 0 0; padding-left: 16px; display: grid; gap: 3px; }
.formula { text-align: center; padding: 12px; color: #bfe6fa; }
.defs { margin: 0; padding-left: 18px; display: grid; gap: 6px; line-height: 1.5; }
.refs { margin: 8px 0 0; padding-left: 16px; display: grid; gap: 10px; line-height: 1.45; }
.refs a { word-break: break-all; }
@media print { .layout { display: block; } .report { border: 0; } }
</style>

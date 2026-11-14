<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="eyebrow">01 · Mission Overview · Medical Officer</div>
        <h1>Estado de la tripulación — día {{ s.day }}</h1>
        <p>Cada indicador se compara con la línea base de la propia persona. Verde = dentro de lo habitual; vigilar y actuar
          indican desviaciones estadísticas, no diagnósticos.</p>
      </div>
      <div v-if="s.mission.comunicacion.apagon" class="notice err small"><Icon name="signalOff" />
        Apagón de comunicaciones (días {{ s.mission.apagon[0] }}–{{ s.mission.apagon[1] }}): el sistema sigue operando a bordo.</div>
    </div>

    <section class="cols-4">
      <div class="panel kpi"><span class="label">Tripulación</span><span class="v">{{ s.crew.length }}<small>astronautas</small></span>
        <span class="tiny muted">{{ counts.verde }} normal · {{ counts.amarillo }} vigilar · {{ counts.rojo }} actuar</span></div>
      <div class="panel kpi"><span class="label">Alertas de hoy</span><span class="v">{{ todayAlerts }}</span>
        <span class="tiny muted">en {{ s.crew.filter((a) => a.alertas_hoy).length }} astronauta(s)</span></div>
      <div class="panel kpi"><span class="label">Pendientes de revisión</span><span class="v">{{ pendingTotal }}</span>
        <span class="tiny muted">hasta el día {{ s.day }} · {{ queueRed }} rojas</span></div>
      <div class="panel kpi"><span class="label">Calidad de datos (14 d)</span><span class="v">{{ quality }}<small>%</small></span>
        <span class="tiny muted">mediciones válidas disponibles</span></div>
    </section>

    <section class="crew">
      <article v-for="a in s.crew" :key="a.id" class="panel card edge" :class="a.nivel" tabindex="0"
               @click="open(a.id)" @keydown.enter="open(a.id)">
        <div class="row between">
          <div class="row">
            <div class="avatar" :class="a.nivel">{{ initials(a.nombre) }}</div>
            <div>
              <h3>{{ a.nombre }}</h3>
              <div class="tiny muted">{{ a.rol }} · {{ a.id }}</div>
            </div>
          </div>
          <LevelBadge :level="a.nivel" />
        </div>
        <div class="row between idx">
          <div><span class="label">Índice de estabilidad</span>
            <div class="num"><strong class="big">{{ a.indice ?? '—' }}</strong><span class="muted small">/100</span></div></div>
          <div class="right tiny muted">100 = todo en su rango habitual<br />Datos 14 d: {{ a.calidad_pct }} %</div>
        </div>
        <div class="chips">
          <div v-for="(v, k) in a.indicadores" :key="k" class="chip" :class="v.nivel" :title="`${s.indicators[k]?.nombre}: ${LEVEL[v.nivel].label}`">
            <Icon :name="IND_ICON[k]" :size="14" />
            <span class="tiny">{{ s.indicators[k]?.corto }}</span>
            <Icon :name="LEVEL[v.nivel].icon" :size="12" :stroke="2.6" class="st" />
          </div>
        </div>
        <p class="small top-alert" v-if="a.alerta_principal"><Icon name="triangle" :size="13" /> {{ a.alerta_principal }}</p>
        <p class="small muted" v-else>Sin alertas hoy.</p>
      </article>
    </section>

    <section class="officer">
      <div class="panel">
        <div class="panel-head">
          <h2><Icon name="layers" /> Matriz de la tripulación (z robusto de hoy)</h2>
          <span class="tiny muted">positivo = peor que lo habitual · celdas con icono y texto</span>
        </div>
        <div class="table-wrap">
          <table class="table matrix">
            <thead><tr><th>Astronauta</th><th v-for="(cfg, k) in s.indicators" :key="k">{{ cfg.corto }}</th></tr></thead>
            <tbody>
              <tr v-for="a in s.crew" :key="a.id" @click="open(a.id)" class="clickable">
                <td class="strong">{{ a.nombre }}</td>
                <td v-for="(cfg, k) in s.indicators" :key="k">
                  <span class="cell" :class="a.indicadores[k].nivel">
                    <Icon :name="LEVEL[a.indicadores[k].nivel].icon" :size="12" />
                    <span class="mono">{{ a.indicadores[k].z ?? LEVEL[a.indicadores[k].nivel].label }}</span>
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel queue">
        <div class="panel-head">
          <h2><Icon name="stethoscope" /> Cola del oficial médico</h2>
          <div class="tabs">
            <button v-for="f in FILTERS" :key="f.k" :class="{ on: filter === f.k }" @click="filter = f.k">{{ f.l }}</button>
          </div>
        </div>
        <p class="tiny muted">Alertas pendientes de los últimos 7 días. Las amarillas son avisos para vigilar; las rojas
          requieren evaluación del oficial médico según protocolo.</p>
        <div v-if="loading" class="skeleton" />
        <div v-else-if="!queue.length" class="notice info small"><Icon name="check" /> No hay alertas pendientes con este filtro.</div>
        <div v-else class="list">
          <div v-for="a in queue.slice(0, 12)" :key="a.id" class="item edge" :class="a.nivel">
            <button class="item-main" @click="toggle(a.id)" :aria-expanded="openId === a.id">
              <LevelBadge :level="a.nivel" />
              <div class="grow">
                <div class="small strong">{{ a.titulo }}</div>
                <div class="tiny muted">{{ crewName(a.astro_id) }} · día {{ a.day }} · {{ a.indicadores.map((k) => s.indicators[k]?.corto).join(' + ') }}</div>
              </div>
              <Icon name="chevron" :size="14" :class="{ rot: openId === a.id }" />
            </button>
            <AlertCard v-if="openId === a.id" :a="a" @changed="reviewed" />
          </div>
          <p v-if="queue.length > 12" class="tiny muted">… y {{ queue.length - 12 }} más (ver en Salud y alertas).</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, useStore, LEVEL, IND_ICON } from '../store.js'
import Icon from '../components/Icon.vue'
import LevelBadge from '../components/LevelBadge.vue'
import AlertCard from '../components/AlertCard.vue'

const s = useStore()
const router = useRouter()
const alerts = ref([])
const loading = ref(true)
const filter = ref('rojo')
const openId = ref(null)
const FILTERS = [{ k: 'rojo', l: 'Rojas' }, { k: 'todas', l: 'Todas' }]

async function load() {
  try { alerts.value = await api('/alerts?estado=pendiente') } finally { loading.value = false }
}
async function reviewed() { await load(); await s.refresh() }
watch(() => s.day, load, { immediate: true })

const queue = computed(() => alerts.value
  .filter((a) => a.day > s.day - 7)
  .filter((a) => filter.value === 'todas' || a.nivel === 'rojo'))
const queueRed = computed(() => alerts.value.filter((a) => a.nivel === 'rojo' && a.day > s.day - 7).length)
const counts = computed(() => s.crew.reduce((c, a) => { c[a.nivel] = (c[a.nivel] || 0) + 1; return c }, { verde: 0, amarillo: 0, rojo: 0 }))
const todayAlerts = computed(() => s.crew.reduce((n, a) => n + a.alertas_hoy, 0))
const pendingTotal = computed(() => s.crew.reduce((n, a) => n + a.pendientes, 0))
const quality = computed(() => Math.round(s.crew.reduce((n, a) => n + a.calidad_pct, 0) / Math.max(s.crew.length, 1)))
const initials = (n) => n.replace(/^[^ ]+\. /, '').split(' ').map((w) => w[0]).join('').slice(0, 2)
const crewName = (id) => s.crew.find((a) => a.id === id)?.nombre || id
const toggle = (id) => { openId.value = openId.value === id ? null : id }
function open(id) { s.select(id); router.push(`/salud/${id}`) }
</script>

<style scoped>
.crew { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(280px, 100%), 1fr)); gap: 14px; }
.card { cursor: pointer; display: grid; gap: 12px; transition: transform .12s, border-color .12s; }
.card:hover { transform: translateY(-2px); border-color: var(--line); }
.avatar { width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center; font-weight: 700; font-size: 0.85rem; background: var(--surface-3); border: 2px solid var(--gray); }
.avatar.verde { border-color: var(--ok); } .avatar.amarillo { border-color: var(--warn); } .avatar.rojo { border-color: var(--red); }
.big { font-size: 1.6rem; letter-spacing: -0.02em; }
.idx { align-items: flex-end; }
.chips { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.chip { display: flex; align-items: center; gap: 5px; padding: 5px 7px; border-radius: 7px; background: var(--bg-2); border: 1px solid var(--line-soft); color: var(--muted); }
.chip .st { margin-left: auto; }
.chip.verde .st { color: var(--ok); } .chip.amarillo { color: var(--warn); border-color: rgba(242,184,93,.35); }
.chip.rojo { color: #ff9a9f; border-color: rgba(231,106,112,.5); background: rgba(231,106,112,.08); }
.top-alert { color: var(--warn); display: flex; gap: 6px; align-items: center; }
.officer { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); gap: 14px; align-items: start; }
.officer > * { min-width: 0; }
@media (max-width: 1050px) { .officer { grid-template-columns: 1fr; } }
.matrix td, .matrix th { text-align: center; }
.matrix td:first-child, .matrix th:first-child { text-align: left; }
.clickable { cursor: pointer; }
.clickable:hover td { background: var(--surface-2); }
.cell { display: inline-flex; gap: 4px; align-items: center; padding: 2px 7px; border-radius: 6px; font-size: 0.8rem; }
.cell.verde { color: var(--ok); } .cell.amarillo { color: var(--warn); background: rgba(242,184,93,.1); }
.cell.rojo { color: #ff9a9f; background: rgba(231,106,112,.14); } .cell.sin_dato, .cell.calibrando { color: var(--gray); }
.queue { display: grid; gap: 10px; }
.list { display: grid; gap: 8px; }
.item { background: var(--surface-2); border-radius: var(--radius-sm); overflow: hidden; }
.item-main { width: 100%; display: flex; gap: 10px; align-items: center; background: transparent; border: 0; padding: 10px 12px; cursor: pointer; text-align: left; }
.item-main:hover { background: var(--surface-3); }
.grow { flex: 1; min-width: 0; }
.rot { transform: rotate(90deg); }
</style>

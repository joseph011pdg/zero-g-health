<template>
  <div class="page">
    <div v-if="!a" class="skeleton" style="height: 420px" />
    <template v-else>
      <header class="head">
        <router-link to="/" class="btn ghost sm back"><Icon name="prev" :size="13" /> Crew</router-link>
        <div class="id">
          <div class="ring" :class="a.nivel"><Avatar :id="a.id" :name="a.nombre" :size="64" /></div>
          <div>
            <div class="row wrap"><h1>{{ a.nombre }}</h1><LevelBadge :level="a.nivel" /></div>
            <div class="muted small">{{ a.rol }} · day {{ a.dia }}<span v-if="a.indice !== null"> · stability {{ a.indice }}/100</span></div>
          </div>
        </div>
        <div class="row wrap actions">
          <button class="btn" @click="sheet = 'checkin'"><Icon name="smile" :size="16" /> Check-in</button>
          <button class="btn primary" @click="sheet = 'pvt'"><Icon name="target" :size="16" /> PVT test</button>
        </div>
      </header>

      <nav class="switch" aria-label="Switch astronaut">
        <router-link v-for="c in s.crew" :key="c.id" :to="`/crew/${c.id}`" :class="{ on: c.id === id }" :title="c.nombre">
          <Avatar :id="c.id" :name="c.nombre" :size="32" />
          <Icon :name="LEVEL[c.nivel].icon" :size="12" :stroke="2.6" class="st" :class="'c-' + c.nivel" />
        </router-link>
      </nav>

      <section class="grid">
        <div v-if="!todayAlerts.length" class="panel okp" :class="{ open: openEps.length }">
          <Icon :name="openEps.length ? 'clock' : 'check'" :size="22" :class="openEps.length ? 'c-rojo' : 'c-verde'" />
          <div v-if="!openEps.length"><strong>Today: everything within their usual range</strong>
            <p class="small muted">No indicator is away from their usual values. An indicator with no data shows “No data”, never normal.</p></div>
          <div v-else><strong>Today: values within their usual range · {{ openEps.length === 1 ? 'one alert is still open' : `${openEps.length} alerts are still open` }}</strong>
            <p class="small muted">An alert does not close by itself when the value returns to normal: the Medical Officer must acknowledge or resolve it.</p></div>
        </div>
        <AlertCard v-for="al in todayAlerts" :key="al.id" :a="al" :since="sinceOf(al)" @changed="load" />
        <template v-if="openEps.length">
          <p v-for="g in openEps" :key="'t' + g.key" class="small openline"><Icon name="clock" :size="14" />
            Alert from day {{ g.rep.day }} still open (unacknowledged for {{ plural(a.dia - g.rep.day, 'day', 'days') }})</p>
          <AlertCard v-for="g in openEps" :key="g.key" :a="g.rep" :since="g.since" @changed="load" />
        </template>
      </section>

      <section class="tiles" aria-label="Indicadores">
        <button v-for="(v, k, ti) in a.indicadores" :key="k" class="panel tile rise" :style="{ '--i': ti }" :class="[v.nivel, { sel: ind === k }]" @click="ind = k" :aria-pressed="ind === k">
          <div class="row between">
            <span class="row label"><Icon :name="IND_ICON[k]" :size="15" />{{ s.indicators[k].corto }}</span>
            <LevelBadge :level="v.nivel" icon-only />
          </div>
          <div class="row between end">
            <div class="val num" :class="'c-' + (v.nivel === 'verde' ? 'none' : v.nivel)">{{ fmt(v.valor, s.indicators[k].decimales) }} <small>{{ s.indicators[k].unidad }}</small></div>
            <Icon :name="trendIcon(k, v.tendencia_dia)" :size="18" :class="trendClass(k, v.tendencia_dia)" />
          </div>
          <div class="small muted">Their usual: <span class="num">{{ fmt(v.linea_base, s.indicators[k].decimales) }}</span>
            <span v-if="v.fuente && v.fuente !== 'sintetico'" class="tag manual">{{ SRC_LABEL[v.fuente] }}</span></div>
        </button>
      </section>

      <section class="panel">
        <div class="panel-head">
          <div>
            <h2><Icon :name="IND_ICON[ind]" :size="18" /> {{ s.indicators[ind].nombre }}</h2>
            <p class="tiny muted fresh">{{ freshness }}</p>
          </div>
          <div class="row wrap no-print">
            <div class="tabs">
              <button v-for="r in RANGES" :key="r.v" :class="{ on: range === r.v }" @click="range = r.v">{{ r.l }}</button>
            </div>
            <label class="row tiny"><input type="checkbox" v-model="showFixed" /> Population threshold</label>
            <label class="row tiny"><input type="checkbox" v-model="showTruth" /> Simulated events</label>
          </div>
        </div>
        <TrendChart :data="chartData" :unidad="s.indicators[ind].unidad" :nombre="s.indicators[ind].corto"
                    :decimales="s.indicators[ind].decimales" :fijo="s.indicators[ind].umbral_fijo" :show-fixed="showFixed"
                    :events="showTruth ? truth.filter((e) => e.afecta.split(',').includes(ind)) : []" :height="280" />
      </section>

      <section class="cols-2">
        <div class="panel">
          <h2 class="mb"><Icon name="radiation" :size="18" /> Cumulative radiation</h2>
          <div class="kpi"><span class="v">{{ fmt(a.radiacion.acumulada_medida_mgy, 1) }} <small>mGy</small></span></div>
          <div class="bar"><div :style="{ width: Math.min(a.radiacion.porcentaje_del_presupuesto, 150) / 1.5 + '%' }" :class="{ over: a.radiacion.porcentaje_del_presupuesto > 110 }" /></div>
          <p class="small"><b class="num">{{ fmt(a.radiacion.porcentaje_del_presupuesto, 0) }}%</b> of what is expected to date ({{ fmt(a.radiacion.presupuesto_escenario_mgy, 1) }} mGy) · {{ plural(a.radiacion.dias_sin_lectura, 'day', 'days') }} without a reading</p>
          <p class="tiny muted">{{ a.radiacion.supuesto }} The alert watches the daily rate against each person's usual values.</p>
        </div>
        <div class="panel">
          <h2 class="mb"><Icon name="clipboard" :size="18" /> History</h2>
          <div class="hist">
            <div v-for="h in a.historial_alertas.filter((x) => x.nivel === 'rojo').slice(0, 6)" :key="h.id" class="hrow">
              <LevelBadge :level="h.nivel" icon-only /><span class="small grow">{{ h.titulo }}</span><span class="tiny muted">day {{ h.day }}</span>
            </div>
            <div v-for="c in a.checkins.slice(0, 3)" :key="'c' + c.id" class="hrow">
              <Icon name="smile" :size="15" class="muted" /><span class="small grow">Check-in: mood {{ fmt(c.animo, 1) }}/10, sleep {{ c.calidad_sueno }}/5</span><span class="tiny muted">day {{ c.day }}</span>
            </div>
            <div v-for="p in a.pvt.slice(0, 3)" :key="'p' + p.id" class="hrow">
              <Icon name="target" :size="15" class="muted" /><span class="small grow">PVT: {{ plural(p.errores, 'lapse', 'lapses') }}{{ p.valido ? '' : ' (invalid)' }}</span><span class="tiny muted">day {{ p.day }}</span>
            </div>
            <p v-if="!a.historial_alertas.some((x) => x.nivel === 'rojo') && !a.checkins.length && !a.pvt.length" class="small muted">No notable events.</p>
          </div>
        </div>
      </section>
    </template>

    <CheckinSheet v-if="sheet === 'checkin' && a" :astro="a" @close="sheet = null" @saved="load" />
    <PvtSheet v-if="sheet === 'pvt' && a" :astro="a" @close="sheet = null" @saved="load" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api, useStore, fmt, plural, episodes, LEVEL, IND_ICON, SRC_LABEL } from '../store.js'
import Icon from '../components/Icon.vue'
import Avatar from '../components/Avatar.vue'
import LevelBadge from '../components/LevelBadge.vue'
import AlertCard from '../components/AlertCard.vue'
import TrendChart from '../components/TrendChart.vue'
import CheckinSheet from '../components/CheckinSheet.vue'
import PvtSheet from '../components/PvtSheet.vue'

const props = defineProps({ id: String })
const s = useStore()
const router = useRouter()
const route = useRoute()
const a = ref(null)
const truth = ref([])
const ind = ref('rhr')
const range = ref(60)
const showFixed = ref(true)
const showTruth = ref(false)
//?action=checkin | pvt abre directamente el panel (botones de la portada)
const sheet = ref(['checkin', 'pvt'].includes(route.query.action) ? route.query.action : null)
const RANGES = [{ v: 14, l: '14 d' }, { v: 30, l: '30 d' }, { v: 60, l: '60 d' }, { v: 999, l: 'All' }]
let manual = false

const hist = computed(() => (a.value ? s.withAcks(a.value.historial_alertas) : []))
const eps = computed(() => (a.value ? episodes(hist.value, a.value.dia) : []))
const todayAlerts = computed(() => (a.value ? s.withAcks(a.value.alertas) : []))
// Episodios abiertos (sin reconocer) que hoy ya no generan alerta
// Solo se muestran cuando hoy no hay alertas: así una alerta abierta nunca queda oculta tras un "normal"
const openEps = computed(() => (todayAlerts.value.length ? [] : eps.value.filter((g) => g.rep.estado === 'pendiente'
  && g.rep.nivel === 'rojo' && g.rep.day < a.value.dia)))
const sinceOf = (al) => eps.value.find((g) => g.key === `${al.astro_id}|${al.episodio}|${al.nivel}`)?.since ?? null

async function load() {
  try {
    a.value = await api(`/astronauts/${props.id}`)
    truth.value = await api(`/events?astro_id=${props.id}`)
    const top = a.value.alertas.find((x) => x.nivel === 'rojo') || a.value.alertas[0]
    if (top && !manual) ind.value = top.indicadores[0]
  } catch (e) {
    s.toast(e.message, 'err')
    if (String(e.message).includes('no encontrado')) router.replace('/')
  }
}
watch(() => props.id, () => { manual = false; s.select(props.id) })
watch(() => [props.id, s.tick], load, { immediate: true })
watch(ind, () => { manual = true })

const freshness = computed(() => {
  if (!a.value) return ''
  const pts = a.value.series[ind.value]
  const last = [...pts].reverse().find((p) => p.valor !== null)
  const q = a.value.indicadores[ind.value].calidad_14d_pct
  const when = !last ? 'no measurements' : last.day === a.value.dia ? 'last measurement: today' : `last measurement: ${plural(a.value.dia - last.day, 'day', 'days')} ago`
  return `${when} · data in 14 days: ${q ?? 0}%${q !== null && q < 70 ? ' · low reliability' : ''}`
})
const chartData = computed(() => (a.value ? a.value.series[ind.value].slice(-range.value) : []))
function trendIcon(k, t) {
  if (t === null || t === undefined || Math.abs(t) < (s.indicators[k].min_spread / 7)) return 'trendFlat'
  return t > 0 ? 'trendUp' : 'trendDown'
}
function trendClass(k, t) {
  if (trendIcon(k, t) === 'trendFlat') return 'faint'
  return (t > 0) === (s.indicators[k].direction > 0) ? 'c-amarillo' : 'c-verde'
}
</script>

<style scoped>
.head { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.back { margin-right: 4px; }
.id { display: flex; align-items: center; gap: 14px; flex: 1; min-width: 260px; }
.ring { border-radius: 50%; padding: 3px; border: 3px solid var(--line); flex: none; }
.ring.verde { border-color: var(--ok); } .ring.amarillo { border-color: #d99100; } .ring.rojo { border-color: var(--red); }
.actions .btn { min-height: 44px; padding: 10px 18px; }
@media (max-width: 640px) {
  /* Check-in y PVT: dos columnas iguales a todo el ancho */
  .actions { display: grid; grid-template-columns: 1fr 1fr; width: 100%; }
  .actions .btn { justify-content: center; }
}
.switch { display: flex; gap: 8px; }
.switch a { position: relative; border-radius: 50%; padding: 2px; border: 2px solid transparent; opacity: .7; }
.switch a.on { border-color: var(--blue); opacity: 1; }
.switch a:hover { opacity: 1; }
.switch .st { position: absolute; right: -2px; bottom: -2px; background: #fff; border-radius: 50%; }
.okp.open { border-top-color: var(--red); }
.openline { display: flex; gap: 6px; align-items: center; color: var(--red); font-weight: 600; margin: 4px 0 -6px; }
.okp { display: flex; gap: 12px; align-items: flex-start; border-top: 2px solid var(--ok); border-radius: 0; }
.tiles { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; }
@media (max-width: 1100px) { .tiles { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 560px) { .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); } .val { font-size: 1.4rem; } }
.tile { text-align: left; cursor: pointer; display: grid; gap: 6px; padding: 14px 16px; color: var(--text); transition: border-color .15s; }
.tile:hover { border-color: #b8c7e3; }
.tile.sel { border: 2px solid var(--blue); padding: 13px 15px; }
.end { align-items: flex-end; }
.val { font-size: 1.7rem; font-weight: 600; letter-spacing: -0.02em; }
.val small { font-size: 0.8rem; color: var(--muted); margin-left: 1px; font-weight: 500; }
.fresh { margin-top: 2px; }
.mb { margin-bottom: 10px; display: flex; gap: 8px; align-items: center; }
.bar { height: 8px; background: var(--surface-2); border-radius: 4px; overflow: hidden; margin: 8px 0; }
.bar div { height: 100%; background: var(--blue); }
.bar div.over { background: #d99100; }
.hist { display: grid; gap: 4px; }
.hrow { display: flex; gap: 10px; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--line-soft); }
.grow { flex: 1; }
</style>

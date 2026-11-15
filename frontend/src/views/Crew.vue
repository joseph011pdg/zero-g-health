<template>
  <div class="page">
    <section class="opening">
      <div class="lead">
        <h1 v-if="needAction.length"><span class="hl">{{ needAction.length }} de {{ s.crew.length }}</span> tripulantes requieren acción.</h1>
        <h1 v-else-if="watch.length">Sin acciones urgentes; <span class="hl">{{ watch.length }}</span> para vigilar.</h1>
        <h1 v-else>Toda la tripulación <span class="hl">dentro de lo habitual</span>.</h1>

        <div class="actions">
          <button class="ab main" @click="goAlarms"><span><Icon name="bell" :size="16" />Revisar alarmas</span><span class="k num">{{ highPending }}</span></button>
          <router-link class="ab" :to="`/persona/${s.selected}?accion=checkin`"><span><Icon name="smile" :size="16" />Check-in</span><span class="k">{{ short(selName) }}</span></router-link>
          <router-link class="ab" :to="`/persona/${s.selected}?accion=pvt`"><span><Icon name="target" :size="16" />Prueba PVT</span><span class="k">3 min</span></router-link>
          <router-link class="ab" to="/tierra"><span><Icon name="send" :size="16" />Enviar reporte</span><span class="k num">{{ s.pendingReports }} en cola</span></router-link>
        </div>

        <div class="byline">
          <span><Icon name="satellite" :size="14" />{{ link.apagon ? 'Sin enlace con la Tierra' : `Mensajes a la Tierra: ${fmt(link.retraso_min, 1)} min` }}</span>
          <span v-if="blackoutText"><Icon name="signalOff" :size="14" />{{ blackoutText }}</span>
          <span v-if="s.updatedAt"><Icon name="clock" :size="14" />Actualizado {{ hhmm(s.updatedAt) }}</span>
        </div>
      </div>

      <div class="hero-img">
        <!-- Video real de NASA ("ISS Fly-Through to Cupola"): la Tierra bajo la estación, en bucle suave.
             Foto fija si el sistema pide reducir movimiento. -->
        <video v-if="!reduceMotion" class="hero-video" :class="{ out: fadeOut }" src="/img/portada.mp4" poster="/img/portada-poster.jpg"
               autoplay muted playsinline preload="auto" @timeupdate="softLoop" aria-hidden="true"></video>
        <img v-else class="hero-video" src="/img/portada-poster.jpg" alt="" />
        <div class="txt">
          <h2>Monitoreo de salud de la tripulación</h2>
          <p>Cada astronauta comparado con su propia línea base. Alertas explicadas y seguimiento sin depender de la Tierra.</p>
          <div class="hbtns">
            <button class="hb p" @click="goAlarms">Revisar alarmas</button>
            <router-link class="hb" to="/tierra">Generar reporte</router-link>
          </div>
        </div>
      </div>
    </section>

    <MissionStrip />

    <section aria-labelledby="t-crew">
      <div class="sec-h"><h2 id="t-crew">Tripulación</h2><router-link class="go" :to="`/persona/${s.selected}`">Ver los seis indicadores →</router-link></div>
      <router-link v-for="(p, i) in rows" :key="p.a.id" :to="`/persona/${p.a.id}`" class="person" @click="s.select(p.a.id)">
        <div class="who">
          <b>{{ p.a.nombre }}</b><small>{{ p.a.rol }}</small>
          <LevelBadge :level="p.a.nivel" class="st" />
        </div>
        <div class="reading" :class="'n-' + p.a.nivel">
          <span class="v num">{{ fmt(p.v.valor, s.indicators[p.k].decimales) }}</span><span class="u">{{ s.indicators[p.k].unidad }}</span>
          <span class="d num">Su normal {{ fmt(p.v.linea_base, s.indicators[p.k].decimales) }}<template v-if="p.v.diferencia !== null"> · {{ signed(p.v.diferencia, s.indicators[p.k].decimales) }}</template></span>
        </div>
        <figure>
          <TrendChart v-if="series[p.a.id]" :data="series[p.a.id][p.k]" :unidad="s.indicators[p.k].unidad" :nombre="s.indicators[p.k].corto"
                      :decimales="s.indicators[p.k].decimales" :show-fixed="false" :height="74" compact />
          <div v-else class="skeleton" style="min-height: 74px" />
          <figcaption><b>Fig. {{ i + 1 }}</b> {{ s.indicators[p.k].corto }} · 14 días</figcaption>
        </figure>
      </router-link>
    </section>

    <section class="two">
      <div id="alarmas">
        <div class="sec-h"><h2>Alarmas</h2></div>
        <div v-if="loading" class="skeleton" style="min-height: 80px" />
        <p v-else-if="!high.length && !low.length" class="empty"><Icon name="check" :size="15" class="c-verde" /> Sin alarmas en los últimos 7 días.</p>
        <template v-else>
          <div v-for="g in high" :key="g.key" class="find" :class="{ done: g.rep.estado !== 'pendiente' }">
            <div class="ftxt">
              <h3><span class="pr">ALTA</span>{{ short(crewName(g.rep.astro_id)) }}: {{ g.rep.titulo }}</h3>
              <span class="meta" :class="metaClass(g)">{{ statusText(g) }}</span>
            </div>
            <div v-if="s.isOfficer" class="facts">
              <template v-if="g.rep.estado === 'pendiente'">
                <button class="act-p" @click="act(g.rep, 'reconocida')"><Icon name="check" :size="14" />Reconocer</button>
                <button class="act-l" @click="act(g.rep, 'pospuesta')">Posponer 24 h</button>
              </template>
              <router-link v-else class="act-l" :to="`/persona/${g.rep.astro_id}`">Ver ficha</router-link>
            </div>
          </div>
          <div v-if="low.length" class="watchrow">
            <button class="act-l" @click="showLow = !showLow" :aria-expanded="showLow">{{ lowPending }} avisos para vigilar {{ showLow ? '↑' : '→' }}</button>
          </div>
          <div v-if="showLow" class="lowlist">
            <router-link v-for="g in low" :key="g.key" :to="`/persona/${g.rep.astro_id}`" class="lowitem">
              <span class="pw">VIGILAR</span><span>{{ short(crewName(g.rep.astro_id)) }}: {{ g.rep.titulo }}</span><span class="muted small">{{ STATE_LABEL[g.rep.estado] }}</span>
            </router-link>
          </div>
        </template>
      </div>
      <div>
        <div class="sec-h"><h2>Enlace con la Tierra</h2><router-link class="go" to="/tierra">Reportes →</router-link></div>
        <table class="kv">
          <tbody>
            <tr><th scope="row">Retraso por mensaje</th><td class="num">{{ link.apagon ? 'sin enlace' : `${fmt(link.retraso_min, 1)} min` }}</td></tr>
            <tr><th scope="row">{{ link.apagon ? 'Enlace vuelve' : 'Próximo apagón' }}</th><td class="num">{{ blackoutCell }}</td></tr>
            <tr><th scope="row">Reportes en cola</th><td class="num">{{ s.pendingReports }}</td></tr>
            <tr><th scope="row">Último envío</th><td class="num">{{ lastSent }}</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <footer class="colophon"><span>Datos simulados · prototipo educativo, no es un dispositivo médico</span><span>Funciona a bordo, sin conexión</span></footer>
  </div>
</template>

<script setup>
import { ref, computed, watch as vwatch } from 'vue'
import { useRouter } from 'vue-router'
import { api, useStore, fmt, signed, STATE_LABEL, RANK_LEVEL } from '../store.js'
import Icon from '../components/Icon.vue'
import LevelBadge from '../components/LevelBadge.vue'
import TrendChart from '../components/TrendChart.vue'
import MissionStrip from '../components/MissionStrip.vue'

const s = useStore()
const router = useRouter()
const alerts = ref([])
const reports = ref([])
const series = ref({})
const loading = ref(true)
const showLow = ref(false)
// Bucle suave: fundido corto al final y vuelta al inicio (el plano de cámara no coincide entre fin e inicio)
const fadeOut = ref(false)
function softLoop(e) {
  const v = e.target
  if (fadeOut.value || !v.duration) return
  if (v.currentTime >= v.duration - 0.6) {
    fadeOut.value = true
    setTimeout(() => { v.currentTime = 0; v.play(); fadeOut.value = false }, 500)
  }
}
const reduceMotion = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

async function load() {
  try {
    const [al, rep] = await Promise.all([api('/alerts?todas=true'), api('/reports')])
    alerts.value = al
    reports.value = rep
  } finally { loading.value = false }
  const out = {}
  await Promise.all(s.crew.map(async (a) => {
    const d = await api(`/astronauts/${a.id}?desde=${Math.max(0, s.day - 13)}`)
    out[a.id] = d.series
  }))
  series.value = out
}
vwatch(() => [s.day, s.tick], load, { immediate: true })

const link = computed(() => s.mission.comunicacion)
const needAction = computed(() => s.crew.filter((a) => a.nivel === 'rojo'))
const watch = computed(() => s.crew.filter((a) => a.nivel === 'amarillo'))
const selName = computed(() => s.crew.find((a) => a.id === s.selected)?.nombre || '')

// Indicador más alejado de su normal por persona; las personas en "actuar" primero
const rows = computed(() => s.crew.map((a) => {
  let best = null
  for (const [k, v] of Object.entries(a.indicadores)) {
    const score = [RANK_LEVEL[v.nivel] ?? -1, v.z ?? -99]
    if (!best || score[0] > best.score[0] || (score[0] === best.score[0] && score[1] > best.score[1])) best = { k, v, score }
  }
  return { a, k: best.k, v: best.v }
}).sort((x, y) => (RANK_LEVEL[y.a.nivel] ?? -1) - (RANK_LEVEL[x.a.nivel] ?? -1)))

const blackoutText = computed(() => {
  const [a, b] = s.mission.apagon
  if (a === null || a === undefined) return ''
  if (link.value.apagon) return `Enlace vuelve en ${b - s.day + 1} días`
  if (s.day < a) return `Apagón en ${a - s.day} días`
  return ''
})
const blackoutCell = computed(() => {
  const [a, b] = s.mission.apagon
  if (a === null || a === undefined) return '—'
  if (link.value.apagon) return `día ${b + 1} · en ${b - s.day + 1} días`
  if (s.day < a) return `día ${a} · en ${a - s.day} días`
  return 'superado'
})
const lastSent = computed(() => {
  const d = reports.value.map((r) => r.dia_envio).filter((x) => x !== null && x !== undefined)
  return d.length ? `día ${Math.max(...d)}` : '—'
})

// Episodios de alarma: misma persona, tipo y nivel; se muestra el más reciente
const groups = computed(() => {
  const map = new Map()
  for (const a of alerts.value) {
    if (a.day <= s.day - 7) continue
    const key = `${a.astro_id}|${a.episodio}|${a.nivel}`
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(a)
  }
  const out = []
  for (const [key, list] of map) {
    list.sort((x, y) => y.day - x.day)
    let first = list[0].day
    for (const x of list.slice(1)) { if (x.day === first - 1) first = x.day; else break }
    out.push({ key, rep: list[0], since: first })
  }
  const order = (g) => (g.rep.estado === 'pendiente' ? 0 : 1)
  return out.sort((a, b) => order(a) - order(b) || b.rep.day - a.rep.day)
})
const high = computed(() => groups.value.filter((g) => g.rep.nivel === 'rojo'))
const low = computed(() => groups.value.filter((g) => g.rep.nivel === 'amarillo'))
const highPending = computed(() => high.value.filter((g) => g.rep.estado === 'pendiente').length)
const lowPending = computed(() => low.value.filter((g) => g.rep.estado === 'pendiente').length)

function statusText(g) {
  const a = g.rep
  if (a.estado === 'pendiente') {
    const d = s.day - g.since
    return d >= 2 ? `${d} días sin reconocer · escalar` : `Sin reconocer desde el día ${g.since}`
  }
  if (a.estado === 'pospuesta') return `Pospuesta hasta el día ${a.revisado_dia + 1}`
  return `${STATE_LABEL[a.estado]}${a.revisor ? ` por ${a.revisor}` : ''}${a.revisado_dia != null ? ` · día ${a.revisado_dia}` : ''}`
}
const metaClass = (g) => (g.rep.estado === 'pendiente' ? 'pend' : g.rep.estado === 'pospuesta' ? 'muted' : 'ok')
async function act(a, estado) {
  await s.run(() => api(`/alerts/${encodeURIComponent(a.id)}`, { method: 'PATCH', body: { estado, revisor: s.officer ? s.officer.nombre : 'Oficial médico' } }),
    estado === 'reconocida' ? 'Alarma reconocida' : 'Alarma pospuesta 24 h')
  await load()
  await s.refresh()
}
function goAlarms() {
  if (!s.isOfficer) s.setRole('oficial')
  router.push({ path: '/', hash: '#alarmas' })
  document.getElementById('alarmas')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
const crewName = (id) => s.crew.find((a) => a.id === id)?.nombre || id
const short = (n) => (n || '').replace(/^[^ ]+\. /, '').split(' ').slice(-1)[0]
const hhmm = (d) => d.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' })
</script>

<style scoped>
.page { gap: 34px; }
.opening { display: grid; grid-template-columns: minmax(0, 5fr) minmax(0, 7fr); gap: 40px; padding-top: 6px; }
.lead { display: grid; gap: 18px; align-content: center; }
.lead h1 { font-size: 3.1rem; line-height: 1.05; letter-spacing: -0.025em; text-wrap: balance; }
.lead h1 .hl { color: var(--blue); }
.byline { display: flex; gap: 18px; flex-wrap: wrap; font-size: 0.82rem; color: var(--muted); }
.byline span { display: inline-flex; align-items: center; gap: 6px; }
.hero-img { position: relative; overflow: hidden; min-height: 340px; border-radius: 18px; background: #0b1626; }
.hero-video { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; display: block; transition: opacity .5s ease; }
.hero-video.out { opacity: 0.15; }
.hero-img .txt { position: absolute; inset: 0; padding: 30px; display: grid; align-content: center; gap: 14px; max-width: 56%;
  background: linear-gradient(90deg, rgba(6, 16, 32, .88) 0%, rgba(6, 16, 32, .65) 70%, rgba(6, 16, 32, 0) 100%); color: #fff; }
.hero-img h2 { font-family: var(--sans); font-size: 1.9rem; line-height: 1.15; letter-spacing: -0.02em; }
.hero-img p { color: #d5e2f3; }
.hbtns { display: flex; gap: 10px; flex-wrap: wrap; }
.hb { border-radius: 10px; padding: 9px 16px; font-weight: 600; font-size: 0.86rem; border: 1px solid #fff; color: #fff; background: transparent; cursor: pointer; }
.hb.p { background: #fff; color: var(--blue); }
.hb:hover { background: rgba(255, 255, 255, .14); }
.hb.p:hover { background: #e8eef8; }

.person { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1.3fr) minmax(0, 4.5fr); gap: 24px; align-items: center; padding: 18px 0; border-bottom: 1px solid var(--line-soft); color: var(--ink); }
.person:hover { background: linear-gradient(90deg, var(--blue-soft), transparent 60%); }
.who b { font-family: var(--serif); font-size: 1.4rem; font-weight: 600; letter-spacing: -0.01em; display: block; }
.who small { display: block; color: var(--muted); font-size: 0.86rem; }
.who .st { margin-top: 8px; }
.reading .v { font-size: 2.9rem; font-weight: 500; letter-spacing: -0.03em; line-height: 1; color: var(--blue); }
.reading.n-rojo .v { color: var(--red); }
.reading.n-amarillo .v { color: var(--warn); }
.reading .u { font-size: 0.92rem; color: var(--muted); margin-left: 4px; }
.reading .d { display: block; font-size: 0.82rem; color: var(--text-2); margin-top: 6px; }
figure { margin: 0; }

.two { display: grid; grid-template-columns: minmax(0, 7fr) minmax(0, 5fr); gap: 40px; }
.find { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 16px; align-items: center; padding: 16px 0; border-bottom: 1px solid var(--line-soft); }
.find h3 { font-size: 1.2rem; }
.find.done h3 { color: var(--text-2); }
.pr { font-family: var(--sans); font-size: 0.7rem; font-weight: 600; color: var(--red); background: var(--red-soft); padding: 3px 7px; margin-right: 10px; vertical-align: 3px; }
.pw { font-size: 0.7rem; font-weight: 600; color: var(--warn); background: var(--warn-soft); padding: 3px 7px; flex: none; }
.meta { display: block; margin-top: 4px; font-size: 0.82rem; font-weight: 500; }
.meta.pend { color: var(--red); }
.meta.ok { color: var(--ok); }
.facts { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
.act-p { background: var(--blue); color: #fff; border: 0; padding: 9px 14px; font-weight: 600; font-size: 0.84rem; cursor: pointer; display: inline-flex; gap: 8px; align-items: center; border-radius: 2px; }
.act-p:hover { background: #0a3480; }
.act-l { background: none; border: 0; color: var(--blue); font-weight: 600; font-size: 0.84rem; cursor: pointer; padding: 4px 0; text-decoration: underline; text-underline-offset: 3px; }
.watchrow { padding: 14px 0; }
.lowlist { display: grid; }
.lowitem { display: flex; gap: 12px; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--line-soft); font-size: 0.92rem; color: var(--ink); }
.lowitem > span:nth-child(2) { flex: 1; }
.empty { padding: 16px 0; color: var(--text-2); display: flex; gap: 8px; align-items: center; }
.kv { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
.kv th, .kv td { padding: 12px 0; border-bottom: 1px solid var(--line-soft); }
.kv th { text-align: left; font-weight: 500; color: var(--text-2); }
.kv td { text-align: right; font-weight: 600; }
.colophon { border-top: 1px solid var(--ink); padding-top: 12px; font-size: 0.8rem; color: var(--muted); display: flex; justify-content: space-between; gap: 20px; flex-wrap: wrap; }

@media (max-width: 1000px) {
  .opening, .two { grid-template-columns: 1fr; }
  .lead h1 { font-size: 2.4rem; }
}
@media (max-width: 640px) {
  .person { grid-template-columns: 1fr 1fr; gap: 12px; }
  .person figure { grid-column: 1 / -1; }
  .reading .v { font-size: 2.2rem; }
  .hero-img .txt { max-width: 100%; padding: 22px; }
  .hero-img h2 { font-size: 1.5rem; }
  .actions { grid-template-columns: 1fr; }
  .ab:nth-child(odd) { border-right: 0; padding-right: 4px; }
  .ab:nth-child(even) { padding-left: 4px; }
}
</style>

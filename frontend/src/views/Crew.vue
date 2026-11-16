<template>
  <div class="page">
    <section class="opening rise">
      <div class="lead">
        <h1 v-if="highPending"><span class="hl">{{ highPending === 1 ? '1 alert needs' : `${highPending} alerts need` }}</span> attention.</h1>
        <h1 v-else-if="lowPending">No urgent alerts; <span class="hl">{{ plural(lowPending, 'notice', 'notices') }}</span> to watch.</h1>
        <h1 v-else-if="needAction.length || watch.length">Alerts up to date; <span class="hl">{{ needAction.length + watch.length }} of {{ s.crew.length }}</span> being followed.</h1>
        <h1 v-else>The whole crew is <span class="hl">within their usual range</span>.</h1>

        <p class="tagline">Each astronaut is compared with <b>their own baseline</b>, on board and without Earth.
          <button class="what" @click="showPitch = !showPitch" :aria-expanded="showPitch">What is Zero G Health? {{ showPitch ? '↑' : '↓' }}</button>
          <i>simulated data</i></p>
        <dl v-if="showPitch" class="pitch">
          <div><dt>Problem</dt><dd>On the way to Mars a message takes up to 20 min each way and there are blackouts: Earth cannot watch crew health in real time.</dd></div>
          <div><dt>Solution</dt><dd>Zero G Health compares each astronaut with their own baseline and alerts on board, without Internet, with an explanation and a safe follow-up.</dd></div>
          <div><dt>Evidence</dt><dd>In simulation it detects <b>98.9%</b> of events with <b>0.78</b> false alarms per 30 astronaut-days (fixed threshold: 88.9% and 1.87). <router-link to="/lab/validation">See validation</router-link></dd></div>
        </dl>

        <div class="byline">
          <span><Icon name="satellite" :size="14" />{{ link.apagon ? 'No link with Earth' : `Messages to Earth: ${fmt(link.retraso_min, 1)} min` }}</span>
          <span v-if="blackoutText"><Icon name="signalOff" :size="14" />{{ blackoutText }}</span>
          <span v-if="s.updatedAt"><Icon name="clock" :size="14" />Updated {{ hhmm(s.updatedAt) }}</span>
        </div>
      </div>

      <div class="hero-img">
        <!-- Video real de NASA ("Aurora Borealis from Space (4K)"): auroras vistas desde la ISS, en bucle suave.
             Foto fija si el sistema pide reducir movimiento. -->
        <video v-if="!reduceMotion" class="hero-video" :class="{ out: fadeOut }" src="/img/portada.mp4" poster="/img/portada-poster.jpg"
               autoplay muted playsinline preload="auto" @timeupdate="softLoop" aria-hidden="true"></video>
        <img v-else class="hero-video" src="/img/portada-poster.jpg" alt="" />
        <div class="txt">
          <h2>Crew health monitoring</h2>
          <p>Explained alerts and follow-up without depending on Earth.</p>
        </div>
      </div>
    </section>

    <section aria-labelledby="t-crew">
      <div class="sec-h"><h2 id="t-crew">Crew</h2><span class="dotkey">dots: heart rate, HRV, sleep, radiation, attention, mood</span></div>
      <router-link v-for="(p, i) in rows" :key="p.a.id" :to="`/crew/${p.a.id}`" class="person rise" :style="{ '--i': i }" @click="s.select(p.a.id)">
        <div class="who">
          <b>{{ p.a.nombre }}</b><small>{{ p.a.rol }}</small>
          <span class="dots" aria-label="Six indicators">
            <i v-for="(v, k) in p.a.indicadores" :key="k" :class="'d-' + v.nivel" :title="`${s.indicators[k].corto}: ${LEVEL[v.nivel].label}`"></i>
          </span>
          <span v-if="openOf(p.a.id)" class="openep">{{ openOf(p.a.id) }}</span>
        </div>
        <div class="reading" :class="'n-' + p.a.nivel">
          <span class="say"><LevelBadge :level="p.a.nivel" />{{ sayOf(p) }}</span>
          <span class="v num">{{ fmt(p.v.valor, s.indicators[p.k].decimales) }}</span> <span class="u">{{ s.indicators[p.k].unidad }}</span>
          <span class="d num">Their usual {{ fmt(p.v.linea_base, s.indicators[p.k].decimales) }}<template v-if="p.v.diferencia !== null">, {{ signed(p.v.diferencia, s.indicators[p.k].decimales) }}</template></span>
        </div>
        <figure>
          <TrendChart v-if="series[p.a.id]" :data="series[p.a.id][p.k]" :unidad="s.indicators[p.k].unidad" :nombre="s.indicators[p.k].corto"
                      :decimales="s.indicators[p.k].decimales" :show-fixed="false" :height="74" compact />
          <div v-else class="skeleton" style="min-height: 74px" />
          <figcaption><b>Fig. {{ i + 1 }}</b> {{ s.indicators[p.k].corto }}, 14 days</figcaption>
        </figure>
      </router-link>
    </section>

    <section class="do">
      <div>
        <div class="sec-h"><h2>Actions</h2></div>
        <div class="actions">
          <button class="ab main" @click="goAlarms"><span><Icon name="bell" :size="16" />Review alerts</span><span class="k num">{{ highPending }}</span></button>
          <router-link class="ab" :to="`/crew/${s.selected}?action=checkin`"><span><Icon name="smile" :size="16" />Check-in</span><span class="k">{{ short(selName) }}</span></router-link>
          <router-link class="ab" :to="`/crew/${s.selected}?action=pvt`"><span><Icon name="target" :size="16" />PVT test</span><span class="k">3 min</span></router-link>
          <router-link class="ab" to="/reports"><span><Icon name="send" :size="16" />Send report</span><span class="k num">{{ s.pendingReports }} queued</span></router-link>
        </div>
      </div>
      <div>
        <div class="sec-h"><h2>Try the demo</h2></div>
        <div class="tryit" role="group" aria-label="Try the demo">
          <button class="tb main" @click="s.demo = true"><b><Icon name="compass" :size="15" />Guided demo</b><small>9 steps, about 3 minutes</small></button>
          <button class="tb" :aria-pressed="s.apagon" @click="toggleApagon">
            <b><Icon :name="s.apagon ? 'satellite' : 'signalOff'" :size="15" />{{ s.apagon ? 'Restore link' : 'Simulate blackout' }}</b><small>lose the link with Earth</small></button>
          <button v-for="sc in SCEN" :key="sc.k" class="tb" @click="goScen(sc)"><b>{{ sc.l }}</b><small>{{ sc.d }}</small></button>
        </div>
      </div>
    </section>

    <MissionStrip />

    <section class="two">
      <div id="alerts">
        <div class="sec-h"><h2>Alerts</h2></div>
        <p class="legend"><span class="pr">ACT</span> notify the Medical Officer <span class="pw">WATCH</span> repeat the measurement</p>
        <div v-if="loading" class="skeleton" style="min-height: 80px" />
        <p v-else-if="!high.length && !low.length" class="empty"><Icon name="check" :size="15" class="c-verde" /> No alerts in the last 7 days.</p>
        <template v-else>
          <div v-for="(g, gi) in high" :key="g.key" class="find rise" :style="{ '--i': gi }" :class="{ done: g.rep.estado !== 'pendiente' }">
            <div class="ftxt">
              <h3><span class="pr">ACT</span>{{ short(crewName(g.rep.astro_id)) }}: {{ g.rep.titulo }}</h3>
              <span class="fact">{{ factText(g.rep) }}</span>
              <span class="meta" :class="metaClass(g)">{{ statusText(g) }}</span>
            </div>
            <div v-if="s.isOfficer" class="facts">
              <template v-if="g.rep.estado === 'pendiente'">
                <button class="act-p" @click="act(g.rep, 'reconocida')"><Icon name="check" :size="14" />Acknowledge</button>
                <button class="act-l" @click="act(g.rep, 'pospuesta')">Snooze 24 h</button>
              </template>
              <router-link v-else class="act-l" :to="`/crew/${g.rep.astro_id}`">View profile</router-link>
            </div>
          </div>
          <div v-if="low.length" class="lowlist">
            <router-link v-for="g in lowShown" :key="g.key" :to="`/crew/${g.rep.astro_id}`" class="lowitem">
              <span class="pw">WATCH</span><span>{{ short(crewName(g.rep.astro_id)) }}: {{ g.rep.titulo }}</span><span class="muted small">{{ factText(g.rep) }}, {{ STATE_LABEL[g.rep.estado] }}</span>
            </router-link>
          </div>
          <div v-if="lowSorted.length > LOW_TOP" class="watchrow">
            <button class="act-l" @click="showLow = !showLow" :aria-expanded="showLow">{{ showLow ? 'Show fewer' : plural(lowSorted.length - LOW_TOP, 'more notice', 'more notices') }} {{ showLow ? '↑' : '→' }}</button>
          </div>
        </template>
      </div>
      <div>
        <div class="sec-h"><h2>Link with Earth</h2><router-link class="go" to="/reports">Reports →</router-link></div>
        <table class="kv">
          <tbody>
            <tr><th scope="row">Delay per message</th><td class="num">{{ link.apagon ? 'no link' : `${fmt(link.retraso_min, 1)} min` }}</td></tr>
            <tr><th scope="row">{{ link.apagon ? 'Link returns' : 'Next blackout' }}</th><td class="num">{{ blackoutCell }}</td></tr>
            <tr><th scope="row">Reports queued</th><td class="num">{{ s.pendingReports }}</td></tr>
            <tr><th scope="row">Last sent</th><td class="num">{{ lastSent }}</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <footer class="colophon"><span>Simulated data. Educational prototype, not a medical device</span><span>Runs on board with no Internet (local version), <router-link to="/about">About Zero G Health</router-link></span></footer>
  </div>
</template>

<script setup>
import { ref, computed, watch as vwatch } from 'vue'
import { useRouter } from 'vue-router'
import { api, useStore, fmt, signed, plural, episodes, STATE_LABEL, RANK_LEVEL, LEVEL, LOCALE } from '../store.js'
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
const showPitch = ref(false)
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
  if (link.value.simulado) return 'Simulated blackout: reports wait in the queue'
  if (link.value.apagon) return `Link returns in ${plural(b - s.day + 1, 'day', 'days')}`
  if (s.day < a) return `Blackout in ${plural(a - s.day, 'day', 'days')}`
  return ''
})
const blackoutCell = computed(() => {
  const [a, b] = s.mission.apagon
  if (a === null || a === undefined) return 'n/a'
  if (link.value.simulado) return 'when the simulated blackout is turned off'
  if (link.value.apagon) return `day ${b + 1}, in ${plural(b - s.day + 1, 'day', 'days')}`
  if (s.day < a) return `day ${a}, in ${plural(a - s.day, 'day', 'days')}`
  return 'passed'
})
const lastSent = computed(() => {
  const d = reports.value.map((r) => r.dia_envio).filter((x) => x !== null && x !== undefined)
  return d.length ? `day ${Math.max(...d)}` : 'n/a'
})

// Episodios de alarma (misma persona, tipo y nivel en días consecutivos); en la demo pública
// se aplican los reconocimientos guardados en este navegador
const groups = computed(() => episodes(s.withAcks(alerts.value), s.day))
const high = computed(() => groups.value.filter((g) => g.rep.nivel === 'rojo'))
const low = computed(() => groups.value.filter((g) => g.rep.nivel === 'amarillo'))
const highPending = computed(() => high.value.filter((g) => g.rep.estado === 'pendiente').length)
const lowPending = computed(() => low.value.filter((g) => g.rep.estado === 'pendiente').length)
//AVISOS: pendientes y de mayor z primero; el resto se agrupa
const LOW_TOP = 2
const maxZ = (a) => Math.max(...(a.cuanto || []).map((c) => Math.abs(c.z ?? 0)), 0)
const lowSorted = computed(() => [...low.value].sort((x, y) => (x.rep.estado === 'pendiente' ? 0 : 1) - (y.rep.estado === 'pendiente' ? 0 : 1) || maxZ(y.rep) - maxZ(x.rep)))
const lowShown = computed(() => (showLow.value ? lowSorted.value : lowSorted.value.slice(0, LOW_TOP)))

function statusText(g) {
  const a = g.rep
  if (a.estado === 'pendiente') {
    const d = s.day - g.since
    return d >= 2 ? `${d} days unacknowledged, escalate` : `Unacknowledged since day ${g.since}`
  }
  if (a.estado === 'pospuesta') return `Snoozed until day ${a.revisado_dia + 1}`
  return `${STATE_LABEL[a.estado]}${a.revisor ? ` by ${a.revisor}` : ''}${a.revisado_dia != null ? `, day ${a.revisado_dia}` : ''}`
}
const metaClass = (g) => (g.rep.estado === 'pendiente' ? 'pend' : g.rep.estado === 'pospuesta' ? 'muted' : 'ok')
async function act(a, estado) {
  const nota = estado === 'reconocida' ? window.prompt('Note for the log (optional):', '') : null
  if (nota === null && estado === 'reconocida') return // cancelado
  await s.run(() => s.review(a, estado, nota),
    `${estado === 'reconocida' ? 'Alert acknowledged' : 'Alert snoozed 24 h'}${s.publico ? ' (only in this browser)' : ''}`)
  if (!s.publico) await load()
}
// Qué indicador y cuánto: "Lapsos PVT: 5 lapsos frente a su normal de 1 (z = 4,8)"
function factText(a) {
  return (a.cuanto || []).map((c) => {
    const d = s.indicators[c.indicador]?.decimales ?? 1
    return `${s.indicators[c.indicador]?.corto || c.nombre}: ${fmt(c.valor, d)} ${c.unidad} vs. their usual ${fmt(c.linea_base, d)} (z = ${fmt(c.z, 1)})`
  }).join('; ')
}
// Episodio de alarma abierto aunque hoy los valores hayan vuelto a su normal
function openOf(id) {
  const g = groups.value.find((x) => x.astro_id === id && x.rep.estado === 'pendiente' && x.rep.nivel === 'rojo' && x.rep.day < s.day)
  if (!g) return ''
  const a = s.crew.find((x) => x.id === id)
  return `${a?.nivel === 'verde' ? 'Today: normal. ' : ''}Alert from day ${g.rep.day} still open (unacknowledged for ${plural(s.day - g.rep.day, 'day', 'days')})`
}
//ESTADO en una frase por tripulante
function sayOf(p) {
  if (p.a.alerta_principal) return p.a.alerta_principal
  if (p.a.nivel === 'verde') return 'All six indicators within their usual range'
  return `${s.indicators[p.k].corto}: ${LEVEL[p.v.nivel]?.label || ''}`
}
const SCEN = [
  { k: 'B', l: 'See fatigue (B)', d: 'day 54, Cmdr. Rivera', day: 54, id: 'A1' },
  { k: 'C', l: 'See stress (C)', d: 'day 72, Eng. Lindqvist', day: 72, id: 'A3' },
  { k: 'D', l: 'See solar event (D)', d: 'day 87, whole crew', day: 87, id: null }
]
async function goScen(sc) {
  await s.run(() => s.setDay(sc.day))
  if (sc.id) { s.select(sc.id); router.push(`/crew/${sc.id}`) }
}
function toggleApagon() {
  const on = !s.apagon
  s.run(() => s.setApagon(on), on ? 'Simulated blackout: data and alerts keep working; reports stay queued' : 'Link restored')
}
function goAlarms() {
  if (!s.isOfficer) s.setRole('oficial')
  router.push({ path: '/', hash: '#alerts' })
  document.getElementById('alerts')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
const crewName = (id) => s.crew.find((a) => a.id === id)?.nombre || id
const short = (n) => (n || '').replace(/^[^ ]+\. /, '').split(' ').slice(-1)[0]
const hhmm = (d) => d.toLocaleTimeString(LOCALE, { hour: '2-digit', minute: '2-digit' })
</script>

<style scoped>
.page { gap: 34px; }
.opening { display: grid; grid-template-columns: minmax(0, 11fr) minmax(0, 14fr); gap: 40px; padding-top: 6px; }
.lead { display: grid; gap: 14px; align-content: center; }
.tagline { margin: 0; font-size: 1rem; color: var(--text-2); line-height: 1.5; }
.tagline b { color: var(--ink); font-weight: 600; }
.tagline i { color: var(--muted); font-size: 0.86rem; }
.what { background: none; border: 0; padding: 0 4px; font: inherit; color: var(--blue); font-weight: 600; text-decoration: underline; text-underline-offset: 3px; cursor: pointer; }
.lead h1 { font-size: 3.1rem; line-height: 1.05; letter-spacing: -0.025em; text-wrap: balance; }
.lead h1 .hl { color: var(--blue); }
.byline { display: flex; gap: 18px; flex-wrap: wrap; font-size: 0.82rem; color: var(--muted); }
.byline span { display: inline-flex; align-items: center; gap: 6px; }
.hero-img { position: relative; overflow: hidden; min-height: 300px; align-self: stretch; border-radius: 18px; background: #0b1626; }
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

.person { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(0, 2.4fr) minmax(0, 3.6fr); gap: 24px; align-items: center; padding: 18px 0; border-bottom: 1px solid var(--line-soft); color: var(--ink); }
.person:hover { background: linear-gradient(90deg, var(--blue-soft), transparent 60%); }
.who b { font-family: var(--serif); font-size: 1.4rem; font-weight: 600; letter-spacing: -0.01em; display: block; }
.who small { display: block; color: var(--muted); font-size: 0.86rem; }
.who .st { margin-top: 8px; }
.reading .v { font-size: 1.9rem; font-weight: 600; letter-spacing: -0.03em; line-height: 1;
  background: linear-gradient(90deg, #0a1f44, #1f6fe0); -webkit-background-clip: text; background-clip: text; color: transparent; }
.reading.n-rojo .v { background-image: linear-gradient(90deg, #8a3f00, #f07a1a); }
.reading.n-amarillo .v { background-image: linear-gradient(90deg, #7a5600, #e0a400); }
.reading .u { font-size: 0.92rem; color: var(--muted); margin-left: 1px; }
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
.pitch { margin: 0; display: grid; gap: 8px; border-left: 2px solid var(--blue); padding-left: 14px; }
.pitch div { display: grid; grid-template-columns: 78px minmax(0, 1fr); gap: 10px; }
.pitch dt { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--blue); padding-top: 3px; }
.pitch dd { margin: 0; font-size: 0.9rem; color: var(--text-2); line-height: 1.45; }
.pitch dd b { color: var(--ink); }
.pitch i { color: var(--muted); }
.do { display: grid; grid-template-columns: minmax(0, 5fr) minmax(0, 7fr); gap: 40px; }
.dotkey { font-size: 0.78rem; color: #c9d8f2; margin-left: auto; }
.say { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: 0.98rem; font-weight: 600; color: var(--ink); margin-bottom: 8px; line-height: 1.3; }
.tryit { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 8px; padding-top: 12px; }
.tb { display: grid; gap: 2px; text-align: left; border: 1px solid var(--line); background: #fff; color: var(--ink); font: inherit; font-size: 0.84rem; font-weight: 500; padding: 8px 12px; border-radius: 2px; cursor: pointer; min-height: 40px; }
.tb b { display: inline-flex; align-items: center; gap: 7px; font-weight: 600; }
.tb small { font-size: 0.76rem; color: var(--muted); font-weight: 400; }
.tb.main small, .tb[aria-pressed="true"] small { color: #c9d8f2; }
.tb:hover { border-color: var(--blue); color: var(--blue); }
.tb.main { background: var(--blue); border-color: var(--blue); color: #fff; font-weight: 600; }
.tb.main:hover { background: #0a3480; color: #fff; }
.tb[aria-pressed="true"] { background: var(--navy); border-color: var(--navy); color: #fff; }
.dots { display: flex; gap: 5px; margin-top: 8px; }
.dots i { width: 9px; height: 9px; border-radius: 50%; background: var(--ok); }
.dots i.d-amarillo { background: var(--warn); }
.dots i.d-rojo { background: var(--red); }
.dots i.d-sin_dato, .dots i.d-calibrando { background: transparent; border: 1.5px solid var(--muted); }
.openep { display: block; margin-top: 6px; font-size: 0.78rem; font-weight: 600; color: var(--red); line-height: 1.35; }
.fact { display: block; margin-top: 4px; font-size: 0.84rem; color: var(--text-2); }
.legend { font-size: 0.8rem; color: var(--text-2); margin: 0 0 4px; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.legend .pr { margin-right: 0; vertical-align: 0; }
.colophon { border-top: 1px solid var(--ink); padding-top: 12px; font-size: 0.8rem; color: var(--muted); display: flex; justify-content: space-between; gap: 20px; flex-wrap: wrap; }

@media (max-width: 1000px) {
  .opening, .two, .do { grid-template-columns: 1fr; }
  .do { gap: 24px; }
  .lead h1 { font-size: 2.4rem; }
}
@media (max-width: 640px) {
  .pitch div { grid-template-columns: 1fr; gap: 2px; }
  .person { grid-template-columns: 1fr; gap: 8px; }
  .who { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 10px; }
  .who .dots { margin-top: 0; }
  .who .openep { flex-basis: 100%; }
  .hero-img { min-height: 190px; }
  .hero-img p { display: none; }
  .person figure { grid-column: 1 / -1; }
  .reading .v { font-size: 1.5rem; }
  .dotkey { display: none; }
  .hero-img .txt { max-width: 100%; padding: 22px; }
  .hero-img h2 { font-size: 1.5rem; }
  .actions { grid-template-columns: 1fr; }
  .ab:nth-child(odd) { border-right: 0; padding-right: 4px; }
  .ab:nth-child(even) { padding-left: 4px; }
}
</style>

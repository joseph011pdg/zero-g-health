<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="eyebrow">02 · Astronaut Health · Alerts &amp; Decisions</div>
        <div class="row wrap">
          <h1>{{ a?.nombre || '…' }}</h1>
          <LevelBadge v-if="a" :level="a.nivel" />
        </div>
        <p v-if="a">{{ a.rol }} · día {{ a.dia }} · índice de estabilidad {{ a.indice ?? '—' }}/100
          <span class="tag" v-if="a.ficticio">perfil ficticio</span></p>
      </div>
      <div class="row wrap no-print">
        <div class="tabs" role="tablist" aria-label="Astronauta">
          <button v-for="c in s.crew" :key="c.id" :class="{ on: c.id === id }" @click="go(c.id)">
            <Icon :name="LEVEL[c.nivel].icon" :size="13" :class="'c-' + c.nivel" />{{ c.id }}
          </button>
        </div>
        <button v-if="!s.publico" class="btn sm" @click="showProfile = !showProfile"><Icon name="user" :size="14" /> Nuevo perfil</button>
      </div>
    </div>

    <form v-if="showProfile" class="panel grid newp no-print" @submit.prevent="createProfile">
      <h2>Nuevo astronauta (F1)</h2>
      <div class="cols-4">
        <label class="field"><span>Identificador</span><input class="input" v-model="np.id" required pattern="[A-Za-z0-9_-]{2,8}" placeholder="A5" /></label>
        <label class="field"><span>Nombre ficticio</span><input class="input" v-model="np.nombre" required minlength="2" /></label>
        <label class="field"><span>Rol</span><input class="input" v-model="np.rol" required minlength="2" /></label>
        <label class="field"><span>Datos iniciales</span>
          <select class="input" v-model="np.generar_datos">
            <option value="ninguno">Ninguno (calibrará con datos reales/CSV)</option>
            <option value="A">Sintéticos · estable</option><option value="B">Sintéticos · fatiga (día 45)</option>
            <option value="C">Sintéticos · estrés (día 45)</option><option value="E">Sintéticos · conductual (día 45)</option>
          </select></label>
      </div>
      <div class="row"><button class="btn primary" type="submit">Crear perfil</button>
        <span class="tiny muted">Cada perfil tiene sus propios registros y su propia línea base. No use datos reales identificables.</span></div>
    </form>

    <div v-if="!a" class="skeleton" style="height: 400px" />
    <template v-else>
      <section class="layout">
        <div class="grid">
          <div class="panel-head"><h2><Icon name="triangle" /> Alertas de hoy</h2>
            <span class="tiny muted">qué cambió · cuánto · cómo · qué hacer · fuente</span></div>
          <div v-if="!a.alertas.length" class="panel ok-panel">
            <div class="row"><Icon name="check" :size="20" class="c-verde" /><strong>Sin alertas hoy.</strong></div>
            <p class="small muted">Los indicadores evaluados están dentro de su rango habitual o aún no hay datos suficientes
              (ver estado de cada uno). La ausencia de datos no se interpreta como normal.</p>
          </div>
          <AlertCard v-for="al in a.alertas" :key="al.id" :a="al" expanded @changed="load" />

          <div class="panel">
            <div class="panel-head"><h2><Icon name="clipboard" /> Historial de alertas</h2>
              <div class="tabs"><button :class="{ on: hf === 'rojo' }" @click="hf = 'rojo'">Rojas</button>
                <button :class="{ on: hf === 'todas' }" @click="hf = 'todas'">Todas</button></div></div>
            <div class="hist">
              <button v-for="h in hist" :key="h.id" class="hrow" @click="focus(h)">
                <LevelBadge :level="h.nivel" icon-only />
                <span class="mono tiny">D{{ h.day }}</span>
                <span class="small grow">{{ h.titulo }}</span>
                <span class="tiny muted">{{ STATE_LABEL[h.estado] }}</span>
              </button>
              <p v-if="!hist.length" class="small muted">Sin alertas registradas.</p>
            </div>
          </div>
        </div>

        <div class="grid">
          <div class="tiles">
            <button v-for="(v, k) in a.indicadores" :key="k" class="panel tile edge" :class="[v.nivel, { sel: ind === k }]"
                    @click="ind = k" :aria-pressed="ind === k">
              <div class="row between">
                <span class="row label"><Icon :name="IND_ICON[k]" :size="14" />{{ s.indicators[k].corto }}</span>
                <LevelBadge :level="v.nivel" />
              </div>
              <div class="row between end">
                <div class="val num">{{ fmt(v.valor, s.indicators[k].decimales) }}<small>{{ s.indicators[k].unidad }}</small></div>
                <Icon :name="trendIcon(k, v.tendencia_dia)" :size="18" :class="trendClass(k, v.tendencia_dia)" :title="'Tendencia 7 días'" />
              </div>
              <dl class="stats tiny">
                <div><dt>Mediana</dt><dd class="num">{{ fmt(v.linea_base, s.indicators[k].decimales) }}</dd></div>
                <div><dt>MAD×1,48</dt><dd class="num">{{ fmt(v.mad, 2) }}</dd></div>
                <div><dt>n · ventana</dt><dd class="num">{{ v.n_obs ?? '—' }} · {{ v.ventana }} d</dd></div>
                <div><dt>Diferencia</dt><dd class="num">{{ signed(v.diferencia, s.indicators[k].decimales) }}</dd></div>
                <div><dt>z robusto</dt><dd class="num strong" :class="'c-' + v.nivel">{{ fmt(v.z, 2) }}</dd></div>
                <div><dt>Datos 14 d</dt><dd class="num">{{ fmt(v.calidad_14d_pct, 0) }} %</dd></div>
              </dl>
              <div class="tiny muted ref">{{ v.referencia ? 'vs. ' + v.referencia : (v.nivel === 'sin_dato' ? 'Sin medición hoy' : 'Línea base en calibración') }}
                <span v-if="v.fuente" class="tag" :class="v.fuente === 'sintetico' ? 'synthetic' : 'manual'">{{ SRC_LABEL[v.fuente] }}</span></div>
            </button>
          </div>

          <div class="panel">
            <div class="panel-head">
              <h2><Icon :name="IND_ICON[ind]" /> {{ s.indicators[ind].nombre }} <span class="muted small">({{ s.indicators[ind].unidad }})</span></h2>
              <div class="row wrap no-print">
                <div class="tabs">
                  <button v-for="r in RANGES" :key="r.v" :class="{ on: range === r.v }" @click="range = r.v">{{ r.l }}</button>
                </div>
                <label class="row tiny"><input type="checkbox" v-model="showFixed" /> umbral fijo</label>
                <label class="row tiny" title="Muestra los eventos inyectados por el simulador (la 'verdad'); el astronauta no los conoce."><input type="checkbox" v-model="showTruth" /> eventos simulados</label>
              </div>
            </div>
            <TrendChart :data="chartData" :unidad="s.indicators[ind].unidad" :nombre="s.indicators[ind].corto"
                        :decimales="s.indicators[ind].decimales" :fijo="s.indicators[ind].umbral_fijo" :show-fixed="showFixed"
                        :events="showTruth ? truth.filter((e) => e.afecta.split(',').includes(ind)) : []" :height="300" />
            <p class="tiny muted">Línea continua: valor observado. Discontinua gris: línea base (mediana de días previos válidos).
              Ámbar: umbral personal "vigilar" (línea base ± {{ s.mission.parametros.yellow }}×MAD). Naranja punteada:
              umbral poblacional fijo (comparador). {{ s.indicators[ind].clinical }}</p>
          </div>

          <div class="cols-2">
            <div class="panel">
              <div class="panel-head"><h2><Icon name="radiation" /> Radiación acumulada</h2></div>
              <div class="kpi"><span class="v">{{ fmt(a.radiacion.acumulada_medida_mgy, 1) }}<small>mGy medidos</small></span></div>
              <div class="bar"><div :style="{ width: Math.min(a.radiacion.porcentaje_del_presupuesto, 150) / 1.5 + '%' }"
                   :class="{ over: a.radiacion.porcentaje_del_presupuesto > 110 }" /></div>
              <p class="small">{{ a.radiacion.porcentaje_del_presupuesto }} % del presupuesto del escenario
                ({{ a.radiacion.presupuesto_escenario_mgy }} mGy) · {{ a.radiacion.dias_sin_lectura }} día(s) sin lectura</p>
              <p class="tiny muted">{{ a.radiacion.supuesto }}</p>
            </div>
            <div class="panel">
              <div class="panel-head"><h2><Icon name="clipboard" /> Registros recientes</h2>
                <router-link class="btn sm" to="/registro">Registrar</router-link></div>
              <div class="tiny muted" v-if="!a.checkins.length && !a.pvt.length">Sin check-ins ni pruebas PVT en esta sesión.</div>
              <ul class="recent small">
                <li v-for="c in a.checkins.slice(0, 4)" :key="'c' + c.id">D{{ c.day }} · check-in: ánimo {{ c.animo }}/10, sueño percibido {{ c.calidad_sueno }}/5</li>
                <li v-for="p in a.pvt.slice(0, 4)" :key="'p' + p.id">D{{ p.day }} · PVT ({{ p.modo }}): {{ p.errores }} errores, RT mediana {{ p.rt_mediana ?? '—' }} ms
                  <span v-if="!p.valido" class="c-amarillo">· inválida</span></li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, useStore, fmt, signed, LEVEL, IND_ICON, SRC_LABEL, STATE_LABEL } from '../store.js'
import Icon from '../components/Icon.vue'
import LevelBadge from '../components/LevelBadge.vue'
import AlertCard from '../components/AlertCard.vue'
import TrendChart from '../components/TrendChart.vue'

const props = defineProps({ id: String })
const s = useStore()
const router = useRouter()
const a = ref(null)
const truth = ref([])
const ind = ref('rhr')
const range = ref(60)
const showFixed = ref(true)
const showTruth = ref(false)
const hf = ref('rojo')
const showProfile = ref(false)
const np = ref({ id: '', nombre: '', rol: '', generar_datos: 'ninguno' })
const RANGES = [{ v: 14, l: '14 d' }, { v: 30, l: '30 d' }, { v: 60, l: '60 d' }, { v: 999, l: 'Toda' }]

async function load() {
  try {
    a.value = await api(`/astronauts/${props.id}`)
    truth.value = await api(`/events?astro_id=${props.id}`)
    if (!a.value.indicadores[ind.value]) ind.value = 'rhr'
    const red = a.value.alertas.find((x) => x.nivel === 'rojo') || a.value.alertas[0]
    if (red && !watchKey.manual) ind.value = red.indicadores[0]
  } catch (e) {
    s.toast(e.message, 'err')
    if (String(e.message).includes('no encontrado')) router.replace('/salud/A1')
  }
}
const watchKey = { manual: false }
watch(() => [props.id, s.tick], () => { s.select(props.id); load() }, { immediate: true })
watch(ind, () => { watchKey.manual = true })
watch(() => props.id, () => { watchKey.manual = false })

const chartData = computed(() => (a.value ? a.value.series[ind.value].slice(-range.value) : []))
const hist = computed(() => (a.value ? a.value.historial_alertas.filter((h) => hf.value === 'todas' || h.nivel === 'rojo').slice(0, 25) : []))

function go(id) { router.push(`/salud/${id}`) }
async function focus(h) { ind.value = h.indicadores[0]; range.value = 999 }
function trendIcon(k, t) {
  if (t === null || t === undefined || Math.abs(t) < (s.indicators[k].min_spread / 7)) return 'trendFlat'
  return t > 0 ? 'trendUp' : 'trendDown'
}
function trendClass(k, t) {
  if (trendIcon(k, t) === 'trendFlat') return 'faint'
  return (t > 0) === (s.indicators[k].direction > 0) ? 'c-amarillo' : 'c-verde'
}
async function createProfile() {
  const r = await s.run(() => api('/astronauts', { method: 'POST', body: { ...np.value } }), 'Perfil creado')
  showProfile.value = false
  await s.refresh()
  router.push(`/salud/${r.id}`)
}
</script>

<style scoped>
.layout { display: grid; grid-template-columns: minmax(320px, 400px) minmax(0, 1fr); gap: 16px; align-items: start; }
.layout > * { min-width: 0; }
@media (max-width: 1050px) { .layout { grid-template-columns: 1fr; } }
.ok-panel { display: grid; gap: 6px; border-left: 3px solid var(--ok); }
.tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(215px, 100%), 1fr)); gap: 10px; }
.tile { text-align: left; cursor: pointer; display: grid; gap: 6px; padding: 12px 14px; color: var(--text); }
.tile.sel { outline: 2px solid var(--blue); outline-offset: -1px; }
.tile .label { gap: 6px; }
.end { align-items: flex-end; }
.val { font-size: 1.6rem; font-weight: 700; letter-spacing: -0.02em; }
.val small { font-size: 0.8rem; color: var(--muted); margin-left: 4px; font-weight: 500; }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px 8px; margin: 0; }
.stats dt { color: var(--faint); font-size: 0.66rem; }
.stats dd { margin: 0; color: var(--text-2); }
.ref { display: flex; justify-content: space-between; gap: 6px; align-items: center; }
.hist { display: grid; gap: 2px; max-height: 300px; overflow-y: auto; }
.hrow { display: flex; gap: 8px; align-items: center; background: transparent; border: 0; padding: 6px 4px; border-radius: 6px; cursor: pointer; text-align: left; color: var(--text); }
.hrow:hover { background: var(--surface-2); }
.grow { flex: 1; }
.bar { height: 8px; background: var(--bg-2); border-radius: 4px; overflow: hidden; margin: 8px 0; border: 1px solid var(--line-soft); }
.bar div { height: 100%; background: var(--blue); }
.bar div.over { background: var(--warn); }
.recent { margin: 0; padding-left: 16px; display: grid; gap: 4px; }
.newp { gap: 12px; }
</style>

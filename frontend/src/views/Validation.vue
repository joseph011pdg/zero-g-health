<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2 class="title">When does a personal baseline detect better?</h2>
        <p>Personal baseline vs. one threshold for everyone. Tuned on some simulated missions and evaluated on different ones.</p>
      </div>
    </div>

    <div v-if="err" class="notice err">{{ err }}</div>
    <div v-if="!v && !err" class="skeleton" style="height: 300px" />
    <template v-if="v">
      <section class="panel proto">
        <div><span class="label">Tuning</span><div class="small">seeds {{ v.protocolo.semillas_ajuste.join('–') }} · 20 missions</div></div>
        <div><span class="label">Evaluation (independent)</span><div class="small">seeds {{ v.protocolo.semillas_evaluacion.join('–') }} ·
          {{ v.protocolo.misiones_evaluacion }} missions × {{ v.protocolo.astronautas_por_mision }} astronauts × {{ v.protocolo.dias_por_mision }} days</div></div>
        <div><span class="label">Chosen cutoffs</span><div class="small mono">Watch |z| ≥ {{ nn(v.parametros.yellow) }} · Act ≥ {{ nn(v.parametros.red) }} or {{ v.parametros.persist }} days</div></div>
        <div><span class="label">Tuning criterion</span><div class="small">{{ v.protocolo.restriccion_ajuste }}; maximum "Act" sensitivity</div></div>
        <div><span class="label">Events evaluated</span><div class="small">{{ g.B_fijo.eventos }} events · {{ nn(g.B_fijo.dias_sanos, 0) }} healthy days</div></div>
      </section>

      <section class="cols-3">
        <div v-for="(label, m, mi) in v.metodos" :key="m" class="panel method rise" :style="{ '--i': mi }" :class="m">
          <div class="label">{{ label }}</div>
          <div class="kpis">
            <div class="kpi"><span class="v">{{ nn(g[m].sensibilidad_pct) }} <small>%</small></span><span class="tiny muted">sensitivity (events)</span></div>
            <div class="kpi"><span class="v">{{ nn(g[m].retraso_medio_dias) }} <small>d</small></span><span class="tiny muted">mean delay · median {{ nn(g[m].retraso_mediano_dias) }} d</span></div>
            <div class="kpi"><span class="v">{{ nn(g[m].episodios_falsos_por_30_dias) }}</span><span class="tiny muted">false alarms / 30 astronaut-days</span></div>
            <div class="kpi"><span class="v">{{ nn(g[m].falsas_alarmas_dias_pct) }} <small>%</small></span><span class="tiny muted">healthy days with an alert</span></div>
          </div>
        </div>
      </section>

      <section class="cols-2">
        <div class="panel">
          <div class="panel-head"><h2>Sensitivity by scenario</h2><span class="tiny muted">% of events detected</span></div>
          <v-chart class="ch" :option="scenOpt('sensibilidad_pct', '%')" autoresize />
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Mean delay by scenario</h2><span class="tiny muted">days from onset (lower = earlier)</span></div>
          <v-chart class="ch" :option="scenOpt('retraso_medio_dias', 'd')" autoresize />
        </div>
      </section>

      <section class="cols-2">
        <div class="panel">
          <div class="panel-head"><h2>Key condition: differences between people</h2></div>
          <v-chart class="ch" :option="sweepOpt" autoresize />
          <p class="small">As heterogeneity between astronauts grows (between-person SD × factor), the fixed threshold loses
            sensitivity while the personal baseline holds. With very homogeneous populations (0.25×) the fixed threshold
            matches the sensitivity and alerts earlier: <strong>there, personalization brings no advantage</strong>.</p>
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Lead time, A vs. B</h2><span class="tiny muted">same events</span></div>
          <div class="table-wrap"><table class="table">
            <thead><tr><th></th><th>Watch</th><th>Act</th></tr></thead>
            <tbody>
              <tr v-for="r in ANT" :key="r.k"><td class="small">{{ r.l }}</td>
                <td class="num">{{ nn(v.evaluacion.anticipacion.A_vigilar[r.k]) }}</td><td class="num">{{ nn(v.evaluacion.anticipacion.A_actuar[r.k]) }}</td></tr>
            </tbody>
          </table></div>
          <p class="tiny muted">Positive mean lead time = A alerts before B. The "Act" level requires more evidence
            (cutoff {{ nn(v.parametros.red) }} or persistence), so on average it alerts <strong>later</strong> than the fixed threshold on
            the events both detect, in exchange for fewer false alarms and detecting events that B misses.</p>
        </div>
      </section>

      <section class="cols-2">
        <div class="panel">
          <div class="panel-head"><h2>Results by indicator</h2><span class="tiny muted">indicator sensitivity on the events that affect it · false alarms (% of days)</span></div>
          <div class="table-wrap"><table class="table">
            <thead><tr><th>Indicator</th><th>Events</th><th>A Watch</th><th>A Act</th><th>B fixed</th><th>FA A Act</th><th>FA B</th></tr></thead>
            <tbody><tr v-for="(x, k) in v.evaluacion.por_indicador.B_fijo" :key="k">
              <td>{{ s.indicators[k]?.corto || k }}</td><td class="num">{{ x.eventos_que_lo_afectan }}</td>
              <td class="num">{{ nn(v.evaluacion.por_indicador.A_vigilar[k].sensibilidad_pct) }}</td>
              <td class="num">{{ nn(v.evaluacion.por_indicador.A_actuar[k].sensibilidad_pct) }}</td>
              <td class="num">{{ nn(x.sensibilidad_pct) }}</td>
              <td class="num">{{ nn(v.evaluacion.por_indicador.A_actuar[k].falsas_alarmas_dias_pct) }}</td>
              <td class="num">{{ nn(x.falsas_alarmas_dias_pct) }}</td></tr></tbody>
          </table></div>
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Method A ablation</h2><span class="tiny muted">what each design choice adds</span></div>
          <div class="table-wrap"><table class="table">
            <thead><tr><th>Variant</th><th>Sens. Act</th><th>Delay</th><th>FA/30 d</th></tr></thead>
            <tbody><tr v-for="(x, k) in v.ablacion" :key="k" :class="{ hl: k === 'completo' }">
              <td class="small">{{ ABL[k] }}</td><td class="num">{{ nn(x.A_actuar.sensibilidad_pct) }}%</td>
              <td class="num">{{ nn(x.A_actuar.retraso_medio_dias) }} d</td><td class="num">{{ nn(x.A_actuar.episodios_falsos_por_30_dias) }}</td></tr></tbody>
          </table></div>
          <p class="tiny muted">The mission-start baseline is what allows slow deterioration to be detected (scenario E): without it,
            "Act" sensitivity drops markedly, in exchange for fewer false alarms.</p>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head"><h2>Cutoff tuning (tuning seeds only)</h2><span class="tiny muted">highlighted row = chosen</span></div>
        <div class="table-wrap"><table class="table">
          <thead><tr><th>Watch</th><th>Act</th><th>Sens. Watch</th><th>FA Watch /30 d</th><th>Sens. Act</th><th>Delay Act</th><th>FA Act /30 d</th><th>Meets</th></tr></thead>
          <tbody><tr v-for="(r, i) in v.ajuste" :key="i" :class="{ hl: r.yellow === v.parametros.yellow && r.red === v.parametros.red }">
            <td class="num">{{ nn(r.yellow) }}</td><td class="num">{{ nn(r.red) }}</td><td class="num">{{ nn(r.vigilar.sensibilidad_pct) }}%</td>
            <td class="num">{{ nn(r.vigilar.episodios_falsos_por_30_dias) }}</td><td class="num">{{ nn(r.actuar.sensibilidad_pct) }}%</td>
            <td class="num">{{ nn(r.actuar.retraso_medio_dias) }} d</td><td class="num">{{ nn(r.actuar.episodios_falsos_por_30_dias) }}</td>
            <td>{{ r.cumple_restriccion ? 'yes' : 'no' }}</td></tr></tbody>
        </table></div>
      </section>

      <section class="cols-2">
        <div class="panel grid">
          <h2><Icon name="flask" /> Reproduce an experiment</h2>
          <div class="cols-2">
            <label class="field"><span>Missions (1–30)</span><input class="input" type="number" min="1" max="30" v-model.number="ex.n_misiones" /></label>
            <label class="field"><span>Starting seed</span><input class="input" type="number" min="0" v-model.number="ex.semilla_inicial" /></label>
            <label class="field"><span>Scenario</span><select class="input" v-model="ex.escenario">
              <option :value="null">Mixed</option><option value="B">B · progressive fatigue</option><option value="C">C · physiological stress</option>
              <option value="D">D · solar event</option><option value="E">E · behavioral change</option></select></label>
            <label class="field"><span>Heterogeneity ({{ nn(ex.heterogeneidad) }}×)</span><input type="range" min="0.25" max="2.5" step="0.25" v-model.number="ex.heterogeneidad" /></label>
            <label class="field"><span>Missing data ({{ Math.round(ex.faltantes * 100) }}%)</span><input type="range" min="0" max="0.4" step="0.05" v-model.number="ex.faltantes" /></label>
            <label class="field"><span>Watch / Act cutoffs</span>
              <div class="row"><input class="input" type="number" step="0.5" v-model.number="ex.yellow" /><input class="input" type="number" step="0.5" v-model.number="ex.red" /></div></label>
          </div>
          <button class="btn primary" @click="runEx" :disabled="running"><Icon name="play" :size="14" />{{ running ? 'Running…' : 'Run' }}</button>
          <p class="tiny faint">The fixed threshold (B) uses the values tuned for 1× heterogeneity. Use seeds other than 1000–1019 so you do not evaluate on the tuning set.</p>
        </div>
        <div class="panel">
          <h2>Experiment result</h2>
          <p v-if="!exRes" class="small muted">Run an experiment to see the results here.</p>
          <template v-else>
            <p class="tiny muted mono">seeds {{ exRes.semillas.join('–') }} · {{ exRes.astronautas }} astronauts · scenario {{ exRes.escenario }} ·
              heterogeneity {{ nn(exRes.heterogeneidad) }}× · missing {{ Math.round(exRes.faltantes * 100) }}% · cutoffs {{ nn(exRes.parametros.yellow) }}/{{ nn(exRes.parametros.red) }} · {{ nn(exRes.segundos) }} s</p>
            <div class="table-wrap"><table class="table">
              <thead><tr><th>Method</th><th>Events</th><th>Sens.</th><th>Delay</th><th>FA/30 d</th><th>FA % days</th></tr></thead>
              <tbody><tr v-for="(x, m) in exRes.resultados.global" :key="m"><td class="small">{{ v.metodos[m] }}</td>
                <td class="num">{{ x.eventos }}</td><td class="num">{{ nn(x.sensibilidad_pct) }}%</td><td class="num">{{ nn(x.retraso_medio_dias) }} d</td>
                <td class="num">{{ nn(x.episodios_falsos_por_30_dias) }}</td><td class="num">{{ nn(x.falsas_alarmas_dias_pct) }}%</td></tr></tbody>
            </table></div>
          </template>
        </div>
      </section>

      <section class="panel" v-if="demo">
        <div class="panel-head"><h2>Per astronaut · loaded demo mission</h2><span class="tiny muted">{{ demo.nota }}</span></div>
        <div class="table-wrap"><table class="table">
          <thead><tr><th>Astronaut</th><th>Events</th><th>A Act: detected · FA/30 d</th><th>A Watch: detected · FA/30 d</th><th>B fixed: detected · FA/30 d</th></tr></thead>
          <tbody><tr v-for="(x, id) in demo.por_astronauta" :key="id">
            <td>{{ id }} · {{ x.nombre }}</td><td class="small">{{ x.eventos.map((e) => `${e.escenario} (D${e.start}–${e.end})`).join(', ') || '—' }}</td>
            <td class="num">{{ x.metodos.A_actuar.detectados }}/{{ x.metodos.A_actuar.eventos }} · {{ nn(x.metodos.A_actuar.episodios_falsos_por_30_dias) }}</td>
            <td class="num">{{ x.metodos.A_vigilar.detectados }}/{{ x.metodos.A_vigilar.eventos }} · {{ nn(x.metodos.A_vigilar.episodios_falsos_por_30_dias) }}</td>
            <td class="num">{{ x.metodos.B_fijo.detectados }}/{{ x.metodos.B_fijo.eventos }} · {{ nn(x.metodos.B_fijo.episodios_falsos_por_30_dias) }}</td></tr></tbody>
        </table></div>
      </section>

      <section class="cols-2">
        <div class="panel">
          <h2>Definitions</h2>
          <ul class="small defs">
            <li><strong>True event:</strong> deviation injected by the simulator (scenarios B, C, D, E) with known start, end and affected indicators; random intensity 0.5–1.5×.</li>
            <li><strong>Detection:</strong> any alert on an affected indicator between the start and the end + 2 days. <strong>Delay:</strong> days from the start to that alert.</li>
            <li><strong>Healthy day:</strong> day ≥ 14 outside [start − 1, end + 7] of every event. <strong>False alarm:</strong> alert on a healthy day; an episode is a run of alert days that starts on a healthy day.</li>
            <li><strong>Method B:</strong> 97.5th percentile (if rising is bad) or 2.5th (if falling is bad) of healthy days in the tuning population: {{ fixedTxt }}.</li>
          </ul>
        </div>
        <div class="panel">
          <h2>Experiment limitations</h2>
          <ul class="small defs">
            <li>All data are <strong>synthetic</strong>: the result depends on the simulator's assumptions (between-person differences larger than day-to-day variation, shape and size of the events).</li>
            <li>There is no validation with real astronaut data and no clinical validation. Showing that the method works on simulated data does not prove that it works in flight.</li>
            <li>The "Watch" level produces ~{{ nn(g.A_vigilar.episodios_falsos_por_30_dias) }} false notices per 30 days per astronaut when watching 6 indicators: it means repeat the measurement, not act.</li>
            <li>Comparator B is a population interval estimated on the same simulated population; real clinical thresholds (e.g., HR &gt; 100 bpm) would be even less sensitive to individual changes.</li>
            <li>14-day window and minimum of 7 observations fixed by design (not tuned).</li>
          </ul>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { api, useStore, nn } from '../store.js'
import { C, baseTooltip, axis } from '../charts.js'
import Icon from '../components/Icon.vue'

const s = useStore()
const v = ref(null)
const err = ref(null)
const demo = ref(null)
const running = ref(false)
const exRes = ref(null)
const ex = ref({ n_misiones: 10, semilla_inicial: 3000, escenario: null, heterogeneidad: 1, faltantes: 0, yellow: 2.5, red: 4.5 })
const COL = { A_vigilar: C.blue, A_actuar: C.ok, B_fijo: C.mars }
const ABL = { completo: 'Full (exclusion + mission-start baseline)', sin_excluir_alertas: 'Without excluding alert days',
  sin_linea_inicial: 'Without mission-start baseline', solo_ventana_movil: '14-day rolling window only' }
const ANT = [{ k: 'eventos_detectados_por_ambos', l: 'Events detected by both' }, { k: 'anticipacion_media_dias', l: 'Mean lead time (days)' },
  { k: 'A_antes_que_B', l: 'A alerts first' }, { k: 'mismo_dia', l: 'Same day' }, { k: 'B_antes_que_A', l: 'B alerts first' },
  { k: 'solo_A_detecta', l: 'Only A detects' }, { k: 'solo_B_detecta', l: 'Only B detects' }]

const g = computed(() => v.value.evaluacion.global)
const fixedTxt = computed(() => Object.entries(v.value.parametros.fixed)
  .map(([k, x]) => `${s.indicators[k]?.corto || k} ${nn(x, Math.max(1, s.indicators[k]?.decimales ?? 1))} ${s.indicators[k]?.unidad || ''}`).join(' · '))

onMounted(async () => {
  try {
    v.value = await api('/validation')
    ex.value.yellow = v.value.parametros.yellow; ex.value.red = v.value.parametros.red
  } catch (e) { err.value = e.message }
  try { demo.value = await api('/validation/demo') } catch { /* opcional */ }
})

function scenOpt(field, unit) {
  const ps = v.value.evaluacion.por_escenario
  const scs = Object.keys(ps.B_fijo)
  return {
    animation: true, tooltip: { ...baseTooltip, trigger: 'axis', valueFormatter: (x) => `${nn(x)} ${unit}` },
    legend: { top: 0, textStyle: { color: C.muted, fontSize: 11 } }, grid: { left: 40, right: 10, top: 34, bottom: 30 },
    xAxis: { type: 'category', data: scs.map((k) => `${k} · ${v.value.escenarios[k]}`), ...axis({ splitLine: { show: false } }),
      axisLabel: { color: C.muted, fontSize: 10, interval: 0, formatter: (x) => x.split(' · ')[1].replace(' (solar event)', '') } },
    yAxis: { type: 'value', ...axis() },
    series: Object.keys(v.value.metodos).map((m) => ({ name: v.value.metodos[m], type: 'bar', barGap: '10%',
      data: scs.map((k) => ps[m][k][field]), itemStyle: { color: COL[m], borderRadius: [3, 3, 0, 0] },
      label: { show: true, position: 'top', color: C.muted, fontSize: 9, formatter: (q) => nn(q.value) } }))
  }
}
const sweepOpt = computed(() => {
  const rows = v.value.heterogeneidad
  const xs = rows.map((r) => `${nn(r.heterogeneidad)}×`)
  return {
    tooltip: { ...baseTooltip, trigger: 'axis', valueFormatter: (x) => nn(x) }, legend: { top: 0, textStyle: { color: C.muted, fontSize: 11 } },
    grid: { left: 40, right: 44, top: 34, bottom: 30 },
    xAxis: { type: 'category', data: xs, name: 'heterogeneity', nameLocation: 'middle', nameGap: 22, nameTextStyle: { color: C.muted }, ...axis({ splitLine: { show: false } }) },
    yAxis: [{ type: 'value', min: 50, max: 100, name: 'sens. %', nameTextStyle: { color: C.muted }, ...axis() },
      { type: 'value', name: 'FA/30 d', nameTextStyle: { color: C.muted }, ...axis({ splitLine: { show: false } }) }],
    series: [
      { name: 'Sens. A Act', type: 'line', data: rows.map((r) => r.A_actuar.sensibilidad_pct), itemStyle: { color: C.ok }, symbolSize: 7 },
      { name: 'Sens. B fixed', type: 'line', data: rows.map((r) => r.B_fijo.sensibilidad_pct), itemStyle: { color: C.mars }, symbolSize: 7 },
      { name: 'FA A Act', type: 'bar', yAxisIndex: 1, data: rows.map((r) => r.A_actuar.episodios_falsos_por_30_dias), itemStyle: { color: 'rgba(31,122,77,.25)' }, barWidth: 12 },
      { name: 'FA B fixed', type: 'bar', yAxisIndex: 1, data: rows.map((r) => r.B_fijo.episodios_falsos_por_30_dias), itemStyle: { color: 'rgba(200,98,58,.25)' }, barWidth: 12 }
    ]
  }
})
async function runEx() {
  running.value = true
  try { exRes.value = await s.run(() => api('/validation/run', { method: 'POST', body: ex.value }), 'Experiment finished') } finally { running.value = false }
}
</script>

<style scoped>
.proto { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; }
.method { border-top: 4px solid var(--line); }
.method.A_vigilar { border-top-color: var(--blue); background: #f2f6fc; } .method.A_actuar { border-top-color: var(--ok); background: #f1f8f4; } .method.B_fijo { border-top-color: var(--mars); background: #fbf3ee; }
.method.A_actuar .kpi .v { color: var(--ok); } .method.B_fijo .kpi .v { color: var(--mars); }
.method > .label { font-size: 0.86rem; font-weight: 600; color: var(--ink); }
.proto { background: var(--blue-soft); border-color: #cfdcf0; }
.proto .label { color: var(--blue); font-weight: 600; }
.kpis { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px; }
.ch { height: 280px; width: 100%; }
.defs { margin: 8px 0 0; padding-left: 18px; display: grid; gap: 7px; line-height: 1.5; }
</style>

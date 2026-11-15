<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2 class="title">¿En qué condiciones la línea base individual detecta mejor?</h2>
        <p>Línea base individual frente a un umbral igual para todos. Ajustado con unas misiones simuladas y evaluado con otras distintas.</p>
      </div>
    </div>

    <div v-if="err" class="notice err">{{ err }}</div>
    <div v-if="!v && !err" class="skeleton" style="height: 300px" />
    <template v-if="v">
      <section class="panel proto">
        <div><span class="label">Ajuste</span><div class="small">semillas {{ v.protocolo.semillas_ajuste.join('–') }} · 20 misiones</div></div>
        <div><span class="label">Evaluación (independiente)</span><div class="small">semillas {{ v.protocolo.semillas_evaluacion.join('–') }} ·
          {{ v.protocolo.misiones_evaluacion }} misiones × {{ v.protocolo.astronautas_por_mision }} astronautas × {{ v.protocolo.dias_por_mision }} días</div></div>
        <div><span class="label">Cortes elegidos</span><div class="small mono">vigilar |z| ≥ {{ v.parametros.yellow }} · actuar ≥ {{ v.parametros.red }} o {{ v.parametros.persist }} días</div></div>
        <div><span class="label">Criterio de ajuste</span><div class="small">{{ v.protocolo.restriccion_ajuste }}; máxima sensibilidad "actuar"</div></div>
        <div><span class="label">Eventos evaluados</span><div class="small">{{ g.B_fijo.eventos }} eventos · {{ g.B_fijo.dias_sanos.toLocaleString('es') }} días sanos</div></div>
      </section>

      <section class="cols-3">
        <div v-for="(label, m) in v.metodos" :key="m" class="panel method" :class="m">
          <div class="label">{{ label }}</div>
          <div class="kpis">
            <div class="kpi"><span class="v">{{ g[m].sensibilidad_pct }}<small>%</small></span><span class="tiny muted">sensibilidad (eventos)</span></div>
            <div class="kpi"><span class="v">{{ g[m].retraso_medio_dias }}<small>d</small></span><span class="tiny muted">retraso medio · mediana {{ g[m].retraso_mediano_dias }} d</span></div>
            <div class="kpi"><span class="v">{{ g[m].episodios_falsos_por_30_dias }}</span><span class="tiny muted">falsas alarmas / 30 días-astronauta</span></div>
            <div class="kpi"><span class="v">{{ g[m].falsas_alarmas_dias_pct }}<small>%</small></span><span class="tiny muted">días sanos con alerta</span></div>
          </div>
        </div>
      </section>

      <section class="cols-2">
        <div class="panel">
          <div class="panel-head"><h2>Sensibilidad por escenario</h2><span class="tiny muted">% de eventos detectados</span></div>
          <v-chart class="ch" :option="scenOpt('sensibilidad_pct', '%')" autoresize />
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Retraso medio por escenario</h2><span class="tiny muted">días desde el inicio (menos = antes)</span></div>
          <v-chart class="ch" :option="scenOpt('retraso_medio_dias', 'd')" autoresize />
        </div>
      </section>

      <section class="cols-2">
        <div class="panel">
          <div class="panel-head"><h2>Condición clave: diferencias entre personas</h2></div>
          <v-chart class="ch" :option="sweepOpt" autoresize />
          <p class="small">Al aumentar la heterogeneidad entre astronautas (DE entre personas × factor), el umbral fijo pierde
            sensibilidad mientras la línea base individual se mantiene. Con poblaciones muy homogéneas (0,25×) el umbral fijo
            iguala la sensibilidad y avisa antes: <strong>ahí la personalización no aporta ventaja</strong>.</p>
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Anticipación A frente a B</h2><span class="tiny muted">mismos eventos</span></div>
          <table class="table">
            <thead><tr><th></th><th>Vigilar</th><th>Actuar</th></tr></thead>
            <tbody>
              <tr v-for="r in ANT" :key="r.k"><td class="small">{{ r.l }}</td>
                <td class="num">{{ v.evaluacion.anticipacion.A_vigilar[r.k] }}</td><td class="num">{{ v.evaluacion.anticipacion.A_actuar[r.k] }}</td></tr>
            </tbody>
          </table>
          <p class="tiny muted">Anticipación media positiva = A avisa antes que B. El nivel "actuar" exige más evidencia
            (corte {{ v.parametros.red }} o persistencia) y por eso, en promedio, avisa <strong>después</strong> que el umbral fijo en
            los eventos que ambos detectan, a cambio de menos falsas alarmas y de detectar eventos que B no ve.</p>
        </div>
      </section>

      <section class="cols-2">
        <div class="panel">
          <div class="panel-head"><h2>Resultados por indicador</h2><span class="tiny muted">sensibilidad del indicador en los eventos que lo afectan · falsas alarmas (% días)</span></div>
          <div class="table-wrap"><table class="table">
            <thead><tr><th>Indicador</th><th>Eventos</th><th>A vigilar</th><th>A actuar</th><th>B fijo</th><th>FA A act.</th><th>FA B</th></tr></thead>
            <tbody><tr v-for="(x, k) in v.evaluacion.por_indicador.B_fijo" :key="k">
              <td>{{ s.indicators[k]?.corto || k }}</td><td class="num">{{ x.eventos_que_lo_afectan }}</td>
              <td class="num">{{ v.evaluacion.por_indicador.A_vigilar[k].sensibilidad_pct ?? '—' }}</td>
              <td class="num">{{ v.evaluacion.por_indicador.A_actuar[k].sensibilidad_pct ?? '—' }}</td>
              <td class="num">{{ x.sensibilidad_pct ?? '—' }}</td>
              <td class="num">{{ v.evaluacion.por_indicador.A_actuar[k].falsas_alarmas_dias_pct }}</td>
              <td class="num">{{ x.falsas_alarmas_dias_pct }}</td></tr></tbody>
          </table></div>
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Ablación del método A</h2><span class="tiny muted">qué aporta cada decisión</span></div>
          <table class="table">
            <thead><tr><th>Variante</th><th>Sens. actuar</th><th>Retraso</th><th>FA/30 d</th></tr></thead>
            <tbody><tr v-for="(x, k) in v.ablacion" :key="k" :class="{ hl: k === 'completo' }">
              <td class="small">{{ ABL[k] }}</td><td class="num">{{ x.A_actuar.sensibilidad_pct }} %</td>
              <td class="num">{{ x.A_actuar.retraso_medio_dias }} d</td><td class="num">{{ x.A_actuar.episodios_falsos_por_30_dias }}</td></tr></tbody>
          </table>
          <p class="tiny muted">La línea base inicial es la que permite detectar deterioros lentos (escenario E): sin ella la
            sensibilidad "actuar" cae de forma marcada, a cambio de menos falsas alarmas.</p>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head"><h2>Ajuste de cortes (solo semillas de ajuste)</h2><span class="tiny muted">fila resaltada = elegida</span></div>
        <div class="table-wrap"><table class="table">
          <thead><tr><th>Amarillo</th><th>Rojo</th><th>Sens. vigilar</th><th>FA vigilar /30 d</th><th>Sens. actuar</th><th>Retraso actuar</th><th>FA actuar /30 d</th><th>Cumple</th></tr></thead>
          <tbody><tr v-for="(r, i) in v.ajuste" :key="i" :class="{ hl: r.yellow === v.parametros.yellow && r.red === v.parametros.red }">
            <td class="num">{{ r.yellow }}</td><td class="num">{{ r.red }}</td><td class="num">{{ r.vigilar.sensibilidad_pct }} %</td>
            <td class="num">{{ r.vigilar.episodios_falsos_por_30_dias }}</td><td class="num">{{ r.actuar.sensibilidad_pct }} %</td>
            <td class="num">{{ r.actuar.retraso_medio_dias }} d</td><td class="num">{{ r.actuar.episodios_falsos_por_30_dias }}</td>
            <td>{{ r.cumple_restriccion ? 'sí' : 'no' }}</td></tr></tbody>
        </table></div>
      </section>

      <section class="cols-2">
        <div class="panel grid">
          <h2><Icon name="flask" /> Reproducir un experimento</h2>
          <div class="cols-2">
            <label class="field"><span>Misiones (1–30)</span><input class="input" type="number" min="1" max="30" v-model.number="ex.n_misiones" /></label>
            <label class="field"><span>Semilla inicial</span><input class="input" type="number" min="0" v-model.number="ex.semilla_inicial" /></label>
            <label class="field"><span>Escenario</span><select class="input" v-model="ex.escenario">
              <option :value="null">Mixto</option><option value="B">B · fatiga progresiva</option><option value="C">C · estrés fisiológico</option>
              <option value="D">D · evento solar</option><option value="E">E · cambio conductual</option></select></label>
            <label class="field"><span>Heterogeneidad ({{ ex.heterogeneidad }}×)</span><input type="range" min="0.25" max="2.5" step="0.25" v-model.number="ex.heterogeneidad" /></label>
            <label class="field"><span>Datos faltantes ({{ Math.round(ex.faltantes * 100) }} %)</span><input type="range" min="0" max="0.4" step="0.05" v-model.number="ex.faltantes" /></label>
            <label class="field"><span>Cortes amarillo / rojo</span>
              <div class="row"><input class="input" type="number" step="0.5" v-model.number="ex.yellow" /><input class="input" type="number" step="0.5" v-model.number="ex.red" /></div></label>
          </div>
          <button class="btn primary" @click="runEx" :disabled="running"><Icon name="play" :size="14" />{{ running ? 'Calculando…' : 'Ejecutar' }}</button>
          <p class="tiny faint">El umbral fijo (B) usa los valores ajustados para heterogeneidad 1×. Use semillas distintas de 1000–1019 para no evaluar con el conjunto de ajuste.</p>
        </div>
        <div class="panel">
          <h2>Resultado del experimento</h2>
          <p v-if="!exRes" class="small muted">Ejecute un experimento para ver los resultados aquí.</p>
          <template v-else>
            <p class="tiny muted mono">semillas {{ exRes.semillas.join('–') }} · {{ exRes.astronautas }} astronautas · escenario {{ exRes.escenario }} ·
              heterogeneidad {{ exRes.heterogeneidad }}× · faltantes {{ Math.round(exRes.faltantes * 100) }} % · cortes {{ exRes.parametros.yellow }}/{{ exRes.parametros.red }} · {{ exRes.segundos }} s</p>
            <table class="table">
              <thead><tr><th>Método</th><th>Eventos</th><th>Sens.</th><th>Retraso</th><th>FA/30 d</th><th>FA % días</th></tr></thead>
              <tbody><tr v-for="(x, m) in exRes.resultados.global" :key="m"><td class="small">{{ v.metodos[m] }}</td>
                <td class="num">{{ x.eventos }}</td><td class="num">{{ x.sensibilidad_pct }} %</td><td class="num">{{ x.retraso_medio_dias ?? '—' }} d</td>
                <td class="num">{{ x.episodios_falsos_por_30_dias }}</td><td class="num">{{ x.falsas_alarmas_dias_pct }} %</td></tr></tbody>
            </table>
          </template>
        </div>
      </section>

      <section class="panel" v-if="demo">
        <div class="panel-head"><h2>Por astronauta · misión de demostración cargada</h2><span class="tiny muted">{{ demo.nota }}</span></div>
        <div class="table-wrap"><table class="table">
          <thead><tr><th>Astronauta</th><th>Eventos</th><th>A actuar: detectados · FA/30 d</th><th>A vigilar: detectados · FA/30 d</th><th>B fijo: detectados · FA/30 d</th></tr></thead>
          <tbody><tr v-for="(x, id) in demo.por_astronauta" :key="id">
            <td>{{ id }} · {{ x.nombre }}</td><td class="small">{{ x.eventos.map((e) => `${e.escenario} (D${e.start}–${e.end})`).join(', ') || '—' }}</td>
            <td class="num">{{ x.metodos.A_actuar.detectados }}/{{ x.metodos.A_actuar.eventos }} · {{ x.metodos.A_actuar.episodios_falsos_por_30_dias }}</td>
            <td class="num">{{ x.metodos.A_vigilar.detectados }}/{{ x.metodos.A_vigilar.eventos }} · {{ x.metodos.A_vigilar.episodios_falsos_por_30_dias }}</td>
            <td class="num">{{ x.metodos.B_fijo.detectados }}/{{ x.metodos.B_fijo.eventos }} · {{ x.metodos.B_fijo.episodios_falsos_por_30_dias }}</td></tr></tbody>
        </table></div>
      </section>

      <section class="cols-2">
        <div class="panel">
          <h2>Definiciones</h2>
          <ul class="small defs">
            <li><strong>Evento verdadero:</strong> desviación inyectada por el simulador (escenarios B, C, D, E) con inicio, fin e indicadores afectados conocidos; intensidad aleatoria 0,5–1,5×.</li>
            <li><strong>Detección:</strong> alguna alerta en un indicador afectado entre el inicio y el fin + 2 días. <strong>Retraso:</strong> días desde el inicio hasta esa alerta.</li>
            <li><strong>Día sano:</strong> día ≥ 14 fuera de [inicio − 1, fin + 7] de todo evento. <strong>Falsa alarma:</strong> alerta en un día sano; un episodio es una racha de días con alerta que empieza en un día sano.</li>
            <li><strong>Método B:</strong> percentil 97,5 (si subir es malo) o 2,5 (si bajar es malo) de los días sanos de la población de ajuste: {{ fixedTxt }}.</li>
          </ul>
        </div>
        <div class="panel">
          <h2>Limitaciones del experimento</h2>
          <ul class="small defs">
            <li>Todos los datos son <strong>sintéticos</strong>: el resultado depende de los supuestos del simulador (diferencias entre personas mayores que la variación diaria, forma y tamaño de los eventos).</li>
            <li>No hay validación con datos reales de astronautas ni validación clínica. Mostrar que el método funciona en datos simulados no prueba que funcione en vuelo.</li>
            <li>El nivel "vigilar" genera ~{{ g.A_vigilar.episodios_falsos_por_30_dias }} avisos falsos por 30 días por astronauta al vigilar 6 indicadores: es un aviso para repetir la medición, no para actuar.</li>
            <li>El comparador B es un intervalo poblacional estimado en la misma población simulada; umbrales clínicos reales (p. ej., FC &gt; 100 lpm) serían aún menos sensibles a cambios individuales.</li>
            <li>Ventana de 14 días y min. 7 observaciones fijadas por diseño (no ajustadas).</li>
          </ul>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { api, useStore } from '../store.js'
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
const ABL = { completo: 'Completo (exclusión + línea inicial)', sin_excluir_alertas: 'Sin excluir días en alerta',
  sin_linea_inicial: 'Sin línea base inicial', solo_ventana_movil: 'Solo ventana móvil de 14 días' }
const ANT = [{ k: 'eventos_detectados_por_ambos', l: 'Eventos detectados por ambos' }, { k: 'anticipacion_media_dias', l: 'Anticipación media (días)' },
  { k: 'A_antes_que_B', l: 'A avisa antes' }, { k: 'mismo_dia', l: 'Mismo día' }, { k: 'B_antes_que_A', l: 'B avisa antes' },
  { k: 'solo_A_detecta', l: 'Solo A detecta' }, { k: 'solo_B_detecta', l: 'Solo B detecta' }]

const g = computed(() => v.value.evaluacion.global)
const fixedTxt = computed(() => Object.entries(v.value.parametros.fixed)
  .map(([k, x]) => `${s.indicators[k]?.corto || k} ${x} ${s.indicators[k]?.unidad || ''}`).join(' · '))

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
    animation: true, tooltip: { ...baseTooltip, trigger: 'axis', valueFormatter: (x) => `${x} ${unit}` },
    legend: { top: 0, textStyle: { color: C.muted, fontSize: 11 } }, grid: { left: 40, right: 10, top: 34, bottom: 30 },
    xAxis: { type: 'category', data: scs.map((k) => `${k} · ${v.value.escenarios[k]}`), ...axis({ splitLine: { show: false } }),
      axisLabel: { color: C.muted, fontSize: 10, interval: 0, formatter: (x) => x.split(' · ')[1].replace(' (evento solar)', '') } },
    yAxis: { type: 'value', ...axis() },
    series: Object.keys(v.value.metodos).map((m) => ({ name: v.value.metodos[m], type: 'bar', barGap: '10%',
      data: scs.map((k) => ps[m][k][field]), itemStyle: { color: COL[m], borderRadius: [3, 3, 0, 0] },
      label: { show: true, position: 'top', color: C.muted, fontSize: 9 } }))
  }
}
const sweepOpt = computed(() => {
  const rows = v.value.heterogeneidad
  const xs = rows.map((r) => `${r.heterogeneidad}×`)
  return {
    tooltip: { ...baseTooltip, trigger: 'axis' }, legend: { top: 0, textStyle: { color: C.muted, fontSize: 11 } },
    grid: { left: 40, right: 44, top: 34, bottom: 30 },
    xAxis: { type: 'category', data: xs, name: 'heterogeneidad', nameLocation: 'middle', nameGap: 22, nameTextStyle: { color: C.muted }, ...axis({ splitLine: { show: false } }) },
    yAxis: [{ type: 'value', min: 50, max: 100, name: 'sens. %', nameTextStyle: { color: C.muted }, ...axis() },
      { type: 'value', name: 'FA/30 d', nameTextStyle: { color: C.muted }, ...axis({ splitLine: { show: false } }) }],
    series: [
      { name: 'Sens. A actuar', type: 'line', data: rows.map((r) => r.A_actuar.sensibilidad_pct), itemStyle: { color: C.ok }, symbolSize: 7 },
      { name: 'Sens. B fijo', type: 'line', data: rows.map((r) => r.B_fijo.sensibilidad_pct), itemStyle: { color: C.mars }, symbolSize: 7 },
      { name: 'FA A actuar', type: 'bar', yAxisIndex: 1, data: rows.map((r) => r.A_actuar.episodios_falsos_por_30_dias), itemStyle: { color: 'rgba(31,122,77,.25)' }, barWidth: 12 },
      { name: 'FA B fijo', type: 'bar', yAxisIndex: 1, data: rows.map((r) => r.B_fijo.episodios_falsos_por_30_dias), itemStyle: { color: 'rgba(200,98,58,.25)' }, barWidth: 12 }
    ]
  }
})
async function runEx() {
  running.value = true
  try { exRes.value = await s.run(() => api('/validation/run', { method: 'POST', body: ex.value }), 'Experimento terminado') } finally { running.value = false }
}
</script>

<style scoped>
.proto { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; }
.method { border-top: 3px solid var(--line); }
.method.A_vigilar { border-top-color: var(--blue); } .method.A_actuar { border-top-color: var(--ok); } .method.B_fijo { border-top-color: var(--mars); }
.kpis { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px; }
.ch { height: 280px; width: 100%; }
.defs { margin: 8px 0 0; padding-left: 18px; display: grid; gap: 7px; line-height: 1.5; }
</style>

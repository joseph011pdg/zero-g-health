<template>
  <div class="page">
    <section class="cols-2">
      <form class="panel grid" @submit.prevent="sendManual">
        <h2>Medición manual</h2>
        <label class="field"><span>Astronauta</span>
          <select class="input" v-model="mm.astro_id"><option v-for="c in s.crew" :key="c.id" :value="c.id">{{ c.nombre }}</option></select></label>
        <div class="cols-2">
          <label class="field"><span>Indicador</span>
            <select class="input" v-model="mm.indicator" @change="mm.unit = s.indicators[mm.indicator].unidad">
              <option v-for="(c, k) in s.indicators" :key="k" :value="k">{{ c.corto }}</option></select></label>
          <label class="field"><span>Valor ({{ s.indicators[mm.indicator].unidad }})</span>
            <input class="input" type="number" step="any" v-model.number="mm.value" required /></label>
          <label class="field"><span>Día</span><input class="input" type="number" min="0" :max="s.mission.dias - 1" v-model.number="mm.day" /></label>
          <label class="field"><span>Origen</span><select class="input" v-model="mm.source">
            <option value="manual">Manual</option><option value="real">Sensor real</option></select></label>
        </div>
        <button class="btn primary" :disabled="busy">Guardar medición</button>
        <p class="tiny muted">Rango aceptado: {{ s.indicators[mm.indicator].limites.join(' – ') }} {{ s.indicators[mm.indicator].unidad }}.</p>
      </form>

      <div class="panel grid">
        <h2>Importar CSV</h2>
        <p class="tiny muted"><code>astro_id,day,indicator,value,unit[,source]</code> · indicadores: {{ Object.keys(s.indicators).join(', ') }}</p>
        <div class="row wrap">
          <label class="btn"><Icon name="upload" :size="14" /> Elegir archivo<input type="file" accept=".csv,text/csv" hidden @change="readFile" /></label>
          <button class="btn ghost" @click="example">Ejemplo con errores</button>
        </div>
        <textarea class="input mono csv" v-model="csvText" placeholder="astro_id,day,indicator,value,unit" aria-label="Contenido CSV" />
        <label class="row small"><input type="checkbox" v-model="overwrite" /> Sobrescribir valores existentes</label>
        <button class="btn primary" @click="sendCsv" :disabled="!csvText.trim() || busy">Validar e importar</button>
        <div v-if="csvRes" class="sub grid">
          <div class="row wrap small"><span class="c-verde strong">{{ csvRes.insertados }} nuevos</span>
            <span>{{ csvRes.reemplazados }} reemplazados</span><span class="c-amarillo strong">{{ csvRes.rechazados.length }} rechazados</span></div>
          <ul v-if="csvRes.rechazados.length" class="rej tiny">
            <li v-for="(r, i) in csvRes.rechazados" :key="i"><span class="mono">{{ r.astro_id }} · {{ r.day }} · {{ r.indicator }} · {{ r.value }}</span> — {{ r.motivo }}</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="cols-2">
      <form class="panel grid" @submit.prevent="createProfile">
        <h2>Nuevo astronauta</h2>
        <div class="cols-2">
          <label class="field"><span>Identificador</span><input class="input" v-model="np.id" required pattern="[A-Za-z0-9_-]{2,8}" placeholder="A5" /></label>
          <label class="field"><span>Nombre (ficticio)</span><input class="input" v-model="np.nombre" required minlength="2" /></label>
          <label class="field"><span>Rol</span><input class="input" v-model="np.rol" required minlength="2" /></label>
          <label class="field"><span>Datos iniciales</span>
            <select class="input" v-model="np.generar_datos">
              <option value="ninguno">Ninguno</option><option value="A">Simulados · estable</option>
              <option value="B">Simulados · fatiga</option><option value="C">Simulados · estrés</option><option value="E">Simulados · conductual</option>
            </select></label>
        </div>
        <button class="btn primary" type="submit" :disabled="s.publico">Crear perfil</button>
        <p v-if="s.publico" class="tiny c-amarillo">Disponible en la versión local.</p>
      </form>
      <IngestLog :key="logKey" />
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, useStore } from '../store.js'
import Icon from '../components/Icon.vue'
import IngestLog from '../components/IngestLog.vue'

const s = useStore()
const router = useRouter()
const busy = ref(false)
const logKey = ref(0)
const mm = reactive({ astro_id: s.selected, indicator: 'rhr', value: null, unit: 'lpm', day: s.day, source: 'manual' })
watch(() => s.day, (d) => { mm.day = d })
const csvText = ref('')
const overwrite = ref(false)
const csvRes = ref(null)
const np = ref({ id: '', nombre: '', rol: '', generar_datos: 'ninguno' })

async function act(fn, msg) {
  busy.value = true
  try { const r = await s.run(fn, msg); await s.refresh(); logKey.value++; return r } finally { busy.value = false }
}
async function sendManual() { await act(() => api('/measurements', { method: 'POST', body: { ...mm } }), 'Medición guardada') }
function readFile(e) {
  const f = e.target.files[0]
  if (!f) return
  if (f.size > 2_000_000) { s.toast('Archivo demasiado grande (máx. 2 MB)', 'err'); return }
  const r = new FileReader(); r.onload = () => { csvText.value = r.result }; r.readAsText(f)
}
function example() {
  const a = s.selected, d = s.day
  csvText.value = `astro_id,day,indicator,value,unit,source\n${a},${d},rhr,64,bpm,csv\n${a},${d},sleep,6.2,h,csv\n${a},${d},hrv,40,lpm,csv\n${a},${d},sleep,30,h,csv\nZZ9,${d},mood,6,/10,csv\n${a},${d},mood,,/10,csv`
}
async function sendCsv() { csvRes.value = await act(() => api('/ingest/csv', { method: 'POST', body: { csv: csvText.value, sobrescribir: overwrite.value } })) }
async function createProfile() {
  const r = await act(() => api('/astronauts', { method: 'POST', body: { ...np.value } }), 'Perfil creado')
  router.push(`/persona/${r.id}`)
}
</script>

<style scoped>
.csv { min-height: 120px; font-size: 0.8rem; }
.rej { margin: 0; padding-left: 16px; display: grid; gap: 3px; }
code { font-family: var(--mono); background: var(--surface-2); padding: 1px 5px; border-radius: 4px; }
</style>

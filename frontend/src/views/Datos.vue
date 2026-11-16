<template>
  <div class="page">
    <section class="cols-2">
      <form class="panel grid" @submit.prevent="sendManual">
        <h2>Manual measurement</h2>
        <label class="field"><span>Astronaut</span>
          <select class="input" v-model="mm.astro_id"><option v-for="c in s.crew" :key="c.id" :value="c.id">{{ c.nombre }}</option></select></label>
        <div class="cols-2">
          <label class="field"><span>Indicator</span>
            <select class="input" v-model="mm.indicator" @change="mm.unit = s.indicators[mm.indicator].unidad">
              <option v-for="(c, k) in s.indicators" :key="k" :value="k">{{ c.corto }}</option></select></label>
          <label class="field"><span>Value ({{ s.indicators[mm.indicator].unidad }})</span>
            <input class="input" type="number" step="any" v-model.number="mm.value" required /></label>
          <label class="field"><span>Day</span><input class="input" type="number" min="0" :max="s.mission.dias - 1" v-model.number="mm.day" /></label>
          <label class="field"><span>Source</span><select class="input" v-model="mm.source">
            <option value="manual">Manual</option><option value="real">Real sensor</option></select></label>
        </div>
        <button class="btn primary" :disabled="busy">Save measurement</button>
        <p class="tiny muted">Accepted range: {{ s.indicators[mm.indicator].limites.join(' – ') }} {{ s.indicators[mm.indicator].unidad }}.</p>
      </form>

      <div class="panel grid">
        <h2>Import CSV</h2>
        <p class="tiny muted"><code>astro_id,day,indicator,value,unit[,source]</code> · indicators: {{ Object.keys(s.indicators).join(', ') }}</p>
        <div class="row wrap">
          <label class="btn"><Icon name="upload" :size="14" /> Choose file<input type="file" accept=".csv,text/csv" hidden @change="readFile" /></label>
          <button class="btn ghost" @click="example">Example with errors</button>
        </div>
        <textarea class="input mono csv" v-model="csvText" placeholder="astro_id,day,indicator,value,unit" aria-label="CSV content" />
        <label class="row small"><input type="checkbox" v-model="overwrite" /> Overwrite existing values</label>
        <button class="btn primary" @click="sendCsv" :disabled="!csvText.trim() || busy">Validate and import</button>
        <div v-if="csvRes" class="sub grid">
          <div class="row wrap small"><span class="c-verde strong">{{ csvRes.insertados }} new</span>
            <span>{{ csvRes.reemplazados }} replaced</span><span class="c-amarillo strong">{{ csvRes.rechazados.length }} rejected</span></div>
          <ul v-if="csvRes.rechazados.length" class="rej tiny">
            <li v-for="(r, i) in csvRes.rechazados" :key="i"><span class="mono">{{ r.astro_id }} · {{ r.day }} · {{ r.indicator }} · {{ r.value }}</span>: {{ r.motivo }}</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="cols-2">
      <form class="panel grid" @submit.prevent="createProfile">
        <h2>New astronaut</h2>
        <div class="cols-2">
          <label class="field"><span>Identifier</span><input class="input" v-model="np.id" required pattern="[A-Za-z0-9_-]{2,8}" placeholder="A5" /></label>
          <label class="field"><span>Name (fictional)</span><input class="input" v-model="np.nombre" required minlength="2" /></label>
          <label class="field"><span>Role</span><input class="input" v-model="np.rol" required minlength="2" /></label>
          <label class="field"><span>Initial data</span>
            <select class="input" v-model="np.generar_datos">
              <option value="ninguno">None</option><option value="A">Simulated · stable</option>
              <option value="B">Simulated · fatigue</option><option value="C">Simulated · stress</option><option value="E">Simulated · behavioral</option>
            </select></label>
        </div>
        <button class="btn primary" type="submit" :disabled="s.publico">Create profile</button>
        <p v-if="s.publico" class="tiny c-amarillo">Available in the local version.</p>
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
const mm = reactive({ astro_id: s.selected, indicator: 'rhr', value: null, unit: 'bpm', day: s.day, source: 'manual' })
watch(() => s.day, (d) => { mm.day = d })
const csvText = ref('')
const overwrite = ref(false)
const csvRes = ref(null)
const np = ref({ id: '', nombre: '', rol: '', generar_datos: 'ninguno' })

async function act(fn, msg) {
  busy.value = true
  try { const r = await s.run(fn, msg); await s.refresh(); logKey.value++; return r } finally { busy.value = false }
}
async function sendManual() { await act(() => api('/measurements', { method: 'POST', body: { ...mm } }), 'Measurement saved') }
function readFile(e) {
  const f = e.target.files[0]
  if (!f) return
  if (f.size > 2_000_000) { s.toast('File too large (max. 2 MB)', 'err'); return }
  const r = new FileReader(); r.onload = () => { csvText.value = r.result }; r.readAsText(f)
}
function example() {
  const a = s.selected, d = s.day
  csvText.value = `astro_id,day,indicator,value,unit,source\n${a},${d},rhr,64,bpm,csv\n${a},${d},sleep,6.2,h,csv\n${a},${d},hrv,40,lpm,csv\n${a},${d},sleep,30,h,csv\nZZ9,${d},mood,6,/10,csv\n${a},${d},mood,,/10,csv`
}
async function sendCsv() { csvRes.value = await act(() => api('/ingest/csv', { method: 'POST', body: { csv: csvText.value, sobrescribir: overwrite.value } })) }
async function createProfile() {
  const r = await act(() => api('/astronauts', { method: 'POST', body: { ...np.value } }), 'Profile created')
  router.push(`/crew/${r.id}`)
}
</script>

<style scoped>
.csv { min-height: 120px; font-size: 0.8rem; }
.rej { margin: 0; padding-left: 16px; display: grid; gap: 3px; }
code { font-family: var(--mono); background: var(--surface-2); padding: 1px 5px; border-radius: 4px; }
</style>

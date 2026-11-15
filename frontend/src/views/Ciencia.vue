<template>
  <div class="page">
    <section class="hero panel">
      <div class="pics">
        <img class="planet" src="/img/tierra.jpg" alt="La Tierra vista por el Apolo 17" width="120" height="120" />
        <img class="planet" src="/img/marte.jpg" alt="Marte, mosaico del Viking Orbiter" width="104" height="104" />
      </div>
      <div class="grid">
        <h2>Cada astronauta se compara consigo mismo</h2>
        <div class="formula mono">z = (valor de hoy − mediana de sus 14 días previos) / (1,4826 × MAD)</div>
        <p class="small">Vigilar si z ≥ {{ nn(p.yellow) }} · Actuar si z ≥ {{ nn(p.red) }} o {{ p.persist }} días seguidos en vigilar. Son parámetros
          experimentales ({{ p.origen }}), no límites médicos.</p>
      </div>
    </section>

    <section class="cols-2">
      <div class="panel">
        <h2 class="mb">Cómo decide</h2>
        <ul class="small list">
          <li>El valor de hoy nunca entra en su propia referencia.</li>
          <li>Los días en alerta no se suman a la línea base: un deterioro no se “normaliza”.</li>
          <li>También compara con sus primeros 14 días de misión para ver cambios lentos.</li>
          <li>Sin medición: “sin dato”. Con menos de 7 días: “calibrando”. Nunca supone que está bien.</li>
          <li>Las recomendaciones son de seguimiento; las rojas remiten al oficial médico.</li>
        </ul>
      </div>
      <div class="panel">
        <h2 class="mb">Qué es real y qué es simulado</h2>
        <ul class="small list">
          <li><strong>Simulado:</strong> todas las mediciones, la tripulación (ficticia), los eventos, el apagón y el envío a la Tierra.</li>
          <li><strong>De la literatura:</strong> dosis ~0,4 mGy/día (Patel et al., 2020), lapso PVT-B ≥ 355 ms (Basner et al., 2011), sueño ≥ 7 h (Watson et al., 2015).</li>
          <li><strong>Datos NASA:</strong> el prototipo no incluye mediciones individuales de NASA; acepta datos reales por CSV.</li>
          <li><strong>Imágenes:</strong> fotos de dominio público de NASA (créditos abajo); retratos ilustrados propios.</li>
        </ul>
      </div>
    </section>

    <section class="panel">
      <h2 class="mb">Indicadores</h2>
      <div class="table-wrap"><table class="table">
        <thead><tr><th>Indicador</th><th>Sensor</th><th>Empeora si</th><th class="right">Umbral poblacional</th><th>Referencia clínica</th></tr></thead>
        <tbody><tr v-for="(c, k) in s.indicators" :key="k">
          <td class="strong"><Icon :name="IND_ICON[k]" :size="14" /> {{ c.corto }} <span class="muted">({{ c.unidad }})</span></td>
          <td class="small">{{ c.sensor }}</td><td>{{ c.direction > 0 ? 'sube' : 'baja' }}</td>
          <td class="num right">{{ nn(c.umbral_fijo, Math.max(1, c.decimales)) }}</td><td class="small muted">{{ c.clinical }}</td></tr></tbody>
      </table></div>
    </section>

    <section class="cols-2">
      <div class="panel">
        <h2 class="mb">Fuentes</h2>
        <ul class="refs small">
          <li v-for="e in ev" :key="e.id">{{ e.cita }} <span class="tiny muted">· {{ e.tipo }}{{ e.en_propuesta ? '' : ' · añadida' }}</span></li>
        </ul>
      </div>
      <div class="panel">
        <h2 class="mb">Limitaciones</h2>
        <ul class="small list">
          <li>Validado solo con datos simulados; sin validación clínica.</li>
          <li>La PVT en navegador no corrige la latencia del equipo.</li>
          <li>El ánimo es una sola pregunta, no un test psicológico validado.</li>
          <li>La dosis acumulada se compara con el presupuesto de la misión simulada, no con límites de NASA.</li>
          <li>Falta que el oficial médico pueda aceptar una nueva línea base tras una adaptación legítima.</li>
        </ul>
        <p class="tiny muted credits">Imágenes: “The Blue Marble”, NASA/tripulación del Apolo 17, dominio público; “Valles Marineris”, Viking Orbiter, NASA/USGS,
          dominio público; video “ISS Fly-Through to Cupola (8K)” (NASA); mapas “Blue Marble Next Generation” (NASA) y “Mars Viking MDIM21” (NASA/JPL/USGS); todos de dominio público, vía Wikimedia Commons. BASAL no está afiliado ni respaldado por NASA.</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api, useStore, nn, IND_ICON } from '../store.js'
import Icon from '../components/Icon.vue'
const s = useStore()
const ev = ref([])
const p = computed(() => s.mission.parametros)
onMounted(async () => { ev.value = await api('/evidence') })
</script>

<style scoped>
.hero { display: flex; gap: 24px; align-items: center; flex-wrap: wrap; }
.pics { display: flex; align-items: center; gap: 10px; }
.planet { border-radius: 50%; object-fit: cover; clip-path: circle(47%); }
.formula { background: var(--blue-soft); color: var(--blue); padding: 12px 14px; border-radius: 10px; font-size: 0.9rem; }
.mb { margin-bottom: 10px; }
.list { margin: 0; padding-left: 18px; display: grid; gap: 6px; line-height: 1.5; }
.refs { margin: 0; padding-left: 16px; display: grid; gap: 8px; line-height: 1.45; }
.credits { margin-top: 12px; }
</style>

<template>
  <div class="page">
    <section class="hero panel">
      <div class="pics">
        <img class="planet" src="/img/tierra.jpg" alt="Earth seen by Apollo 17" width="120" height="120" />
        <img class="planet" src="/img/marte.jpg" alt="Mars, Viking Orbiter mosaic" width="104" height="104" />
      </div>
      <div class="grid">
        <h2>Each astronaut is compared with themselves</h2>
        <div class="formula mono">z = (today's value − median of their previous 14 days) / (1.4826 × MAD)</div>
        <p class="small">Watch if z ≥ {{ nn(p.yellow) }}. Act if z ≥ {{ nn(p.red) }} or {{ p.persist }} days in a row at Watch. These are experimental
          parameters ({{ p.origen }}), not medical limits.</p>
      </div>
    </section>

    <section class="cols-2">
      <div class="panel">
        <h2 class="mb">How it decides</h2>
        <ul class="small list">
          <li>Today's value never enters its own reference.</li>
          <li>Alert days are not added to the baseline: a deterioration is not “normalized”.</li>
          <li>It also compares with the first 14 mission days to catch slow changes.</li>
          <li>No measurement: “No data”. Fewer than 7 days: “Calibrating”. It never assumes everything is fine.</li>
          <li>Recommendations are follow-up only; Act alerts go to the Medical Officer.</li>
        </ul>
      </div>
      <div class="panel">
        <h2 class="mb">What is real and what is simulated</h2>
        <ul class="small list">
          <li><strong>Simulated:</strong> all measurements, the (fictional) crew, the events, the blackout and the transmission to Earth.</li>
          <li><strong>From the literature:</strong> dose ~0.4 mGy/day (Patel et al., 2020), PVT-B lapse ≥ 355 ms (Basner et al., 2011), sleep ≥ 7 h (Watson et al., 2015).</li>
          <li><strong>NASA data:</strong> the prototype includes no individual NASA measurements; it accepts real data via CSV.</li>
          <li><strong>Images:</strong> NASA public-domain photos and video (credits below); <strong>AI-generated portraits of fictional crew</strong> (illustrations made with Claude, Anthropic).</li>
        </ul>
      </div>
    </section>

    <section class="panel">
      <h2 class="mb">Indicators</h2>
      <div class="table-wrap"><table class="table">
        <thead><tr><th>Indicator</th><th>Sensor</th><th>Worse if it</th><th class="right">Population threshold</th><th>Clinical reference</th></tr></thead>
        <tbody><tr v-for="(c, k) in s.indicators" :key="k">
          <td class="strong"><Icon :name="IND_ICON[k]" :size="14" /> {{ c.corto }} <span class="muted">({{ c.unidad }})</span></td>
          <td class="small">{{ c.sensor }}</td><td>{{ c.direction > 0 ? 'rises' : 'falls' }}</td>
          <td class="num right">{{ nn(c.umbral_fijo, Math.max(1, c.decimales)) }}</td><td class="small muted">{{ c.clinical }}</td></tr></tbody>
      </table></div>
    </section>

    <section class="cols-2">
      <div class="panel">
        <h2 class="mb">Sources</h2>
        <ul class="refs small">
          <li v-for="e in ev" :key="e.id">{{ e.cita }} <span class="tiny muted">({{ e.tipo }}{{ e.en_propuesta ? '' : ', added' }})</span></li>
        </ul>
      </div>
      <div class="panel">
        <h2 class="mb">Limitations</h2>
        <ul class="small list">
          <li>Validated only with simulated data; no clinical validation.</li>
          <li>The browser PVT does not correct for device latency.</li>
          <li>Mood is a single question, not a validated psychological test.</li>
          <li>Cumulative dose is compared with what the simulated mission expects, not with NASA limits.</li>
          <li>Not built yet: a way for the Medical Officer to accept a new baseline after a legitimate adaptation.</li>
        </ul>
        <p class="tiny muted credits">Images: “The Blue Marble”, NASA/Apollo 17 crew, public domain; “Valles Marineris”, Viking Orbiter, NASA/USGS,
          public domain; videos “ISS Fly-Through to Cupola (8K)” and “Aurora Borealis from Space (4K)” (NASA); maps “Blue Marble Next Generation” (NASA) and “Mars Viking MDIM21” (NASA/JPL/USGS); all public domain, via Wikimedia Commons. Zero G Health is not affiliated with or endorsed by NASA.</p>
      </div>
    </section>
    <p class="tiny muted">Simulated data. Educational prototype, not a medical device.</p>
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
.hero { display: flex; gap: 24px; align-items: center; flex-wrap: wrap; background: var(--navy); border-color: var(--navy); color: #fff; }
.hero h2 { color: #fff; }
.hero p { color: #d5e2f3; }
.hero .formula { background: rgba(255, 255, 255, .1); color: #fff; }
.pics { display: flex; align-items: center; gap: 10px; }
.planet { border-radius: 50%; object-fit: cover; clip-path: circle(47%); }
.formula { background: var(--blue-soft); color: var(--blue); padding: 12px 14px; border-radius: 10px; font-size: 0.9rem; }
.mb { margin-bottom: 10px; }
.list { margin: 0; padding-left: 18px; display: grid; gap: 6px; line-height: 1.5; }
.refs { margin: 0; padding-left: 16px; display: grid; gap: 8px; line-height: 1.45; }
.credits { margin-top: 12px; }
</style>

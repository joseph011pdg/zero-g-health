<template>
  <section class="strip" aria-label="Mission trajectory">
    <figure class="body">
      <div class="globe earth" role="img" aria-label="Earth rotating (NASA Blue Marble map)"></div>
      <figcaption>Earth</figcaption>
    </figure>

    <div class="track">
      <div class="top">
        <span class="ttl">Trajectory <span class="date">{{ m.fecha }} · {{ Math.round(pct(s.day)) }}% of the journey</span></span>
        <span class="small link" :class="m.comunicacion.apagon ? 'off' : ''">
          <Icon :name="m.comunicacion.apagon ? 'signalOff' : 'satellite'" :size="14" />
          {{ linkText }}
        </span>
      </div>

      <div class="line-wrap">
        <div class="line"></div>
        <div class="done" :style="{ width: pct(s.day) + '%' }"></div>
        <div v-if="hasBlackout" class="blackout" :style="{ left: pct(m.apagon[0]) + '%', width: Math.max(pct(m.apagon[1]) - pct(m.apagon[0]), 1.5) + '%' }"
             :title="`No link with Earth: days ${m.apagon[0]}–${m.apagon[1]}`"></div>
        <span v-for="ms in milestones" :key="ms.day" class="tick" :class="{ past: s.day >= ms.day }" :style="{ left: pct(ms.day) + '%' }" :title="ms.label"></span>
        <div class="ship" :style="{ left: pct(s.day) + '%' }" aria-hidden="true">
          <span class="bubble">Day {{ s.day }}</span>
          <svg width="34" height="34" viewBox="0 0 34 34"><circle cx="17" cy="17" r="15.5" fill="#0b3d91" stroke="#ffffff" stroke-width="3" /><path d="M11 11.5l13 5.5-13 5.5 3-5.5z" fill="#ffffff" /></svg>
        </div>
        <input type="range" min="0" :max="m.dias - 1" :value="s.day" @change="s.setDay(+$event.target.value)"
               aria-label="Mission day (drag the ship)" class="range" />
      </div>

      <div class="ms-labels">
        <span v-for="ms in milestones" :key="ms.day" :style="{ left: pct(ms.day) + '%' }" :class="{ past: s.day >= ms.day }">{{ ms.label }}</span>
        <span v-if="hasBlackout" class="bl" :style="{ left: (pct(m.apagon[0]) + pct(m.apagon[1])) / 2 + '%' }">Blackout</span>
      </div>
    </div>

    <figure class="body">
      <div class="globe mars" role="img" aria-label="Mars rotating (NASA/USGS Viking mosaic)"></div>
      <figcaption>Mars</figcaption>
    </figure>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useStore, fmt, plural } from '../store.js'
import Icon from './Icon.vue'

const s = useStore()
const m = computed(() => s.mission)
const pct = (d) => (100 * d) / Math.max(m.value.dias - 1, 1)
const hasBlackout = computed(() => m.value.apagon[0] !== null && m.value.apagon[0] !== undefined)
// Hitos del plan de vuelo simulado (solo orientativos para la demo)
const milestones = computed(() => {
  const last = m.value.dias - 1
  return [{ day: 0, label: 'Departure' }, { day: Math.round(last / 2), label: 'Midway' }, { day: last, label: 'Arrival' }]
})
const linkText = computed(() => {
  const c = m.value.comunicacion
  const [a, b] = m.value.apagon
  if (c.simulado) return 'No link · simulated blackout'
  if (c.apagon) return `No link · back in ${plural(b - s.day + 1, 'day', 'days')}`
  if (hasBlackout.value && s.day < a) return `Messages take ${fmt(c.retraso_min, 1)} min · blackout in ${plural(a - s.day, 'day', 'days')}`
  return `Messages take ${fmt(c.retraso_min, 1)} min`
})
</script>

<style scoped>
/* Franja Tierra–Marte sobre blanco: borde fino, trayectoria en azul NASA, hitos con puntos */
.strip { display: flex; align-items: center; gap: 28px; padding: 18px 26px 14px; background: #fff; border: 1px solid var(--line-soft); border-radius: var(--radius); }
.body { margin: 0; display: grid; justify-items: center; gap: 8px; flex: none; }
.body figcaption { font-family: var(--serif); font-size: 0.95rem; color: var(--ink); font-weight: 600; margin: 0; }
/* Globos que giran: el planisferio real se desliza dentro del círculo (oeste → este) */
.globe { --size: 76px; width: var(--size); height: var(--size); border-radius: 50%; position: relative; overflow: hidden;
  background-repeat: repeat-x; background-size: calc(var(--size) * 2) var(--size); background-position: 0 0;
  animation: spin var(--period, 40s) linear infinite;
  box-shadow: 0 0 0 4px #fff, 0 0 0 5px var(--line-soft), 0 8px 18px rgba(11, 27, 51, .22); }
.globe::after { content: ''; position: absolute; inset: 0; border-radius: 50%;
  background: radial-gradient(circle at 32% 28%, rgba(255, 255, 255, .28) 0%, rgba(255, 255, 255, 0) 38%, rgba(0, 0, 0, 0) 55%, rgba(0, 0, 0, .55) 100%);
  box-shadow: inset -6px -4px 12px rgba(0, 0, 0, .35); }
.earth { --size: 76px; --period: 40s; background-image: url(/img/tierra-mapa.jpg); }
.mars { --size: 66px; --period: 52s; background-image: url(/img/marte-mapa.jpg); }
@keyframes spin { to { background-position: calc(var(--size) * 2) 0; } }
@media (prefers-reduced-motion: reduce) { .globe { animation: none; } }
.track { flex: 1; display: grid; gap: 6px; min-width: 0; }
.top { display: flex; justify-content: space-between; gap: 8px; align-items: baseline; }
.ttl { font-family: var(--serif); font-size: 1.35rem; font-weight: 600; color: var(--ink); }
.ttl .date { font-family: var(--sans); font-size: 0.8rem; font-weight: 400; color: var(--muted); margin-left: 10px; }
.link { display: inline-flex; align-items: center; gap: 6px; color: var(--blue); font-weight: 500; font-size: 0.86rem; }
.link.off { color: var(--red); font-weight: 600; }
.line-wrap { position: relative; height: 56px; margin-top: 4px; }
.line { position: absolute; top: 35px; left: 0; right: 0; height: 0; border-top: 2px dotted #b8c4d6; }
.done { position: absolute; top: 34px; left: 0; height: 4px; border-radius: 2px; background: var(--blue); }
.blackout { position: absolute; top: 29px; height: 14px; background: var(--red-soft); border: 1px solid #e3c194; border-radius: 3px; }
.tick { position: absolute; top: 30px; width: 12px; height: 12px; border-radius: 50%; background: #fff; border: 2px solid #b8c4d6; transform: translateX(-6px); }
.tick.past { border-color: var(--blue); background: var(--blue); }
.ship { position: absolute; top: 0; transform: translateX(-50%); display: grid; justify-items: center; pointer-events: none; transition: left .25s cubic-bezier(.16,1,.3,1); z-index: 1; }
.ship svg { margin-top: 1px; filter: drop-shadow(0 3px 6px rgba(11, 61, 145, .35)); }
.bubble { font-size: 0.74rem; font-weight: 600; color: #fff; background: var(--ink); padding: 1px 8px; border-radius: 2px; white-space: nowrap; margin-bottom: -1px; }
.range { position: absolute; inset: 0; width: 100%; opacity: 0; cursor: grab; margin: 0; z-index: 2; }
.range:active { cursor: grabbing; }
.line-wrap:focus-within .ship svg circle { stroke: var(--ink); }
.ms-labels { position: relative; height: 16px; }
.ms-labels span { position: absolute; transform: translateX(-50%); font-size: 0.74rem; color: var(--faint); white-space: nowrap; }
.ms-labels span:first-child { transform: none; }
.ms-labels span:nth-child(3) { transform: translateX(-100%); }
.ms-labels span.past { color: var(--blue); font-weight: 500; }
.ms-labels .bl { color: var(--red); font-weight: 600; }
@media (max-width: 640px) {
  .strip { gap: 12px; padding: 12px 14px; }
  .earth { --size: 46px; } .mars { --size: 40px; }
  .body figcaption { display: none; }
  .ms-labels span:nth-child(2) { display: none; }
  /* "Blackout" en una segunda fila para no montarse con "Arrival" */
  .ms-labels { height: 32px; }
  .ms-labels .bl { top: 16px; }
  .top { flex-wrap: wrap; }
  .ttl .date { display: none; }
  .ttl { font-size: 1.1rem; }
}
</style>

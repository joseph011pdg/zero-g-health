<template>
  <!-- Pantalla de inicio: una vez por sesión. Sirve también de pantalla de carga mientras despierta el servidor. -->
  <div class="splash" :class="{ out: leaving }" role="dialog" aria-modal="true" aria-labelledby="sp-title" @keydown.enter="enter" @keydown.esc="enter">
    <!-- Video de NASA (dominio público, "ISS Fly-Through to Cupola"): acercándose a la cúpula desde dentro.
         Distinto al de la portada. Bucle con fundido; foto fija si se pide reducir movimiento. -->
    <video v-if="!reduceMotion" class="bg" :class="{ dim: fading }" :src="videoSrc" poster="/img/bienvenida-poster.jpg"
           autoplay muted playsinline preload="auto" @timeupdate="softLoop" aria-hidden="true"></video>
    <img v-else class="bg" src="/img/bienvenida-poster.jpg" alt="" aria-hidden="true" />
    <div class="veil" aria-hidden="true"></div>
    <div class="center">
      <div class="logo-wrap">
        <svg class="mark" width="104" height="104" viewBox="0 0 84 84" aria-hidden="true">
          <rect x="2" y="2" width="80" height="80" fill="#0a1f44" stroke="rgba(255,255,255,.55)" stroke-width="1.5" />
          <text x="40" y="58" text-anchor="middle" class="mono">0G</text>
          <path class="cross" d="M60 18v10M55 23h10" stroke="#f2a93b" stroke-width="3.5" stroke-linecap="round" />
          <path class="base" d="M12 70h60" stroke="#ffffff" stroke-opacity=".6" stroke-width="2" />
        </svg>
      </div>
      <h1 id="sp-title" class="name">Zero G <em>Health</em></h1>
      <p class="lead-line">Every astronaut compared with their own baseline. On board, without Earth.</p>
      <div class="cta">
        <button ref="btn" class="enter" @click="enter" :disabled="!ready">
          {{ ready ? 'Enter mission' : 'Waking up the server…' }}
        </button>
        <p class="note">NASA Space Apps Challenge 2026. Simulated data, not a medical device.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'

const props = defineProps({ ready: Boolean })
const emit = defineEmits(['done'])
const leaving = ref(false)
const fading = ref(false)
//CALIDAD: 2560×1280 (desde el original 8K) en pantallas grandes, 1280×640 en celulares
const videoSrc = typeof window !== 'undefined' && window.innerWidth >= 900 ? '/img/bienvenida-hd.mp4' : '/img/bienvenida.mp4'
const reduceMotion = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
//BUCLE suave: fundido corto al final y vuelta al inicio (el último plano no coincide con el primero)
function softLoop(e) {
  const v = e.target
  if (fading.value || !v.duration || !isFinite(v.duration)) return
  if (v.currentTime >= v.duration - 0.7) {
    fading.value = true
    setTimeout(() => { v.currentTime = 0; v.play(); fading.value = false }, 450)
  }
}
const btn = ref(null)

function enter() {
  if (!props.ready || leaving.value) return
  leaving.value = true
  setTimeout(() => emit('done'), 260)
}
//Cuando la app está lista, el foco pasa al botón para entrar con Enter
watch(() => props.ready, async (r) => { if (r) { await nextTick(); btn.value?.focus() } })
onMounted(() => { if (props.ready) btn.value?.focus() })
</script>

<style scoped>
.splash { user-select: none; position: fixed; inset: 0; z-index: 100; background: var(--navy); color: #fff; display: grid; place-items: center; padding: 24px; overflow: hidden;
  transition: opacity 260ms var(--ease-out), transform 260ms var(--ease-out); }
.splash.out { opacity: 0; transform: translateY(-8px); }
/* FONDO: la foto entra con un acercamiento lento que se detiene (solo transform y opacidad) */
.bg { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 50%; animation: settle 1600ms var(--ease-out) both; transition: opacity 450ms ease; }
.bg.dim { opacity: .2; }
.veil { position: absolute; inset: 0; background:
  radial-gradient(ellipse 55% 45% at 50% 50%, rgba(10, 31, 68, .55) 0%, rgba(10, 31, 68, .3) 70%, rgba(10, 31, 68, .5) 100%); }
.name { text-shadow: 0 2px 18px rgba(6, 16, 32, .55); }
.lead-line { text-shadow: 0 1px 10px rgba(6, 16, 32, .8); }
/* RECUADRO de vidrio: negro translúcido con desenfoque, para que logo y texto contrasten sobre el video */
.center { position: relative; display: grid; justify-items: center; align-content: center; gap: 14px; text-align: center; width: min(640px, 100%); margin: 0 auto;
  padding: 36px 48px; border-radius: 18px; background: rgba(4, 8, 16, .52); border: 1px solid rgba(255, 255, 255, .18);
  -webkit-backdrop-filter: blur(12px) saturate(1.15); backdrop-filter: blur(12px) saturate(1.15);
  box-shadow: 0 24px 60px rgba(6, 16, 32, .35); animation: mark-in 520ms var(--ease-out) both; }
@media (max-width: 640px) { .center { padding: 28px 20px; border-radius: 14px; } }
.mono { font-family: var(--serif); font-weight: 600; font-size: 44px; fill: #ffffff; }
.mark { filter: drop-shadow(0 10px 30px rgba(6, 16, 32, .6)); }

/* ENTRADA: marca → cruz y línea base → nombre → texto → botón (escalonado) */
.mark { animation: mark-in 520ms var(--ease-out) both; }
.cross { transform-box: fill-box; transform-origin: center; animation: pop 360ms var(--ease-out) 380ms both; }
.base { transform-box: fill-box; transform-origin: left center; animation: draw 480ms var(--ease-out) 260ms both; }
.name { font-family: var(--serif); font-size: clamp(2.2rem, 7vw, 3.6rem); color: #fff; letter-spacing: -0.02em; margin-top: 4px; animation: rise 420ms var(--ease-out) 360ms both; }
.name em { font-style: normal; color: #f2c27a; }
.lead-line { color: #ffffff; font-weight: 500; font-size: 1.06rem; line-height: 1.5; text-wrap: balance; max-width: 46ch; animation: rise 420ms var(--ease-out) 460ms both; }
.cta { display: grid; justify-items: center; gap: 12px; margin-top: 10px; animation: rise 420ms var(--ease-out) 560ms both; }
.enter { background: var(--navy); color: #fff; border: 1px solid rgba(255, 255, 255, .55); border-radius: var(--radius-sm); padding: 12px 26px; font: inherit; font-weight: 600; font-size: 1rem; cursor: pointer; min-height: 46px;
  transition: transform 140ms var(--ease-out), background-color 150ms ease, opacity 150ms ease; }
.enter:active { transform: scale(0.97); }
.enter:disabled { opacity: .7; cursor: progress; }
@media (hover: hover) and (pointer: fine) { .enter:not(:disabled):hover { background: #13306a; } }
/* LETRA pequeña legible: blanca, algo más grande y con sombra suave para separarla del video */
.note { font-size: 0.84rem; font-weight: 500; color: rgba(255, 255, 255, .92); letter-spacing: 0.01em; text-shadow: 0 1px 8px rgba(6, 16, 32, .75); }

@keyframes mark-in { from { opacity: 0; transform: scale(0.94); } to { opacity: 1; transform: scale(1); } }
@keyframes pop { from { opacity: 0; transform: scale(0.6); } to { opacity: 1; transform: scale(1); } }
@keyframes draw { from { transform: scaleX(0); } to { transform: scaleX(1); } }
@keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes settle { from { opacity: 0; transform: scale(1.06); } to { opacity: 1; transform: scale(1); } }

/* Movimiento reducido: solo aparece con opacidad, sin desplazamientos ni estrellas animadas */
@media (prefers-reduced-motion: reduce) {
  .mark, .cross, .base, .name, .lead-line, .cta { animation: fade 300ms ease both; }
  .bg { animation: fade 400ms ease both; }
  .splash.out { transform: none; }
}
@keyframes fade { from { opacity: 0; } to { opacity: 1; } }
</style>

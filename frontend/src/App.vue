<template>
  <header class="top no-print">
    <div class="mast">
      <router-link to="/" class="word" aria-label="Zero G Health, home">
        <Logo :size="30" inverse label="" />Zero G <em>Health</em>
      </router-link>

      <nav class="nav" aria-label="Sections">
        <router-link to="/" :class="{ on: (route.path === '/' && route.hash !== '#alerts') || route.path.startsWith('/crew') }">Crew</router-link>
        <router-link :to="{ path: '/', hash: '#alerts' }" :class="{ on: route.path === '/' && route.hash === '#alerts' }">Alerts</router-link>
        <router-link to="/reports" :class="{ on: route.path === '/reports' }">Reports<span v-if="s.pendingReports" class="count">{{ s.pendingReports }}</span></router-link>
        <router-link to="/lab" :class="{ on: route.path.startsWith('/lab') }">Laboratory</router-link>
      </nav>

      <div class="edition" v-if="s.mission">
        <div class="ed-line">
          <button class="step" @click="s.advance(-1)" :disabled="s.day <= 0" aria-label="Previous day"><Icon name="prev" :size="11" /></button>
          <span><span class="pre">Onboard health report · </span><b>Day {{ s.day }}<span class="of"> of {{ s.mission.dias - 1 }}</span></b></span>
          <button class="step" @click="s.advance(1)" :disabled="s.day >= s.mission.dias - 1" aria-label="Next day"><Icon name="next" :size="11" /></button>
        </div>
        <div class="ed-sub">
          <span :class="{ off: link.apagon }">{{ link.apagon ? 'No link with Earth' : `Earth: ${fmt(link.retraso_min, 1)} min` }}</span>
          <span class="sys" :class="{ off: s.online === false }">{{ s.online === false ? 'local engine stopped' : 'local system running' }}</span>
        </div>
      </div>

      <div class="role" role="group" aria-label="Role">
        <button :aria-pressed="s.role === 'astronauta'" @click="s.setRole('astronauta')" aria-label="Astronaut role"><span class="lbl">Astronaut</span><Icon class="ico" name="user" :size="14" /></button>
        <button :aria-pressed="s.role === 'oficial'" @click="s.setRole('oficial')" aria-label="Medical Officer role"><span class="lbl">Medical Officer</span><Icon class="ico" name="stethoscope" :size="14" /></button>
      </div>
      <button class="demo-btn" @click="s.demo = !s.demo" :aria-expanded="s.demo" aria-label="Guided demo"><Icon name="compass" :size="15" /><span class="lbl">Demo</span></button>
    </div>
  </header>

  <div v-if="s.publico" class="public no-print" role="note">
    <span><b>Public demo</b> · simulated data</span>
    <button class="reset" @click="s.run(() => s.resetDemo(), 'Demo reset')">Reset demo</button>
  </div>

  <transition name="fade"><GuidedDemo v-if="s.demo" @close="s.demo = false" /></transition>

  <main>
    <div v-if="s.online === false" class="page">
      <div class="notice err"><Icon name="server" :size="18" />
        <div><strong>The local engine is not responding.</strong> Run <code>.\scripts\start.ps1</code> in the project folder; it will retry on its own.</div>
      </div>
    </div>
    <router-view v-else-if="s.mission" v-slot="{ Component }">
      <transition name="fade" mode="out-in"><component :is="Component" /></transition>
    </router-view>
    <div v-else class="page waking" role="status">
      <div class="skeleton" style="height: 220px"></div>
      <p class="small muted">Waking up the server… The first visit can take up to a minute (free hosting).</p>
    </div>
  </main>

  <Splash v-if="splash" :ready="!!s.mission || s.online === false" @done="closeSplash" />

  <div class="toasts" aria-live="polite">
    <div v-for="t in s.toasts" :key="t.id" class="toast" :class="t.kind">{{ t.msg }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useStore, fmt } from './store.js'
import Icon from './components/Icon.vue'
import GuidedDemo from './components/GuidedDemo.vue'
import Logo from './components/Logo.vue'
import Splash from './components/Splash.vue'

const s = useStore()
const route = useRoute()
const link = computed(() => s.mission?.comunicacion || {})
//INICIO: pantalla de bienvenida una vez por sesión
function seen() { try { return sessionStorage.getItem('zg.splash') === '1' } catch { return false } }
const splash = ref(!seen())
function closeSplash() { splash.value = false; try { sessionStorage.setItem('zg.splash', '1') } catch { /* solo memoria */ } }
onMounted(() => s.init())
</script>

<style scoped>
/* Cabecera en azul NASA con texto blanco */
.top { background: var(--navy); color: #fff; position: sticky; top: 0; z-index: 20; box-shadow: 0 2px 10px rgba(11, 27, 51, .18); }
.mast { max-width: 1240px; margin: 0 auto; padding: 14px 40px; display: flex; align-items: center; gap: 30px; }
.word { display: flex; align-items: center; gap: 10px; font-family: var(--serif); font-size: 1.6rem; font-weight: 600; letter-spacing: -0.01em; color: #fff; flex: none; }
.word em { font-style: normal; color: #f2c27a; }
.word { white-space: nowrap; }
.nav { display: flex; gap: 24px; }
.nav a { color: #c9d8f2; font-weight: 500; padding: 4px 0; border-bottom: 2px solid transparent; display: inline-flex; align-items: center; gap: 6px; }
.nav a:hover { color: #fff; }
.nav a.on { color: #fff; border-bottom-color: #fff; }
.count { background: #fff; color: var(--navy); font-size: 0.7rem; font-weight: 600; padding: 0 6px; border-radius: 2px; line-height: 1.5; }
.edition { margin-left: auto; text-align: right; font-size: 0.82rem; color: #c9d8f2; line-height: 1.4; }
.edition b { color: #fff; }
.ed-line { display: flex; align-items: center; gap: 6px; justify-content: flex-end; }
.ed-sub { display: flex; gap: 10px; justify-content: flex-end; }
.ed-sub .off { color: #ffd9a8; font-weight: 600; }
.sys::before { content: ''; display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #7ee2a8; margin-right: 5px; vertical-align: 1px; }
.sys.off::before { background: #ffb366; }
.step { width: 22px; height: 22px; border: 1px solid rgba(255, 255, 255, .5); background: transparent; color: #fff; display: grid; place-items: center; cursor: pointer; border-radius: 2px; }
.step:hover:not(:disabled) { border-color: #fff; background: rgba(255, 255, 255, .12); }
.step:disabled { opacity: .35; cursor: not-allowed; }
.role { display: flex; border: 1px solid #fff; flex: none; }
.role button { border: 0; background: transparent; padding: 7px 12px; font-size: 0.82rem; font-weight: 600; color: #fff; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; min-height: 34px; }
.role button[aria-pressed='true'] { background: #fff; color: var(--navy); }
.role .ico { display: none; }
.demo-btn { border: 0; background: none; color: #fff; font-weight: 600; font-size: 0.86rem; display: inline-flex; align-items: center; gap: 6px; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; }
.top :focus-visible { outline-color: #fff; }
/* Franja de demo: continúa el azul marino de la cabecera */
.public { background: #13306a; color: #d5e2f3; padding: 5px max(16px, calc((100% - 1160px) / 2)); font-size: 0.8rem; display: flex; gap: 12px; align-items: center; justify-content: space-between; }
.public b { color: #fff; font-weight: 600; }
.public .reset { background: none; border: 0; color: #fff; font-weight: 600; text-decoration: underline; text-underline-offset: 3px; cursor: pointer; padding: 2px 0; font: inherit; font-weight: 600; }
.waking p { text-align: center; }
.toasts { position: fixed; bottom: 18px; right: 18px; display: grid; gap: 8px; z-index: 70; }
.toast { background: #fff; border: 1px solid var(--ink); padding: 10px 14px; font-size: 0.88rem; max-width: 380px; box-shadow: 0 8px 24px rgba(11, 27, 51, .14); }
.toast.err { border-color: var(--red); color: #6e3b00; }
code { font-family: var(--mono); background: #fff; padding: 1px 6px; }
@media (max-width: 1100px) { .ed-sub { display: none; } }
@media (max-width: 900px) {
  .mast { flex-wrap: wrap; gap: 10px 18px; padding: 12px 16px; }
  .nav { order: 3; width: 100%; gap: 18px; overflow-x: auto; }
  .edition { margin-left: auto; }
  .role .lbl, .demo-btn .lbl { display: none; }
  .role .ico { display: block; }
}
@media (max-width: 640px) {
  /* Cabecera compacta: marca + día en una fila; rol, demo y menú en otra */
  .mast { gap: 8px 12px; padding: 10px 16px; }
  .ed-line .pre { display: none; }
  .demo-btn { display: none; }
  .word { font-size: 1.3rem; }
  .word img { width: 24px; height: 24px; }
  .role button { padding: 6px 10px; min-height: 32px; }
  .nav { gap: 12px; justify-content: space-between; }
  .nav a { font-size: 0.88rem; }
  .public { font-size: 0.76rem; }
}
@media (max-width: 420px) {
  .word { font-size: 1.08rem; gap: 7px; }
  .word :deep(svg) { width: 24px; height: 24px; }
  .mast { gap: 8px 8px; }
  .ed-line { gap: 4px; }
  .ed-line > span { font-size: 0.74rem; }
  .ed-line .of { display: none; }
  .role button { padding: 6px 8px; }
}
</style>

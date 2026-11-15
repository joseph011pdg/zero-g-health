<template>
  <header class="top no-print">
    <div class="mast">
      <router-link to="/" class="word" aria-label="BASAL, inicio">
        <img src="/icon.svg" alt="" width="28" height="28" />BASAL
      </router-link>

      <nav class="nav" aria-label="Secciones">
        <router-link to="/" :class="{ on: (route.path === '/' && route.hash !== '#alarmas') || route.path.startsWith('/persona') }">Tripulación</router-link>
        <router-link :to="{ path: '/', hash: '#alarmas' }" :class="{ on: route.path === '/' && route.hash === '#alarmas' }">Alarmas</router-link>
        <router-link to="/tierra" :class="{ on: route.path === '/tierra' }">Reportes<span v-if="s.pendingReports" class="count">{{ s.pendingReports }}</span></router-link>
        <router-link to="/laboratorio" :class="{ on: route.path.startsWith('/laboratorio') }">Laboratorio</router-link>
      </nav>

      <div class="edition" v-if="s.mission">
        <div class="ed-line">
          <button class="step" @click="s.advance(-1)" :disabled="s.day <= 0" aria-label="Día anterior"><Icon name="prev" :size="11" /></button>
          <span>Informe de salud a bordo · <b>Día {{ s.day }} de {{ s.mission.dias - 1 }}</b></span>
          <button class="step" @click="s.advance(1)" :disabled="s.day >= s.mission.dias - 1" aria-label="Día siguiente"><Icon name="next" :size="11" /></button>
        </div>
        <div class="ed-sub">
          <span :class="{ off: link.apagon }">{{ link.apagon ? 'Sin enlace con la Tierra' : `Tierra: ${fmt(link.retraso_min, 1)} min` }}</span>
          <span class="sys" :class="{ off: s.online === false }">{{ s.online === false ? 'motor local detenido' : 'sistema local operativo' }}</span>
        </div>
      </div>

      <div class="role" role="group" aria-label="Rol">
        <button :aria-pressed="s.role === 'astronauta'" @click="s.setRole('astronauta')"><span class="lbl">Astronauta</span><Icon class="ico" name="user" :size="14" /></button>
        <button :aria-pressed="s.role === 'oficial'" @click="s.setRole('oficial')"><span class="lbl">Oficial médico</span><Icon class="ico" name="stethoscope" :size="14" /></button>
      </div>
      <button class="demo-btn" @click="s.demo = !s.demo" :aria-expanded="s.demo" aria-label="Demo guiada"><Icon name="compass" :size="15" /><span class="lbl">Demo</span></button>
    </div>
  </header>

  <div v-if="s.publico" class="public no-print" role="note">
    <span>Demo pública · datos simulados · lo que haga aquí queda solo en este navegador</span>
    <button class="reset" @click="s.run(() => s.resetDemo(), 'Demo restablecida')">Restablecer demo</button>
  </div>

  <transition name="fade"><GuidedDemo v-if="s.demo" @close="s.demo = false" /></transition>

  <main>
    <div v-if="s.online === false" class="page">
      <div class="notice err"><Icon name="server" :size="18" />
        <div><strong>El motor local no responde.</strong> Ejecute <code>.\scripts\start.ps1</code> en la carpeta del proyecto; se reintentará solo.</div>
      </div>
    </div>
    <router-view v-else-if="s.mission" v-slot="{ Component }">
      <transition name="fade" mode="out-in"><component :is="Component" /></transition>
    </router-view>
    <div v-else class="page waking" role="status">
      <div class="skeleton" style="height: 220px"></div>
      <p class="small muted">Despertando el servidor… La primera visita puede tardar hasta un minuto (alojamiento gratuito).</p>
    </div>
  </main>

  <div class="toasts" aria-live="polite">
    <div v-for="t in s.toasts" :key="t.id" class="toast" :class="t.kind">{{ t.msg }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useStore, fmt } from './store.js'
import Icon from './components/Icon.vue'
import GuidedDemo from './components/GuidedDemo.vue'

const s = useStore()
const route = useRoute()
const link = computed(() => s.mission?.comunicacion || {})
onMounted(() => s.init())
</script>

<style scoped>
/* Cabecera en azul NASA con texto blanco */
.top { background: var(--navy); color: #fff; position: sticky; top: 0; z-index: 20; box-shadow: 0 2px 10px rgba(11, 27, 51, .18); }
.mast { max-width: 1240px; margin: 0 auto; padding: 14px 40px; display: flex; align-items: center; gap: 30px; }
.word { display: flex; align-items: center; gap: 10px; font-family: var(--serif); font-size: 1.6rem; font-weight: 600; letter-spacing: -0.01em; color: #fff; flex: none; }
.word img { border-radius: 50%; }
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
.public { max-width: 1160px; margin: 12px auto 0; padding: 6px 12px; font-size: 0.8rem; color: var(--navy); background: var(--blue-soft); display: flex; gap: 12px; align-items: center; justify-content: space-between; flex-wrap: wrap; }
.public .reset { background: none; border: 0; color: var(--blue); font-weight: 600; text-decoration: underline; text-underline-offset: 3px; cursor: pointer; padding: 4px 0; font: inherit; font-weight: 600; }
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
@media (max-width: 480px) { .ed-line > span { font-size: 0.78rem; } .word { font-size: 1.3rem; } .nav { gap: 12px; justify-content: space-between; } .nav a { font-size: 0.88rem; } }
</style>

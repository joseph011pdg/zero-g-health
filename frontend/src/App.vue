<template>
  <header class="top no-print">
    <div class="bar">
      <router-link to="/" class="brand" aria-label="BASAL, inicio">
        <img src="/icon.svg" alt="" width="30" height="30" />
        <div>
          <div class="name">BASAL</div>
          <div class="tiny muted">Monitoreo de salud autónomo</div>
        </div>
      </router-link>

      <div v-if="s.mission" class="mission">
        <div class="cell hide-md">
          <span class="label">Misión</span>
          <span class="small strong ell" :title="s.mission.nombre">{{ s.mission.nombre }}</span>
        </div>
        <div class="cell">
          <span class="label">Día · fecha sim.</span>
          <span class="small strong mono">D{{ String(s.mission.dia).padStart(3, '0') }} · {{ s.mission.fecha }}</span>
        </div>
        <div class="cell hide-sm">
          <span class="label">Astronauta</span>
          <span class="small strong ell">{{ s.selectedAstro?.nombre || '—' }}</span>
        </div>
        <div class="cell link" :class="{ off: s.mission.comunicacion.apagon }" :title="s.mission.comunicacion.nota">
          <span class="label">Enlace con la Tierra</span>
          <span class="small strong row g4">
            <Icon :name="s.mission.comunicacion.apagon ? 'signalOff' : 'satellite'" :size="14" />
            <template v-if="s.mission.comunicacion.apagon">SIN ENLACE</template>
            <template v-else>Diferido · {{ s.mission.comunicacion.retraso_min }} min</template>
          </span>
        </div>
        <div class="cell sys" :class="{ off: s.online === false }">
          <span class="label">Sistema local</span>
          <span class="small strong row g4"><Icon name="server" :size="14" />{{ s.online === false ? 'Sin motor' : 'Operativo' }}</span>
        </div>
      </div>
      <button class="btn sm blue" @click="demo = !demo" :aria-expanded="demo"><Icon name="compass" :size="14" /> Demo guiada</button>
    </div>

    <nav class="nav" aria-label="Pantallas">
      <router-link v-for="r in NAV" :key="r.to" :to="r.to" class="navlink" :class="{ on: isActive(r) }">
        <span class="mono n">{{ r.n }}</span><Icon :name="r.icon" :size="15" /><span>{{ r.label }}</span>
      </router-link>
      <div v-if="s.mission" class="day-ctl">
        <button class="btn sm ghost" @click="s.advance(-1)" :disabled="s.day <= 0" aria-label="Día anterior"><Icon name="prev" :size="13" /></button>
        <input type="range" min="0" :max="s.mission.dias - 1" v-model.number="day" @change="s.setDay(day)" aria-label="Día de misión" />
        <button class="btn sm ghost" @click="s.advance(1)" :disabled="s.day >= s.mission.dias - 1" aria-label="Día siguiente"><Icon name="next" :size="13" /></button>
      </div>
    </nav>
  </header>

  <div v-if="s.publico" class="public no-print" role="note">
    <Icon name="info" :size="14" /> Demo pública en línea · datos sintéticos · el estado es compartido entre visitantes.
    El producto real funciona sin Internet en el equipo de a bordo.
  </div>

  <transition name="fade"><GuidedDemo v-if="demo" @close="demo = false" /></transition>

  <main>
    <div v-if="s.online === false" class="page">
      <div class="notice err"><Icon name="server" :size="18" />
        <div><strong>Motor local no disponible.</strong> La interfaz funciona sin Internet, pero necesita el backend en este
          equipo. Abra PowerShell en la carpeta del proyecto y ejecute <code>.\scripts\start.ps1</code>.
          Se reintentará automáticamente. <span class="muted">({{ s.error }})</span></div>
      </div>
    </div>
    <router-view v-else-if="s.mission" v-slot="{ Component }">
      <transition name="fade" mode="out-in"><component :is="Component" /></transition>
    </router-view>
    <div v-else class="page"><div class="skeleton" style="height: 220px"></div></div>
  </main>

  <div class="toasts" aria-live="polite">
    <div v-for="t in s.toasts" :key="t.id" class="toast" :class="t.kind">{{ t.msg }}</div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useStore } from './store.js'
import Icon from './components/Icon.vue'
import GuidedDemo from './components/GuidedDemo.vue'

const NAV = [
  { n: '01', to: '/', label: 'Misión y oficial médico', icon: 'users' },
  { n: '02', to: '/salud', label: 'Salud y alertas', icon: 'heart', prefix: '/salud' },
  { n: '03', to: '/registro', label: 'Check-in y PVT', icon: 'clipboard' },
  { n: '04', to: '/simulador', label: 'Simulador', icon: 'cpu' },
  { n: '05', to: '/validacion', label: 'Validation Lab', icon: 'flask' },
  { n: '06', to: '/reportes', label: 'Reportes y ciencia', icon: 'book' }
]
const s = useStore()
const route = useRoute()
const day = ref(0)
const demo = ref(false)
onMounted(() => s.init())
watch(() => s.mission?.dia, (d) => { if (d !== undefined) day.value = d })
const isActive = (r) => (r.prefix ? route.path.startsWith(r.prefix) : route.path === r.to)
</script>

<style scoped>
.top { position: sticky; top: 0; z-index: 20; background: rgba(8, 21, 37, 0.9); backdrop-filter: blur(12px); border-bottom: 1px solid var(--line-soft); }
.bar { max-width: 1320px; margin: 0 auto; padding: 10px 24px; display: flex; align-items: center; gap: 18px; }
.brand { display: flex; align-items: center; gap: 10px; flex: none; }
.name { font-weight: 800; letter-spacing: 0.2em; font-size: 1rem; }
.mission { flex: 1; display: flex; gap: 6px; min-width: 0; overflow: hidden; }
.cell { display: grid; gap: 1px; padding: 5px 12px; border-left: 1px solid var(--line-soft); min-width: 0; }
.cell .label { font-size: 0.6rem; }
.ell { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 230px; }
.g4 { gap: 5px; }
.link { color: var(--ok); }
.link.off { color: #ff9a9f; background: rgba(231,106,112,.1); border-radius: 8px; animation: pulse 2s infinite; }
.sys { color: var(--ok); }
.sys.off { color: #ff9a9f; }
@keyframes pulse { 50% { background: rgba(231,106,112,.2); } }
.nav { max-width: 1320px; margin: 0 auto; padding: 0 24px 8px; display: flex; gap: 2px; align-items: center; overflow-x: auto; }
.navlink { display: inline-flex; align-items: center; gap: 7px; padding: 7px 12px; border-radius: 8px; color: var(--muted); font-weight: 600; font-size: 0.86rem; white-space: nowrap; }
.navlink:hover { color: var(--text); background: var(--surface); }
.navlink.on { color: var(--text); background: var(--surface-2); box-shadow: inset 0 -2px 0 var(--mars); }
.navlink .n { font-size: 0.66rem; color: var(--faint); }
.day-ctl { margin-left: auto; display: flex; align-items: center; gap: 4px; min-width: 220px; }
.public { max-width: 1320px; margin: 10px auto 0; padding: 7px 14px; display: flex; gap: 8px; align-items: center; font-size: 0.8rem; color: #bfe6fa; background: rgba(84,184,232,.08); border: 1px solid rgba(84,184,232,.3); border-radius: 8px; width: calc(100% - 48px); }
.toasts { position: fixed; bottom: 18px; right: 18px; display: grid; gap: 8px; z-index: 50; }
.toast { background: var(--surface-3); border: 1px solid var(--line); border-left: 3px solid var(--ok); padding: 10px 14px; border-radius: 8px; font-size: 0.86rem; max-width: 380px; box-shadow: 0 10px 30px rgba(0,0,0,.5); }
.toast.err { border-left-color: var(--red); }
code { font-family: var(--mono); background: var(--bg-2); padding: 1px 6px; border-radius: 4px; }
@media (max-width: 1100px) { .hide-sm { display: none; } }
@media (max-width: 960px) { .hide-md { display: none; } }
@media (max-width: 800px) { .mission { display: none; } .bar { justify-content: space-between; } .day-ctl { min-width: 160px; } }
</style>

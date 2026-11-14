<template>
  <article class="panel alert edge" :class="a.nivel">
    <header class="row between wrap">
      <div class="row">
        <LevelBadge :level="a.nivel" />
        <h3>{{ a.titulo }}</h3>
      </div>
      <div class="row tiny muted">
        <span class="mono">{{ a.id }}</span>
        <span class="state" :class="a.estado">{{ STATE_LABEL[a.estado] || a.estado }}</span>
      </div>
    </header>

    <div class="q">
      <div class="label">1 · Qué cambió</div>
      <p class="small">{{ a.que_cambio }}</p>
    </div>

    <div class="q">
      <div class="label">2 · Cuánto</div>
      <div class="table-wrap">
        <table class="table mini">
          <thead><tr><th>Indicador</th><th>Hoy</th><th>Línea base</th><th>Cambio</th><th>z</th><th>Datos 14 d</th></tr></thead>
          <tbody>
            <tr v-for="c in a.cuanto" :key="c.indicador">
              <td>{{ c.nombre }}</td>
              <td class="num strong">{{ c.valor }} <span class="muted">{{ c.unidad }}</span></td>
              <td class="num">{{ c.linea_base }}</td>
              <td class="num">{{ signed(c.diferencia, 2) }} <span class="muted" v-if="c.diferencia_pct !== null">({{ signed(c.diferencia_pct, 0) }} %)</span></td>
              <td class="num strong" :class="'c-' + c.nivel">{{ c.z }}</td>
              <td class="num">{{ c.calidad_14d_pct }} %</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <details class="q" :open="expanded">
      <summary class="label">3 · Cómo se detectó</summary>
      <p class="small muted how">{{ a.como }}</p>
    </details>

    <div class="q">
      <div class="label">4 · Seguimiento sugerido</div>
      <ol class="small todo">
        <li v-for="(x, i) in a.acciones" :key="i" :class="{ esc: x.includes('oficial médico') }">{{ x }}</li>
      </ol>
    </div>

    <details class="q" :open="expanded">
      <summary class="label">5 · Fuente y nivel de evidencia</summary>
      <ul class="ev">
        <li v-for="e in a.evidencia" :key="e.id" class="small">
          <span>{{ e.cita }}</span>
          <div class="tiny muted"><span class="tag">{{ e.tipo }}</span> Nivel: {{ e.nivel }}</div>
        </li>
      </ul>
    </details>

    <div v-if="a.fiabilidad !== 'normal'" class="notice warn small"><Icon name="info" /> Fiabilidad {{ a.fiabilidad }} ({{ a.calidad_datos_pct }} % de datos en 14 días).</div>
    <p class="tiny faint">{{ a.aviso }}</p>

    <footer v-if="reviewable" class="review no-print">
      <input class="input" v-model="nota" placeholder="Nota del oficial médico (opcional)" maxlength="500" />
      <div class="row wrap">
        <button class="btn sm" @click="review('revisada')"><Icon name="check" :size="14" /> Revisada</button>
        <button class="btn sm danger" @click="review('escalada')"><Icon name="stethoscope" :size="14" /> Escalar</button>
        <button class="btn sm ghost" @click="review('descartada')">Descartar</button>
        <button v-if="a.estado !== 'pendiente'" class="btn sm ghost" @click="review('pendiente')">Reabrir</button>
      </div>
      <p v-if="a.nota" class="tiny muted">Nota guardada: “{{ a.nota }}”</p>
    </footer>
  </article>
</template>

<script setup>
import { ref } from 'vue'
import Icon from './Icon.vue'
import LevelBadge from './LevelBadge.vue'
import { api, useStore, signed, STATE_LABEL } from '../store.js'

const props = defineProps({ a: Object, reviewable: { type: Boolean, default: true }, expanded: Boolean })
const emit = defineEmits(['changed'])
const s = useStore()
const nota = ref(props.a.nota || '')

async function review(estado) {
  const r = await s.run(() => api(`/alerts/${encodeURIComponent(props.a.id)}`, { method: 'PATCH', body: { estado, nota: nota.value || null } }),
    `Alerta marcada como ${STATE_LABEL[estado].toLowerCase()}`)
  emit('changed', r)
}
</script>

<style scoped>
.alert { display: grid; gap: 10px; padding: 14px 16px; }
.alert h3 { font-size: 0.98rem; }
.q { display: grid; gap: 4px; }
.q p { line-height: 1.5; }
summary { cursor: pointer; list-style: none; }
summary::before { content: '▸ '; }
details[open] summary::before { content: '▾ '; }
.how { font-family: var(--mono); font-size: 0.76rem; line-height: 1.55; margin-top: 4px; }
.todo { margin: 2px 0 0; padding-left: 20px; line-height: 1.55; }
.todo li.esc { color: #ffc2c5; font-weight: 600; }
.ev { margin: 4px 0 0; padding-left: 16px; display: grid; gap: 6px; }
.mini td, .mini th { padding: 5px 8px; }
.state { font-family: var(--mono); text-transform: uppercase; letter-spacing: .06em; padding: 2px 7px; border-radius: 5px; border: 1px solid var(--line); }
.state.revisada { color: var(--ok); border-color: rgba(87,199,154,.4); }
.state.escalada { color: #ff9a9f; border-color: rgba(231,106,112,.5); }
.state.descartada { color: var(--gray); }
.review { display: grid; gap: 8px; border-top: 1px solid var(--line-soft); padding-top: 10px; }
</style>

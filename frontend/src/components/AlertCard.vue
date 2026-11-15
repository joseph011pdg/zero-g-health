<template>
  <article class="alert edge" :class="a.nivel">
    <header class="row between wrap">
      <div class="row">
        <LevelBadge :level="a.nivel" />
        <h3>{{ a.titulo }}</h3>
      </div>
      <span class="state" :class="a.estado">{{ STATE_LABEL[a.estado] || a.estado }}</span>
    </header>

    <ul class="todo">
      <li v-for="(x, i) in a.acciones" :key="i" :class="{ esc: x.includes('oficial médico') }">
        <Icon :name="x.includes('oficial médico') ? 'stethoscope' : 'check'" :size="15" />{{ x }}
      </li>
    </ul>

    <details :open="expanded">
      <summary><Icon name="info" :size="14" /> ¿Por qué?</summary>
      <div class="why">
        <p class="small">{{ a.que_cambio }}</p>
        <div class="table-wrap">
          <table class="table mini">
            <thead><tr><th>Indicador</th><th class="right">Hoy</th><th class="right">Su normal</th><th class="right">Cambio</th><th class="right">z</th></tr></thead>
            <tbody>
              <tr v-for="c in a.cuanto" :key="c.indicador">
                <td>{{ c.nombre }}</td>
                <td class="num right strong">{{ c.valor }} <span class="muted">{{ c.unidad }}</span></td>
                <td class="num right">{{ c.linea_base }}</td>
                <td class="num right">{{ signed(c.diferencia, 2) }}<span class="muted" v-if="c.diferencia_pct !== null"> ({{ signed(c.diferencia_pct, 0) }} %)</span></td>
                <td class="num right strong" :class="'c-' + c.nivel">{{ c.z }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="tiny muted how">{{ a.como }}</p>
        <ul class="ev">
          <li v-for="e in a.evidencia" :key="e.id" class="tiny"><span>{{ e.cita }}</span> <span class="muted">· {{ e.tipo }}. {{ e.nivel }}.</span></li>
        </ul>
        <p v-if="a.fiabilidad !== 'normal'" class="tiny c-amarillo">Fiabilidad {{ a.fiabilidad }} ({{ a.calidad_datos_pct }} % de datos en 14 días).</p>
        <p class="tiny faint">{{ a.aviso }}</p>
      </div>
    </details>

    <p v-if="!canReview" class="ack small" :class="a.estado === 'pendiente' ? 'pend' : 'done'">
      <Icon :name="a.estado === 'pendiente' ? 'clock' : 'check'" :size="14" />
      <template v-if="a.estado === 'pendiente'">{{ a.nivel === 'rojo' ? 'La oficial médica ha sido avisada.' : 'Aviso para vigilar: repita la medición.' }}</template>
      <template v-else>{{ STATE_LABEL[a.estado] }}<span v-if="a.revisor"> por {{ a.revisor }}</span><span v-if="a.revisado_dia !== null && a.revisado_dia !== undefined"> · día {{ a.revisado_dia }}</span><span v-if="a.nota">: “{{ a.nota }}”</span></template>
    </p>

    <footer v-if="canReview" class="review no-print">
      <p v-if="a.estado !== 'pendiente'" class="tiny muted">{{ STATE_LABEL[a.estado] }}<span v-if="a.revisor"> por {{ a.revisor }}</span><span v-if="a.revisado_dia !== null && a.revisado_dia !== undefined"> · día {{ a.revisado_dia }}</span><span v-if="a.nota"> · “{{ a.nota }}”</span></p>
      <input class="input" v-model="nota" placeholder="Nota (opcional)" maxlength="500" aria-label="Nota del oficial médico" />
      <div class="row wrap">
        <button class="btn sm primary" @click="review('reconocida')"><Icon name="check" :size="14" /> Reconocer</button>
        <button class="btn sm" @click="review('pospuesta')"><Icon name="clock" :size="14" /> Posponer 24 h</button>
        <button class="btn sm danger" @click="review('escalada')">Escalar</button>
        <button class="btn sm ghost" @click="review('revisada')">Resuelta</button>
        <button v-if="a.estado !== 'pendiente'" class="btn sm ghost" @click="review('pendiente')">Reabrir</button>
      </div>
    </footer>
  </article>
</template>

<script setup>
import { ref, computed } from 'vue'
import Icon from './Icon.vue'
import LevelBadge from './LevelBadge.vue'
import { api, useStore, signed, STATE_LABEL } from '../store.js'

const props = defineProps({ a: Object, reviewable: { type: Boolean, default: undefined }, expanded: Boolean })
const emit = defineEmits(['changed'])
const s = useStore()
const nota = ref(props.a.nota || '')
// Por defecto, solo el rol de oficial médico ve los controles de revisión
const canReview = computed(() => (props.reviewable === undefined ? s.isOfficer : props.reviewable))

async function review(estado) {
  const r = await s.run(() => api(`/alerts/${encodeURIComponent(props.a.id)}`, { method: 'PATCH', body: { estado, nota: nota.value || null, revisor: s.officer ? s.officer.nombre : 'Oficial médico' } }),
    `Alerta: ${STATE_LABEL[estado].toLowerCase()}`)
  emit('changed', r)
}
</script>

<style scoped>
.alert { display: grid; gap: 10px; padding: 16px 0; background: transparent; border-bottom: 1px solid var(--line-soft); }
.alert h3 { font-size: 1.15rem; }
.todo { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 8px 18px; }
.todo li { display: inline-flex; align-items: center; gap: 6px; font-size: 0.9rem; color: var(--text-2); }
.todo li :deep(svg) { color: var(--blue); }
.todo li.esc { color: var(--red); font-weight: 600; }
.todo li.esc :deep(svg) { color: var(--red); }
summary { cursor: pointer; list-style: none; color: var(--blue); font-size: 0.85rem; font-weight: 500; display: inline-flex; align-items: center; gap: 5px; }
summary::-webkit-details-marker { display: none; }
.why { display: grid; gap: 8px; margin-top: 8px; padding: 12px 14px; background: var(--surface-2); border-left: 1px solid var(--ink); }
.how { font-family: var(--mono); line-height: 1.5; }
.ev { margin: 0; padding-left: 16px; display: grid; gap: 4px; }
.mini td, .mini th { padding: 5px 8px; }
.state { font-size: 0.74rem; font-weight: 600; padding: 2px 8px; border-radius: 2px; background: #edf0f5; color: var(--muted); }
.state.revisada, .state.reconocida { background: var(--ok-soft); color: var(--ok); }
.state.pospuesta { background: var(--blue-soft); color: var(--blue); }
.state.escalada { background: var(--red-soft); color: var(--red); }
.ack { display: flex; gap: 6px; align-items: center; margin: 0; }
.ack.pend { color: var(--muted); }
.ack.done { color: var(--ok); }
.review { display: grid; gap: 8px; border-top: 1px solid var(--line-soft); padding-top: 10px; }
</style>

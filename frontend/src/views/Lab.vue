<template>
  <div class="page lab">
    <div class="page-head">
      <h1>Laboratorio</h1>
      <div class="tabs" role="tablist">
        <router-link v-for="t in TABS" :key="t.k" :to="`/laboratorio/${t.k}`" custom v-slot="{ navigate }">
          <button role="tab" :aria-selected="tab === t.k" :class="{ on: tab === t.k }" @click="navigate"><Icon :name="t.icon" :size="15" />{{ t.l }}</button>
        </router-link>
      </div>
    </div>
    <component :is="VIEWS[tab]" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Icon from '../components/Icon.vue'
import Simulator from './Simulator.vue'
import Validation from './Validation.vue'
import Datos from './Datos.vue'
import Ciencia from './Ciencia.vue'

const props = defineProps({ tab: { type: String, default: 'simulador' } })
const TABS = [{ k: 'simulador', l: 'Simulador', icon: 'cpu' }, { k: 'validacion', l: 'Validación', icon: 'flask' },
  { k: 'datos', l: 'Datos', icon: 'upload' }, { k: 'ciencia', l: 'Ciencia', icon: 'book' }]
const VIEWS = { simulador: Simulator, validacion: Validation, datos: Datos, ciencia: Ciencia }
const tab = computed(() => (VIEWS[props.tab] ? props.tab : 'simulador'))
</script>

<style scoped>
.lab :deep(.page) { padding: 0; max-width: none; }
.lab > .page-head h1 { font-size: 1.45rem; }
/* Títulos internos de cada pestaña: subtítulo en tinta, sin segunda barra azul */
.lab :deep(.page .page-head) { background: none; color: var(--ink); padding: 0 0 6px; border-bottom: 1px solid var(--line-soft); border-radius: 0; }
.lab :deep(.page .page-head h2), .lab :deep(.page .page-head h1) { color: var(--ink); }
.lab :deep(.page .page-head p) { color: var(--muted); }
</style>

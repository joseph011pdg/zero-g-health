<template>
  <div class="panel">
    <div class="panel-head">
      <h2>Registro de ingesta</h2>
      <div class="tabs"><button :class="{ on: f === 'rechazado' }" @click="f = 'rechazado'">Rechazados</button>
        <button :class="{ on: f === '' }" @click="f = ''">Todos</button></div>
    </div>
    <p class="tiny muted">Incluye los registros inválidos del escenario G (datos incompletos) rechazados al cargar la misión.</p>
    <div class="table-wrap scroll">
      <table class="table">
        <thead><tr><th>Astro · día</th><th>Indicador</th><th>Valor</th><th>Estado</th><th>Motivo</th></tr></thead>
        <tbody>
          <tr v-for="r in rows" :key="r.id">
            <td class="mono tiny">{{ r.astro_id }} · D{{ r.day }}</td><td class="tiny">{{ r.indicator }}</td>
            <td class="mono tiny">{{ r.value }}</td>
            <td class="tiny" :class="r.estado === 'rechazado' || r.estado === 'duplicado' ? 'c-amarillo' : 'c-verde'">{{ r.estado }}</td>
            <td class="tiny muted">{{ r.motivo || '—' }}</td>
          </tr>
          <tr v-if="!rows.length"><td colspan="5" class="small muted">Sin registros.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { api } from '../store.js'
const f = ref('rechazado')
const rows = ref([])
watch(f, async () => { rows.value = await api(`/ingest/log?limit=60${f.value ? '&estado=' + f.value : ''}`) }, { immediate: true })
</script>

<style scoped>
.scroll { max-height: 420px; overflow-y: auto; }
</style>

<template>
  <div class="panel">
    <div class="panel-head">
      <h2>Ingestion log</h2>
      <div class="tabs"><button :class="{ on: f === 'rechazado' }" @click="f = 'rechazado'">Rejected</button>
        <button :class="{ on: f === '' }" @click="f = ''">All</button></div>
    </div>
    <p class="tiny muted">Includes the invalid records from scenario G (incomplete data) rejected when the mission was loaded.</p>
    <div class="table-wrap scroll">
      <table class="table">
        <thead><tr><th>Astro · day</th><th>Indicator</th><th>Value</th><th>Status</th><th>Reason</th></tr></thead>
        <tbody>
          <tr v-for="r in rows" :key="r.id">
            <td class="mono tiny">{{ r.astro_id }} · D{{ r.day }}</td><td class="tiny">{{ r.indicator }}</td>
            <td class="mono tiny">{{ r.value }}</td>
            <td class="tiny" :class="r.estado === 'rechazado' || r.estado === 'duplicado' ? 'c-amarillo' : 'c-verde'">{{ ING_STATE[r.estado] || r.estado }}</td>
            <td class="tiny muted">{{ r.motivo || '—' }}</td>
          </tr>
          <tr v-if="!rows.length"><td colspan="5" class="small muted">No records.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { api } from '../store.js'
//ESTADOS de ingesta (identificadores internos en español)
const ING_STATE = { aceptado: 'accepted', rechazado: 'rejected', duplicado: 'duplicate', reemplazado: 'replaced' }
const f = ref('rechazado')
const rows = ref([])
watch(f, async () => { rows.value = await api(`/ingest/log?limit=60${f.value ? '&estado=' + f.value : ''}`) }, { immediate: true })
</script>

<style scoped>
.scroll { max-height: 420px; overflow-y: auto; }
</style>

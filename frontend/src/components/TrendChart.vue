<template>
  <v-chart class="chart" :style="{ height: height + 'px' }" :option="option" autoresize
           :aria-label="`Tendencia de ${nombre}`" role="img" />
</template>

<script setup>
// Valor observado vs. línea base personal, umbral personal "vigilar", umbral poblacional fijo y alertas.
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { C, LEVEL_COLOR, baseTooltip, axis } from '../charts.js'

const props = defineProps({
  data: { type: Array, default: () => [] },
  unidad: String, nombre: String, decimales: { type: Number, default: 1 },
  fijo: Number, showFixed: { type: Boolean, default: true }, showBand: { type: Boolean, default: true },
  events: { type: Array, default: () => [] }, height: { type: Number, default: 180 }, compact: Boolean
})

const LABEL = { verde: 'normal', amarillo: 'vigilar', rojo: 'actuar', sin_dato: 'sin dato', calibrando: 'calibrando' }

const option = computed(() => {
  const d = props.data
  const days = d.map((p) => p.day)
  const nd = props.decimales
  const series = [
    { name: 'Línea base (mediana)', type: 'line', data: d.map((p) => p.normal), showSymbol: false, connectNulls: false,
      lineStyle: { color: C.muted, type: 'dashed', width: 1.2 }, z: 1 },
    { name: props.nombre, type: 'line', data: d.map((p) => p.valor), showSymbol: false, connectNulls: false,
      lineStyle: { color: C.blue, width: 2 }, itemStyle: { color: C.blue }, z: 3,
      markArea: props.events.length ? {
        silent: true, itemStyle: { color: 'rgba(167,139,250,0.10)' },
        label: { color: C.violet, fontSize: 10, position: 'insideTop' },
        data: props.events.map((e) => [{ xAxis: String(e.start), name: e.escenario }, { xAxis: String(Math.min(e.end, days.at(-1) ?? e.end)) }])
          .filter((p) => days.includes(Number(p[0].xAxis)))
      } : undefined },
    { name: 'Alertas', type: 'scatter', symbolSize: 8, z: 4,
      data: d.map((p, i) => (p.nivel === 'amarillo' || p.nivel === 'rojo'
        ? { value: [i, p.valor], itemStyle: { color: LEVEL_COLOR[p.nivel], borderColor: '#081525', borderWidth: 1 },
            symbol: p.nivel === 'rojo' ? 'diamond' : 'triangle' }
        : null)).filter(Boolean) }
  ]
  if (props.showBand) {
    series.push({ name: 'Umbral personal (vigilar)', type: 'line', data: d.map((p) => p.umbral), showSymbol: false,
      lineStyle: { color: C.warn, width: 1, type: [4, 4], opacity: 0.8 }, z: 2 })
  }
  if (props.showFixed && props.fijo !== undefined && props.fijo !== null) {
    series.push({ name: 'Umbral poblacional fijo', type: 'line', data: d.map(() => props.fijo), showSymbol: false,
      lineStyle: { color: C.mars, width: 1, type: 'dotted' }, z: 2 })
  }
  return {
    animation: false,
    grid: { left: 46, right: 14, top: props.compact ? 10 : 34, bottom: 26 },
    legend: props.compact ? undefined : { top: 0, right: 0, textStyle: { color: C.muted, fontSize: 11 }, itemWidth: 14, itemHeight: 8,
      data: series.map((s) => s.name).filter((n) => n !== 'Alertas') },
    tooltip: {
      ...baseTooltip, trigger: 'axis',
      formatter: (ps) => {
        const p = d[ps[0].dataIndex]
        if (!p) return ''
        const v = p.valor === null ? 'sin dato' : `${Number(p.valor).toFixed(nd)} ${props.unidad}`
        return `<b>Día ${p.day}</b><br/>${props.nombre}: <b>${v}</b><br/>` +
          `Línea base: ${p.normal === null ? '—' : Number(p.normal).toFixed(nd)}<br/>` +
          `z robusto: ${p.z ?? '—'} · <b style="color:${LEVEL_COLOR[p.nivel]}">${LABEL[p.nivel]}</b>` +
          (p.fijo ? '<br/><span style="color:#cf7349">Supera el umbral fijo</span>' : '') +
          (p.fuente ? `<br/><span style="color:#9db0c6">Origen: ${p.fuente}</span>` : '')
      }
    },
    xAxis: { type: 'category', data: days.map(String), ...axis({ splitLine: { show: false } }), boundaryGap: false },
    yAxis: { type: 'value', scale: true, ...axis() },
    series
  }
})
</script>

<style scoped>
.chart { width: 100%; }
</style>

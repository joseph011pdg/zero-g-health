<template>
  <v-chart class="chart" :style="{ height: height + 'px' }" :option="option" autoresize
           :aria-label="`${nombre} trend against their usual range`" role="img" />
</template>

<script setup>
// Valor observado sobre la banda de normalidad personal (línea base ± corte "vigilar" × MAD),
// el umbral poblacional opcional y las alertas marcadas sobre la línea.
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { C, LEVEL_COLOR, baseTooltip, axis } from '../charts.js'
import { fmt } from '../store.js'

const props = defineProps({
  data: { type: Array, default: () => [] },
  unidad: String, nombre: String, decimales: { type: Number, default: 1 },
  fijo: Number, showFixed: { type: Boolean, default: true }, showBand: { type: Boolean, default: true },
  events: { type: Array, default: () => [] }, height: { type: Number, default: 180 }, compact: Boolean
})

const LABEL = { verde: 'Normal', amarillo: 'Watch', rojo: 'Act', sin_dato: 'No data', calibrando: 'Calibrating' }
const BAND = 'Their usual range'

const option = computed(() => {
  const d = props.data
  const days = d.map((p) => String(p.day))
  const nd = props.decimales
  const half = d.map((p) => (p.normal === null || p.umbral === null ? null : Math.abs(p.umbral - p.normal)))
  const lower = d.map((p, i) => (half[i] === null ? null : p.normal - half[i]))
  const width = half.map((h) => (h === null ? null : 2 * h))

  // Inicio del episodio de alerta más reciente (para anotarlo en la gráfica)
  let start = null
  for (let i = d.length - 1; i >= 0; i--) {
    if (d[i].nivel === 'rojo' || d[i].nivel === 'amarillo') start = i
    else if (start !== null) break
  }
  if (start !== null && d[d.length - 1].nivel === 'verde') start = null

  const series = []
  if (props.showBand) {
    series.push(
      { name: 'banda-base', type: 'line', data: lower, stack: 'band', showSymbol: false, silent: true,
        lineStyle: { opacity: 0 }, areaStyle: { opacity: 0 }, tooltip: { show: false }, z: 0 },
      { name: BAND, type: 'line', data: width, stack: 'band', showSymbol: false, silent: true,
        lineStyle: { opacity: 0 }, itemStyle: { color: '#c9d8f0' }, areaStyle: { color: '#e6edf8', opacity: 1 }, z: 0 },
      { name: 'Baseline', type: 'line', data: d.map((p) => p.normal), showSymbol: false, silent: true,
        lineStyle: { color: '#9fb4d6', width: 1, type: [2, 3] }, z: 1 }
    )
  }
  if (props.showFixed && props.fijo !== undefined && props.fijo !== null) {
    series.push({ name: 'Population threshold', type: 'line', data: d.map(() => props.fijo), showSymbol: false, silent: true,
      lineStyle: { color: C.mars, width: 1, type: 'dotted' }, z: 1 })
  }
  series.push({
    name: props.nombre, type: 'line', data: d.map((p) => p.valor), showSymbol: false, connectNulls: false,
    lineStyle: { color: C.blue, width: 2.2 }, itemStyle: { color: C.blue }, z: 3,
    markArea: props.events.length ? {
      silent: true, itemStyle: { color: 'rgba(106,79,196,0.08)' },
      label: { color: C.violet, fontSize: 10, position: 'insideTop' },
      data: props.events.map((e) => [{ xAxis: String(e.start), name: `event ${e.escenario}` }, { xAxis: String(Math.min(e.end, d.at(-1)?.day ?? e.end)) }])
        .filter((p) => days.includes(p[0].xAxis))
    } : undefined,
    markLine: start !== null && !props.compact ? {
      silent: true, symbol: 'none', lineStyle: { color: C.red, width: 1, type: 'solid' },
      label: { formatter: `alert day ${d[start].day}`, color: C.red, fontSize: 11, position: 'end', rotate: 0, distance: 4 },
      data: [{ xAxis: days[start] }]
    } : undefined
  })
  series.push({ name: 'Alerts', type: 'scatter', symbolSize: 8, z: 4,
    data: d.map((p, i) => (p.nivel === 'amarillo' || p.nivel === 'rojo'
      ? { value: [i, p.valor], itemStyle: { color: LEVEL_COLOR[p.nivel], borderColor: '#ffffff', borderWidth: 1.5 },
          symbol: p.nivel === 'rojo' ? 'circle' : 'triangle' }
      : null)).filter(Boolean) })

  return {
    animation: false,
    grid: props.compact ? { left: 4, right: 10, top: 8, bottom: 6 } : { left: 46, right: 16, top: 34, bottom: 26 },
    legend: props.compact ? undefined : { top: 0, right: 0, textStyle: { color: C.muted, fontSize: 11 }, itemWidth: 14, itemHeight: 8,
      data: [props.nombre, ...(props.showBand ? [BAND] : []), ...(props.showFixed && props.fijo != null ? ['Population threshold'] : [])] },
    tooltip: {
      ...baseTooltip, trigger: 'axis',
      formatter: (ps) => {
        const p = d[ps[0].dataIndex]
        if (!p) return ''
        const i = ps[0].dataIndex
        const v = p.valor === null ? 'no data' : `${fmt(p.valor, nd)} ${props.unidad}`
        const range = lower[i] === null ? 'n/a' : `${fmt(lower[i], nd)}–${fmt(lower[i] + width[i], nd)}`
        return `<b>Day ${p.day}</b><br/>${props.nombre}: <b>${v}</b><br/>Their usual range: ${range}<br/>` +
          `<b style="color:${LEVEL_COLOR[p.nivel]}">${LABEL[p.nivel]}</b>${p.z !== null ? `, z ${fmt(p.z, 1)}` : ''}` +
          (p.fijo ? '<br/><span style="color:#c8623a">Outside the population threshold</span>' : '')
      }
    },
    xAxis: { type: 'category', data: days, ...axis({ splitLine: { show: false } }), boundaryGap: false, show: !props.compact },
    yAxis: { type: 'value', scale: true, ...axis(), show: !props.compact },
    series
  }
})
</script>

<style scoped>
.chart { width: 100%; }
</style>

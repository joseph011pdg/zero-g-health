// Registro único de ECharts (empaquetado localmente: sin CDN)
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, ScatterChart, BarChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, MarkAreaComponent, MarkLineComponent, LegendComponent, DataZoomComponent
} from 'echarts/components'

use([CanvasRenderer, LineChart, ScatterChart, BarChart, GridComponent, TooltipComponent, MarkAreaComponent,
  MarkLineComponent, LegendComponent, DataZoomComponent])

export const C = {
  text: '#0b1b33', muted: '#5a6b82', line: '#d5dde9', grid: '#e8edf4', blue: '#0b3d91', ok: '#1f7a4d',
  warn: '#c08a00', red: '#b06000', mars: '#b86a3c', violet: '#6a4fc4', gray: '#9aa8bd', surface: '#ffffff'
}
export const LEVEL_COLOR = { verde: C.ok, amarillo: C.warn, rojo: C.red, sin_dato: C.gray, calibrando: C.gray }

export const baseTooltip = {
  backgroundColor: '#ffffff', borderColor: C.line, textStyle: { color: C.text, fontSize: 12 },
  extraCssText: 'box-shadow: 0 8px 24px rgba(11,27,51,.12); border-radius: 8px;'
}
export const axis = (extra = {}) => ({
  axisLine: { lineStyle: { color: C.line } }, axisTick: { show: false },
  axisLabel: { color: C.muted, fontSize: 11 }, splitLine: { lineStyle: { color: C.grid } }, ...extra
})

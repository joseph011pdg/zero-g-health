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
  text: '#f5f8fc', muted: '#9db0c6', line: '#22405f', grid: '#17304b', blue: '#54b8e8', ok: '#57c79a',
  warn: '#f2b85d', red: '#e76a70', mars: '#cf7349', violet: '#a78bfa', gray: '#7d8ea3', surface: '#102238'
}
export const LEVEL_COLOR = { verde: C.ok, amarillo: C.warn, rojo: C.red, sin_dato: C.gray, calibrando: C.gray }

export const baseTooltip = {
  backgroundColor: '#0e1f33', borderColor: C.line, textStyle: { color: C.text, fontSize: 12 },
  extraCssText: 'box-shadow: 0 8px 24px rgba(0,0,0,.45); border-radius: 8px;'
}
export const axis = (extra = {}) => ({
  axisLine: { lineStyle: { color: C.line } }, axisTick: { show: false },
  axisLabel: { color: C.muted, fontSize: 11 }, splitLine: { lineStyle: { color: C.grid } }, ...extra
})

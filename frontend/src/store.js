import { defineStore } from 'pinia'

export class ApiError extends Error {}

export async function api(path, opts = {}) {
  let res
  try {
    res = await fetch(`/api${path}`, {
      method: opts.method || 'GET',
      headers: { 'Content-Type': 'application/json' },
      body: opts.body ? JSON.stringify(opts.body) : undefined
    })
  } catch (e) {
    throw new ApiError('No hay conexión con el motor local (backend). Ejecute scripts\\start.ps1.')
  }
  if (!res.ok) {
    let msg = `Error ${res.status}`
    try {
      const j = await res.json()
      msg = typeof j.detail === 'string' ? j.detail : (j.detail?.[0]?.msg || msg)
    } catch { /* respuesta sin JSON */ }
    throw new ApiError(msg)
  }
  const ct = res.headers.get('content-type') || ''
  return ct.includes('json') ? res.json() : res.text()
}

export const useStore = defineStore('basal', {
  state: () => ({
    mission: null,
    indicators: {},
    crew: [],
    selected: 'A1',
    online: null,
    publico: false,
    error: null,
    toasts: [],
    tick: 0 // se incrementa cuando cambian los datos: las vistas recargan
  }),
  getters: {
    day: (s) => s.mission?.dia ?? 0,
    selectedAstro: (s) => s.crew.find((a) => a.id === s.selected)
  },
  actions: {
    async init() {
      try {
        this.indicators = await api('/indicators')
        this.publico = !!(await api('/health')).publico
        await this.refresh()
        this.online = true
        this.error = null
      } catch (e) {
        this.online = false
        this.error = e.message
      }
      if (!this._ping) this._ping = setInterval(() => this.ping(), 8000)
    },
    async ping() {
      try {
        await api('/health')
        if (!this.online) { this.online = true; this.error = null; await this.refresh() }
      } catch { this.online = false }
    },
    async refresh() {
      const [m, c] = await Promise.all([api('/mission'), api('/crew')])
      this.crew = c.tripulacion
      this.mission = m
      if (!this.crew.find((a) => a.id === this.selected) && this.crew.length) this.selected = this.crew[0].id
      this.tick++
    },
    async setDay(day) {
      await api('/mission/day', { method: 'POST', body: { day } })
      await this.refresh()
    },
    async advance(n) {
      await api('/mission/advance', { method: 'POST', body: { n } })
      await this.refresh()
    },
    select(id) { this.selected = id },
    toast(msg, kind = 'ok') {
      const id = Math.random()
      this.toasts.push({ id, msg, kind })
      setTimeout(() => { this.toasts = this.toasts.filter((t) => t.id !== id) }, 4200)
    },
    async run(fn, okMsg) {
      try {
        const r = await fn()
        if (okMsg) this.toast(okMsg)
        return r
      } catch (e) {
        this.toast(e.message, 'err')
        throw e
      }
    }
  }
})

export const LEVEL = {
  verde: { label: 'Normal', icon: 'check' },
  amarillo: { label: 'Vigilar', icon: 'triangle' },
  rojo: { label: 'Actuar', icon: 'octagon' },
  calibrando: { label: 'Calibrando', icon: 'dashed' },
  sin_dato: { label: 'Sin dato', icon: 'minus' }
}
export const IND_ICON = { rhr: 'heart', hrv: 'activity', sleep: 'moon', dose: 'radiation', pvt: 'target', mood: 'smile' }
export const SRC_LABEL = { sintetico: 'sintético', manual: 'manual', csv: 'CSV', pvt: 'PVT-B', pvt_abreviada: 'PVT abreviada', real: 'real' }
export const STATE_LABEL = { pendiente: 'Pendiente', revisada: 'Revisada', escalada: 'Escalada', descartada: 'Descartada' }

export const fmt = (v, d = 1) => (v === null || v === undefined || Number.isNaN(v) ? '—' : Number(v).toFixed(d))
export const signed = (v, d = 1) => (v === null || v === undefined ? '—' : `${v > 0 ? '+' : ''}${Number(v).toFixed(d)}`)

export function download(name, content, type = 'application/json') {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = Object.assign(document.createElement('a'), { href: url, download: name })
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

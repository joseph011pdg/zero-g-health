import { defineStore } from 'pinia'

export class ApiError extends Error {}

// Estado por sesión (demo pública): cada visitante mueve su propio día y su apagón simulado
// sin cambiar lo que ven los demás. Viaja al backend en cabeceras.
function ssGet(k) { try { return sessionStorage.getItem(k) } catch { return null } }
function ssSet(k, v) { try { v === null ? sessionStorage.removeItem(k) : sessionStorage.setItem(k, v) } catch { /* solo memoria */ } }
export const session = { dia: ssGet('basal.dia') === null ? null : +ssGet('basal.dia'), apagon: ssGet('basal.apagon') === '1' }

export async function api(path, opts = {}) {
  let res
  const headers = { 'Content-Type': 'application/json' }
  if (session.dia !== null) headers['X-Basal-Dia'] = String(session.dia)
  if (session.apagon) headers['X-Basal-Apagon'] = '1'
  try {
    res = await fetch(`/api${path}`, {
      method: opts.method || 'GET',
      headers,
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

function readAcks() {
  try { return JSON.parse(localStorage.getItem('basal.acks') || '{}') } catch { return {} }
}

function readRole() {
  try { return localStorage.getItem('basal.role') || 'oficial' } catch { return 'oficial' }
}

export const useStore = defineStore('basal', {
  state: () => ({
    mission: null,
    indicators: {},
    crew: [],
    selected: 'A1',
    online: null,
    publico: false,
    role: readRole(), // 'astronauta' | 'oficial'
    updatedAt: null,
    pendingReports: 0,
    apagon: session.apagon, // apagón simulado solo en esta sesión
    acks: readAcks(), // demo pública: reconocimientos guardados en este navegador
    error: null,
    toasts: [],
    demo: false, // panel de demo guiada abierto
    tick: 0 // se incrementa cuando cambian los datos: las vistas recargan
  }),
  getters: {
    day: (s) => s.mission?.dia ?? 0,
    selectedAstro: (s) => s.crew.find((a) => a.id === s.selected),
    officer: (s) => s.crew.find((a) => /m[eé]dic/i.test(a.rol)),
    isOfficer: (s) => s.role === 'oficial'
  },
  actions: {
    async init() {
      try {
        this.indicators = await api('/indicators')
        this.publico = !!(await api('/health')).publico
        if (!this.publico && session.dia !== null) { session.dia = null; ssSet('basal.dia', null) }
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
      const [m, c, r] = await Promise.all([api('/mission'), api('/crew'), api('/reports')])
      this.crew = c.tripulacion
      this.mission = m
      this.pendingReports = r.filter((x) => x.estado === 'pendiente').length
      this.updatedAt = new Date()
      if (!this.crew.find((a) => a.id === this.selected) && this.crew.length) this.selected = this.crew[0].id
      this.tick++
    },
    async setDay(day) {
      if (this.publico) {
        session.dia = Math.max(0, Math.min(day, (this.mission?.dias ?? 120) - 1))
        ssSet('basal.dia', String(session.dia))
      } else {
        await api('/mission/day', { method: 'POST', body: { day } })
      }
      await this.refresh()
    },
    async advance(n) {
      if (this.publico) return this.setDay(this.day + n)
      await api('/mission/advance', { method: 'POST', body: { n } })
      await this.refresh()
    },
    async setApagon(on) {
      this.apagon = !!on
      session.apagon = this.apagon
      ssSet('basal.apagon', on ? '1' : null)
      await this.refresh()
    },
    async resetDemo() {
      session.dia = null; session.apagon = false; this.apagon = false
      ssSet('basal.dia', null); ssSet('basal.apagon', null)
      this.acks = {}
      try { localStorage.removeItem('basal.acks') } catch { /* nada */ }
      if (!this.publico) await api('/sim/reset', { method: 'POST', body: {} })
      await this.refresh()
    },
    // Revisión de una alarma. En la demo pública se guarda solo en este navegador.
    async review(a, estado, nota = null) {
      const revisor = this.officer ? this.officer.nombre : 'Oficial médico'
      if (this.publico) {
        const key = `${a.astro_id}|${a.episodio}|${a.nivel}`
        const acks = { ...this.acks }
        if (estado === 'pendiente') delete acks[key]
        else acks[key] = { estado, nota: nota || null, revisor, revisado_dia: this.day, desde: a.day }
        this.acks = acks
        try { localStorage.setItem('basal.acks', JSON.stringify(acks)) } catch { /* solo memoria */ }
        this.tick++
        return { ...a, ...(acks[key] || { estado: 'pendiente', nota: null, revisor: null, revisado_dia: null }) }
      }
      const r = await api(`/alerts/${encodeURIComponent(a.id)}`, { method: 'PATCH', body: { estado, nota: nota || null, revisor } })
      await this.refresh()
      return r
    },
    // Aplica los reconocimientos locales (demo pública) con la misma lógica de episodio del backend:
    // hereda hacia adelante y una alarma pospuesta vuelve a pendiente pasado su día.
    withAcks(list) {
      if (!this.publico || !list) return list
      return list.map((a) => {
        const k = this.acks[`${a.astro_id}|${a.episodio}|${a.nivel}`]
        if (!k || a.day < k.desde || a.day > k.revisado_dia + 10) return a
        if (k.estado === 'pospuesta' && this.day > k.revisado_dia) return a
        return { ...a, estado: k.estado, nota: k.nota, revisor: k.revisor, revisado_dia: k.revisado_dia }
      })
    },
    select(id) { this.selected = id },
    setRole(r) {
      this.role = r
      try { localStorage.setItem('basal.role', r) } catch { /* sin almacenamiento: solo en memoria */ }
    },
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
export const RANK_LEVEL = { sin_dato: -1, calibrando: -1, verde: 0, amarillo: 1, rojo: 2 }
export const IND_ICON = { rhr: 'heart', hrv: 'activity', sleep: 'moon', dose: 'radiation', pvt: 'target', mood: 'smile' }
export const SRC_LABEL = { sintetico: 'sintético', manual: 'manual', csv: 'CSV', pvt: 'PVT-B', pvt_abreviada: 'PVT abreviada', real: 'real' }
export const STATE_LABEL = { pendiente: 'Sin reconocer', reconocida: 'Reconocida', pospuesta: 'Pospuesta 24 h', revisada: 'Resuelta', escalada: 'Escalada', descartada: 'Descartada' }

const nf = (v, d) => Number(v).toLocaleString('es', { minimumFractionDigits: d, maximumFractionDigits: d })
// Cifras con coma decimal (es)
export const fmt = (v, d = 1) => (v === null || v === undefined || Number.isNaN(v) ? '—' : nf(v, d))
// Número con coma decimal sin fijar decimales (cifras de validación)
export const nn = (v, max = 2) => (v === null || v === undefined || Number.isNaN(Number(v)) ? '—' : Number(v).toLocaleString('es', { maximumFractionDigits: max }))
export const signed = (v, d = 1) => (v === null || v === undefined ? '—' : `${v > 0 ? '+' : v < 0 ? '−' : ''}${nf(Math.abs(v), d)}`)

export function download(name, content, type = 'application/json') {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = Object.assign(document.createElement('a'), { href: url, download: name })
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

// Episodios de alarma: misma persona, tipo y nivel en días consecutivos. Devuelve la alerta más
// reciente (rep) y el día en que empezó (since). Solo episodios con alguna alerta en los últimos 7 días.
export function episodes(alerts, day) {
  const map = new Map()
  for (const a of alerts || []) {
    if (a.day <= day - 7 || a.day > day) continue
    const key = `${a.astro_id}|${a.episodio}|${a.nivel}`
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(a)
  }
  const out = []
  for (const [key, list] of map) {
    list.sort((x, y) => y.day - x.day)
    let first = list[0].day
    for (const x of list.slice(1)) { if (x.day === first - 1) first = x.day; else break }
    out.push({ key, rep: list[0], since: first, astro_id: list[0].astro_id })
  }
  const order = (g) => (g.rep.estado === 'pendiente' ? 0 : 1)
  return out.sort((a, b) => order(a) - order(b) || RANK_LEVEL[b.rep.nivel] - RANK_LEVEL[a.rep.nivel] || b.rep.day - a.rep.day)
}

// "1 aviso" / "2 avisos"
export const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`

"""Motor de detección (F5 línea base + F6 anomalías). Solo NumPy/pandas, determinista.

Para cada astronauta, indicador y día t:
  1. Línea base reciente: mediana y MAD de las observaciones VÁLIDAS de los `window` días
     ANTERIORES a t (el valor de hoy nunca entra en su propia referencia). Los días que ya
     estaban en alerta se excluyen, para que un deterioro persistente no "normalice" la base.
     Si quedan menos de `min_periods`, se amplía la búsqueda hasta 2×window días; si aun así
     no alcanza, el indicador queda "calibrando" (no se evalúa, no se da por sano).
  2. Línea base inicial: primeros `window` días válidos de misión (detecta deterioros lentos
     que pasarían por debajo del corte día a día).
  3. z = dirección × (valor − mediana) / max(1,4826 × MAD, min_spread). Positivo = peor.
     Se toma el mayor de los dos z (reciente / inicial) y se informa cuál se usó.
  4. Semáforo: verde z < yellow · amarillo yellow ≤ z < red · rojo z ≥ red,
     o `persist` días válidos seguidos en amarillo.
Sin medición hoy -> "sin_dato" (la ausencia de datos NUNCA se interpreta como sano).

Método B (comparador): alerta si el valor cruza el intervalo de referencia poblacional fijo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Params
from .indicators import INDICATORS, INDICATOR_KEYS

MAD_TO_SD = 1.4826
# Códigos de nivel
SIN_DATO, CALIBRANDO, VERDE, AMARILLO, ROJO = -2, -1, 0, 1, 2
LEVELS = {SIN_DATO: "sin_dato", CALIBRANDO: "calibrando", VERDE: "verde", AMARILLO: "amarillo", ROJO: "rojo"}
RANK = {"sin_dato": -1, "calibrando": -1, "verde": 0, "amarillo": 1, "rojo": 2}


def robust_stats(x: np.ndarray) -> tuple[float, float]:
    """Mediana y MAD escalado (×1,4826) de un vector sin NaN."""
    med = float(np.median(x))
    return med, float(np.median(np.abs(x - med)) * MAD_TO_SD)


def robust_z(value: float, med: float, mad: float, min_spread: float, direction: int = 1) -> float:
    return direction * (value - med) / max(mad, min_spread)


def theil_sen(y: np.ndarray) -> float:
    """Pendiente robusta (mediana de pendientes por pares), unidades por día."""
    idx = np.where(~np.isnan(y))[0]
    if len(idx) < 3:
        return float("nan")
    i, j = np.triu_indices(len(idx), 1)
    return float(np.median((y[idx][j] - y[idx][i]) / (idx[j] - idx[i])))


def score_indicator(values, key: str, p: Params) -> pd.DataFrame:
    """values: array diario (posición = día, NaN = sin dato) de un indicador de un astronauta."""
    cfg = INDICATORS[key]
    v = np.asarray(values, dtype=float)
    n = len(v)
    d, ms = cfg["direction"], cfg["min_spread"]
    out = {c: np.full(n, np.nan) for c in ("z", "z_rec", "z_ini", "med", "mad", "n_obs", "calidad", "tendencia")}
    level = np.full(n, SIN_DATO, dtype=int)
    ref = np.array([""] * n, dtype=object)
    reason = np.array([""] * n, dtype=object)
    flagged = np.zeros(n, dtype=bool)
    valid = ~np.isnan(v)

    vidx = np.where(valid)[0]
    init_ready_at = vidx[p.window - 1] if len(vidx) >= p.window else None
    init_med = init_mad = None
    if init_ready_at is not None:
        init_med, init_mad = robust_stats(v[vidx[:p.window]])

    run = 0  # días válidos seguidos en amarillo o peor
    for t in range(n):
        lo = max(0, t - p.window)
        out["calidad"][t] = valid[lo:t].mean() if t > lo else 0.0
        out["tendencia"][t] = theil_sen(v[max(0, t - 6):t + 1])
        if not valid[t]:
            continue  # sin dato: no se evalúa y no rompe ni reinicia la racha
        # 1) Línea base reciente (excluye hoy y días en alerta)
        usable = valid & ~flagged if p.exclude_alerts else valid
        pool = v[lo:t][usable[lo:t]]
        if len(pool) < p.min_periods:
            lo2 = max(0, t - 2 * p.window)
            pool = v[lo2:t][usable[lo2:t]]
        z_rec = np.nan
        if len(pool) >= p.min_periods:
            med_r, mad_r = robust_stats(pool)
            z_rec = robust_z(v[t], med_r, mad_r, ms, d)
        # 2) Línea base inicial (solo después del periodo de calibración)
        z_ini = np.nan
        if p.use_initial and init_ready_at is not None and t > init_ready_at:
            z_ini = robust_z(v[t], init_med, init_mad, ms, d)
        if np.isnan(z_rec) and np.isnan(z_ini):
            level[t] = CALIBRANDO
            out["n_obs"][t] = len(pool)
            continue
        use_ini = (not np.isnan(z_ini)) and (np.isnan(z_rec) or z_ini > z_rec)
        z = z_ini if use_ini else z_rec
        if use_ini:
            out["med"][t], out["mad"][t], out["n_obs"][t] = init_med, init_mad, p.window
            ref[t] = "mission-start baseline"
        else:
            out["med"][t], out["mad"][t], out["n_obs"][t] = med_r, mad_r, len(pool)
            ref[t] = f"last {p.window} days"
        out["z"][t], out["z_rec"][t], out["z_ini"][t] = z, z_rec, z_ini

        if z >= p.red:
            level[t], reason[t] = ROJO, "corte_rojo"
        elif z >= p.yellow:
            level[t], reason[t] = AMARILLO, "corte_amarillo"
        else:
            level[t] = VERDE
        run = run + 1 if level[t] >= AMARILLO else 0
        if level[t] == AMARILLO and run >= p.persist:
            level[t], reason[t] = ROJO, "persistencia"
        flagged[t] = level[t] >= AMARILLO

    thr = p.fixed[key]
    fixed = (v > thr) if d > 0 else (v < thr)
    fixed &= valid
    return pd.DataFrame({
        "value": v, "normal": out["med"], "mad": out["mad"], "n_obs": out["n_obs"],
        "z": np.round(out["z"], 2), "z_rec": np.round(out["z_rec"], 2), "z_ini": np.round(out["z_ini"], 2),
        "level": level, "base_ref": ref, "reason": reason, "calidad": out["calidad"],
        "tendencia": out["tendencia"], "fixed_alert": fixed.astype(int),
    })


def analyze_astronaut(df: pd.DataFrame, p: Params) -> dict[str, pd.DataFrame]:
    """df: índice = día (0..N-1, sin huecos), columnas = indicadores (NaN = sin dato)."""
    return {k: score_indicator(df[k].to_numpy(dtype=float), k, p) for k in INDICATOR_KEYS}


def global_level(results: dict[str, pd.DataFrame], day: int) -> int:
    lv = [int(r.loc[day, "level"]) for r in results.values()]
    best = max(lv)
    return best if best >= VERDE else (CALIBRANDO if CALIBRANDO in lv else SIN_DATO)


def health_index(results: dict[str, pd.DataFrame], day: int) -> int | None:
    """Índice 0–100 (100 = todo en su rango habitual), solo con indicadores evaluados hoy."""
    zs = [float(r.loc[day, "z"]) for r in results.values() if not pd.isna(r.loc[day, "z"])]
    if not zs:
        return None
    penalty = sum(min(max(z, 0.0), 5.0) for z in zs) / (5.0 * len(zs))
    return int(round(100 * (1 - penalty)))

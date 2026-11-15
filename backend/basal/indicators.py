"""Definición de los seis indicadores que monitorea el sistema.

direction  = +1 -> es preocupante que el valor SUBA; -1 -> que BAJE.
min_spread = variación mínima (resolución práctica de la medida). Evita dividir entre ~0
             cuando el MAD es 0 o casi 0 (datos muy estables o discretos).
limits     = rango físicamente plausible. Fuera de él, el registro se RECHAZA en la ingesta
             (no es un umbral clínico, solo control de calidad del dato).
units      = unidad canónica y alias aceptados en la ingesta (CSV/formularios).
clinical   = referencia clínica convencional cuando existe una defendible (solo informativa).
             Si no existe, se dice explícitamente.

El comparador de "umbral fijo" (método B) NO se escribe a mano: se estima como intervalo de
referencia poblacional (percentil 2,5 / 97,5 de días sanos) en el conjunto de AJUSTE del
simulador y se guarda en data/config.json (ver validation.py).
"""

INDICATORS = {
    "rhr": {
        "nombre": "Resting heart rate",
        "corto": "Resting HR",
        "unidad": "bpm",
        "units": ["bpm", "lpm", "latidos/min", "beats/min"],
        "direction": +1,
        "min_spread": 1.0,
        "limits": (25.0, 220.0),
        "decimales": 0,
        "riesgo": "Cardiovascular / immune",
        "sensor": "Wearable (ECG) at rest",
        "clinical": "Clinical convention: resting tachycardia > 100 bpm (general reference, not spaceflight-specific).",
    },
    "hrv": {
        "nombre": "Heart rate variability (RMSSD)",
        "corto": "HRV (RMSSD)",
        "unidad": "ms",
        "units": ["ms"],
        "direction": -1,
        "min_spread": 2.0,
        "limits": (1.0, 300.0),
        "decimales": 0,
        "riesgo": "Stress and recovery",
        "sensor": "Wearable (ECG) during sleep",
        "clinical": "There is no accepted clinical population threshold for RMSSD: it depends strongly on age and the individual.",
    },
    "sleep": {
        "nombre": "Sleep duration",
        "corto": "Sleep",
        "unidad": "h",
        "units": ["h", "horas", "hr", "hours"],
        "direction": -1,
        "min_spread": 0.25,
        "limits": (0.0, 16.0),
        "decimales": 1,
        "riesgo": "Behavioral / cognitive / immune",
        "sensor": "Wearable actigraphy",
        "clinical": "Consensus recommendation for adults: sleep 7 h or more (Watson et al., 2015).",
    },
    "dose": {
        "nombre": "Radiation dose rate",
        "corto": "Daily dose",
        "unidad": "mGy/day",
        "units": ["mGy/day", "mGy/día", "mGy/dia", "mGy/d", "mGy"],
        "direction": +1,
        "min_spread": 0.02,
        "limits": (0.0, 1000.0),
        "decimales": 2,
        "riesgo": "Cancer, cardiovascular, cognitive",
        "sensor": "Personal dosimeter",
        "clinical": "No NASA limit is used: the prototype watches the daily RATE and compares the CUMULATIVE dose "
                    "with what the simulated scenario expects to date (not with career limits).",
    },
    "pvt": {
        "nombre": "PVT-B lapses and false starts",
        "corto": "PVT lapses",
        "unidad": "lapses",
        "units": ["lapses", "lapsos", "errores", "fallos", "errors"],
        "direction": +1,
        "min_spread": 1.0,
        "limits": (0.0, 100.0),
        "decimales": 0,
        "riesgo": "Fatigue and performance",
        "sensor": "PVT-B test on tablet",
        "clinical": "No clinical threshold; PVT-B defines a lapse as a response ≥ 355 ms (Basner et al., 2011).",
    },
    "mood": {
        "nombre": "Mood (self-report)",
        "corto": "Mood",
        "unidad": "/10",
        "units": ["/10", "puntos", "escala", "points", "scale"],
        "direction": -1,
        "min_spread": 0.5,
        "limits": (1.0, 10.0),
        "decimales": 1,
        "riesgo": "Behavioral health",
        "sensor": "Daily check-in on tablet",
        "clinical": "The prototype's own analog scale: not a validated psychological or diagnostic instrument.",
    },
}

INDICATOR_KEYS = list(INDICATORS.keys())


def canonical_unit(key: str, unit: str | None) -> str | None:
    """Devuelve la unidad canónica si `unit` es aceptada para el indicador; None si no."""
    if unit is None or str(unit).strip() == "":
        return INDICATORS[key]["unidad"]  # sin unidad -> se asume la canónica
    u = str(unit).strip().lower()
    for alias in INDICATORS[key]["units"]:
        if u == alias.lower():
            return INDICATORS[key]["unidad"]
    return None

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
        "nombre": "FC en reposo",
        "corto": "FC reposo",
        "unidad": "lpm",
        "units": ["lpm", "bpm", "latidos/min"],
        "direction": +1,
        "min_spread": 1.0,
        "limits": (25.0, 220.0),
        "decimales": 0,
        "riesgo": "Cardiovascular / inmune",
        "sensor": "Wearable (ECG) en reposo",
        "clinical": "Convención clínica: taquicardia en reposo > 100 lpm (referencia general, no específica de vuelo).",
    },
    "hrv": {
        "nombre": "Variabilidad de la FC (RMSSD)",
        "corto": "VFC (RMSSD)",
        "unidad": "ms",
        "units": ["ms"],
        "direction": -1,
        "min_spread": 2.0,
        "limits": (1.0, 300.0),
        "decimales": 0,
        "riesgo": "Estrés y recuperación",
        "sensor": "Wearable (ECG) durante el sueño",
        "clinical": "No existe un umbral poblacional clínico aceptado para RMSSD: depende mucho de la edad y la persona.",
    },
    "sleep": {
        "nombre": "Duración del sueño",
        "corto": "Sueño",
        "unidad": "h",
        "units": ["h", "horas", "hr"],
        "direction": -1,
        "min_spread": 0.25,
        "limits": (0.0, 16.0),
        "decimales": 1,
        "riesgo": "Conductual / cognitivo / inmune",
        "sensor": "Actigrafía del wearable",
        "clinical": "Recomendación de consenso para adultos: dormir 7 h o más (Watson et al., 2015).",
    },
    "dose": {
        "nombre": "Tasa de dosis de radiación",
        "corto": "Dosis diaria",
        "unidad": "mGy/día",
        "units": ["mGy/día", "mGy/dia", "mGy/d", "mGy"],
        "direction": +1,
        "min_spread": 0.02,
        "limits": (0.0, 1000.0),
        "decimales": 2,
        "riesgo": "Cáncer, cardiovascular, cognitivo",
        "sensor": "Dosímetro personal",
        "clinical": "No se usa un límite de NASA: el prototipo vigila la TASA diaria y compara la dosis ACUMULADA "
                    "con el presupuesto del escenario simulado (no con límites de carrera).",
    },
    "pvt": {
        "nombre": "Errores en la prueba PVT-B (lapsos + anticipaciones)",
        "corto": "Errores PVT",
        "unidad": "errores",
        "units": ["errores", "fallos", "lapsos"],
        "direction": +1,
        "min_spread": 1.0,
        "limits": (0.0, 100.0),
        "decimales": 0,
        "riesgo": "Fatiga y rendimiento",
        "sensor": "Prueba PVT-B en tableta",
        "clinical": "No hay umbral clínico; PVT-B define lapso como respuesta ≥ 355 ms (Basner et al., 2011).",
    },
    "mood": {
        "nombre": "Estado de ánimo (autorreporte)",
        "corto": "Ánimo",
        "unidad": "/10",
        "units": ["/10", "puntos", "escala"],
        "direction": -1,
        "min_spread": 0.5,
        "limits": (1.0, 10.0),
        "decimales": 1,
        "riesgo": "Salud conductual",
        "sensor": "Check-in diario en tableta",
        "clinical": "Escala analógica propia del prototipo: no es un instrumento psicológico validado ni diagnóstico.",
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

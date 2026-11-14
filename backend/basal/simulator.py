"""Simulador de misión (F9): genera datos SINTÉTICOS con desviaciones conocidas.

Los escenarios son representaciones sintéticas para probar algoritmos, NO predicciones
clínicas. Los valores son plausibles e ilustrativos:
  * Tasa de dosis: ~0,4 mGy/día, coherente con la estimación de 300–450 mGy para una misión
    a Marte de ~3 años (Patel et al., 2020). La magnitud del evento solar es ilustrativa.
  * Diferencias entre personas mayores que la variación diaria de cada persona: es la
    hipótesis que motiva la línea base individual (Basner et al., 2014 observan gran
    variabilidad interindividual en Mars-520). `heterogeneity` permite probar el caso contrario.

Escenarios por astronauta:
  A estable · B fatiga progresiva · C estrés fisiológico · D exposición ambiental (radiación)
  E cambio conductual · G datos incompletos (faltantes + registros inválidos)
Escenario de misión: F interrupción de comunicaciones (apagón; ver mission en db.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .indicators import INDICATOR_KEYS

CREW = [
    {"id": "A1", "nombre": "Cmdte. Inés Rivera", "rol": "Comandante"},
    {"id": "A2", "nombre": "Dra. Amara Okafor", "rol": "Oficial médica"},
    {"id": "A3", "nombre": "Ing. Erik Lindqvist", "rol": "Ingeniero de vuelo"},
    {"id": "A4", "nombre": "Esp. Kenji Tanaka", "rol": "Especialista de misión"},
]

SCENARIOS = {
    "A": {"nombre": "Estabilidad fisiológica", "afecta": [], "dur": (0, 0),
          "desc": "Sin desviaciones inyectadas: solo variación diaria normal."},
    "B": {"nombre": "Fatiga progresiva", "afecta": ["sleep", "pvt", "mood"], "dur": (10, 16),
          "desc": "El sueño se acorta poco a poco y aumentan los errores en la PVT."},
    "C": {"nombre": "Estrés fisiológico", "afecta": ["rhr", "hrv"], "dur": (5, 8),
          "desc": "Sube la FC en reposo y baja la variabilidad cardíaca (patrón de estrés o infección)."},
    "D": {"nombre": "Exposición ambiental (evento solar)", "afecta": ["dose"], "dur": (1, 2),
          "desc": "Un evento de partículas solares eleva la tasa de dosis durante 1–2 días."},
    "E": {"nombre": "Cambio conductual", "afecta": ["mood", "pvt"], "dur": (25, 35),
          "desc": "Descenso lento y persistente del ánimo con peor desempeño cognitivo."},
    "G": {"nombre": "Datos incompletos", "afecta": [], "dur": (0, 0),
          "desc": "Faltan mediciones y llegan registros inválidos que la ingesta debe rechazar."},
}
EVENT_SCENARIOS = ["B", "C", "D", "E"]

# Población (media, DE entre personas) y ruido diario dentro de cada persona
POP = {"rhr": (60.0, 7.0), "hrv": (45.0, 12.0), "sleep": (6.9, 0.5), "dose": (0.40, 0.05),
       "pvt": (1.8, 0.7), "mood": (7.4, 0.8)}
NOISE = {"rhr": 1.8, "hrv": 4.5, "sleep": 0.45, "dose": 0.03, "mood": 0.6}
AR = 0.3  # autocorrelación diaria del ruido (los días seguidos se parecen)

# Misión de demostración: inicio fijo de cada evento para que el guion sea reproducible
DEMO_ASSIGNMENTS = {
    "A1": [{"escenario": "B", "inicio": 44}],
    "A2": [{"escenario": "A"}, {"escenario": "G"}],
    "A3": [{"escenario": "C", "inicio": 70}],
    "A4": [{"escenario": "E", "inicio": 52}],
}
DEMO_CREW_EVENTS = [{"escenario": "D", "inicio": 86}]  # evento solar: afecta a toda la tripulación


def _ar_noise(rng, sd, n):
    e = rng.normal(0, sd, n)
    for i in range(1, n):
        e[i] += AR * e[i - 1]
    return e * np.sqrt(1 - AR ** 2)


def _baseline(rng, heterogeneity: float) -> dict:
    b = {k: m + rng.normal(0, s * heterogeneity) for k, (m, s) in POP.items()}
    b["hrv"] = max(b["hrv"], 15.0)
    b["sleep"] = float(np.clip(b["sleep"], 5.5, 8.5))
    b["dose"] = max(b["dose"], 0.2)
    b["pvt"] = max(b["pvt"], 0.4)
    b["mood"] = float(np.clip(b["mood"], 5.0, 9.3))
    return b


def _apply_event(series, base, code, start, end, intensity, rng):
    n = end - start + 1
    sl = slice(start, end + 1)
    k = intensity
    if code == "B":  # progresiva
        r = np.linspace(1 / n, 1, n)
        series["sleep"][sl] -= 1.8 * k * r
        series["pvt"][sl] += rng.poisson(5 * k * r)
        series["mood"][sl] -= 1.0 * k * r
    elif code == "C":  # brusca (2 días hasta el máximo)
        r = np.minimum((np.arange(n) + 1) / 2, 1.0)
        series["rhr"][sl] += 8 * k * r
        series["hrv"][sl] -= 0.30 * k * base["hrv"] * r
    elif code == "D":
        series["dose"][sl] += rng.uniform(3, 9, n) * k
    elif code == "E":  # muy lenta
        r = np.linspace(1 / n, 1, n)
        series["mood"][sl] -= 2.6 * k * r
        series["pvt"][sl] += rng.poisson(3 * k * r)


def simulate_mission(days: int = 120, seed: int = 7, assignments: dict | None = None,
                     crew_events: list | None = None, crew=CREW, heterogeneity: float = 1.0,
                     intensity_range=(1.0, 1.0), missing_rate: float = 0.0):
    """Devuelve (datos, eventos, invalidos).

    datos:     DataFrame astro_id, day, rhr, hrv, sleep, dose, pvt, mood (NaN = no hay medición)
    eventos:   DataFrame astro_id, escenario, nombre, start, end, afecta, intensidad (la "verdad")
    invalidos: lista de registros crudos inválidos (escenario G) para probar la ingesta
    """
    rng = np.random.default_rng(seed)
    assignments = assignments if assignments is not None else DEMO_ASSIGNMENTS
    crew_events = crew_events if crew_events is not None else DEMO_CREW_EVENTS
    rows, events, invalid = [], [], []

    for a in crew:
        base = _baseline(rng, heterogeneity)
        series = {k: base[k] + _ar_noise(rng, NOISE[k], days) for k in NOISE}
        series["pvt"] = rng.poisson(base["pvt"], days).astype(float)

        plan = list(assignments.get(a["id"], [{"escenario": "A"}])) + list(crew_events)
        incomplete = any(p["escenario"] == "G" for p in plan)
        for p in plan:
            code = p["escenario"]
            if code not in EVENT_SCENARIOS:
                continue
            lo, hi = SCENARIOS[code]["dur"]
            dur = int(p.get("duracion") or rng.integers(lo, hi + 1))
            start = int(p.get("inicio") if p.get("inicio") is not None else rng.integers(25, days - 30))
            if start >= days:
                continue
            end = min(start + dur - 1, days - 1)
            k = float(p.get("intensidad") or rng.uniform(*intensity_range))
            _apply_event(series, base, code, start, end, k, rng)
            events.append({"astro_id": a["id"], "escenario": code, "nombre": SCENARIOS[code]["nombre"],
                           "start": start, "end": end, "afecta": ",".join(SCENARIOS[code]["afecta"]),
                           "intensidad": round(k, 2)})

        series["sleep"] = np.clip(series["sleep"], 2.5, 11)
        series["mood"] = np.clip(np.round(series["mood"] * 2) / 2, 1, 10)  # escala en medios puntos
        series["hrv"] = np.clip(series["hrv"], 8, None)
        series["dose"] = np.clip(series["dose"], 0.05, None)
        series["rhr"] = np.round(series["rhr"])

        data = {k: series[k].astype(float).copy() for k in INDICATOR_KEYS}
        rate = max(missing_rate, 0.15 if incomplete else 0.0)
        if rate > 0:
            for k in INDICATOR_KEYS:
                mask = rng.random(days) < rate
                mask[:3] = False
                data[k][mask] = np.nan
        if incomplete:
            # Registros inválidos que llegan "del sensor": la ingesta debe rechazarlos
            for d in rng.choice(np.arange(20, days), size=6, replace=False):
                k = str(rng.choice(["rhr", "sleep", "hrv"]))
                bad = {"rhr": 0.0, "sleep": -1.0, "hrv": 999.0}[k]
                invalid.append({"astro_id": a["id"], "day": int(d), "indicator": k, "value": bad})
                data[k][int(d)] = np.nan

        for i in range(days):
            rows.append({"astro_id": a["id"], "day": i,
                         **{k: (None if np.isnan(data[k][i]) else round(float(data[k][i]), 3)) for k in INDICATOR_KEYS}})

    return pd.DataFrame(rows), pd.DataFrame(events, columns=["astro_id", "escenario", "nombre", "start", "end",
                                                              "afecta", "intensidad"]), invalid


def random_assignments(rng, crew=CREW, days: int = 120) -> tuple[dict, list]:
    """Asignación aleatoria para validación: cada astronauta recibe 0–2 escenarios con inicio aleatorio."""
    out = {}
    for a in crew:
        n = int(rng.choice([0, 1, 2], p=[0.2, 0.5, 0.3]))
        codes = rng.choice(["B", "C", "E"], size=n, replace=False).tolist()
        plan, cursor = [], int(rng.integers(22, 40))
        for c in codes:
            if cursor > days - 20:
                break
            plan.append({"escenario": c, "inicio": cursor})
            cursor += SCENARIOS[c]["dur"][1] + int(rng.integers(15, 25))
        out[a["id"]] = plan or [{"escenario": "A"}]
    crew_ev = [{"escenario": "D", "inicio": int(rng.integers(30, days - 10))}] if rng.random() < 0.6 else []
    return out, crew_ev

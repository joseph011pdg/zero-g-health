"""Capa de decisión (F7): reglas -> alertas explicables.

Cada alerta responde: qué cambió, cuánto, cómo se detectó, qué seguimiento se sugiere y qué
fuente lo respalda (con su nivel de evidencia). Las acciones son conservadoras y de seguimiento.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from .config import Params
from .detector import LEVELS, RANK
from .indicators import INDICATORS

HERE = Path(__file__).parent
RULES = json.loads((HERE / "recomendaciones.json").read_text(encoding="utf-8"))
EVIDENCE = {e["id"]: e for e in json.loads((HERE / "evidence.json").read_text(encoding="utf-8"))}
REASON_TXT = {"corte_rojo": "superó el corte rojo", "corte_amarillo": "superó el corte amarillo",
              "persistencia": "se mantuvo en amarillo varios días seguidos"}


def _num(x, nd=2):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), nd)


def change(key: str, row: pd.Series) -> dict:
    """Cuánto cambió un indicador respecto a su línea base (para la alerta y la interfaz)."""
    cfg = INDICATORS[key]
    val, med = float(row["value"]), _num(row["normal"], 3)
    diff = None if med is None else val - med
    return {
        "indicador": key, "nombre": cfg["nombre"], "unidad": cfg["unidad"],
        "valor": _num(val), "linea_base": _num(med), "dispersion_mad": _num(row["mad"]),
        "n_obs": None if pd.isna(row["n_obs"]) else int(row["n_obs"]), "referencia": row["base_ref"],
        "diferencia": _num(diff), "diferencia_pct": _num(100 * diff / med, 1) if diff is not None and med else None,
        "z": _num(row["z"]), "nivel": LEVELS[int(row["level"])], "motivo": row["reason"],
        "calidad_14d_pct": _num(100 * row["calidad"], 0),
    }


def _explain(c: dict) -> str:
    sentido = "por encima" if (c["diferencia"] or 0) > 0 else "por debajo"
    return (f"{c['nombre']}: {c['valor']} {c['unidad']} frente a una línea base de {c['linea_base']} {c['unidad']} "
            f"({abs(c['z'] or 0):.1f} desviaciones robustas {sentido} de lo habitual para esta persona).")


def _how(c: dict, p: Params) -> str:
    base = (f"z robusto = (valor − mediana) / (1,4826 × MAD) = {c['z']} usando {c['referencia']} "
            f"(n = {c['n_obs']} observaciones válidas, MAD escalado = {c['dispersion_mad']}). ")
    return base + f"Cortes: amarillo ≥ {p.yellow}, rojo ≥ {p.red} o {p.persist} días seguidos en amarillo; " \
                  f"{REASON_TXT.get(c['motivo'], '')}."


def _evidence(ids):
    return [{"id": i, "cita": EVIDENCE[i]["cita"], "tipo": EVIDENCE[i]["tipo"], "nivel": EVIDENCE[i]["nivel"],
             "url": EVIDENCE[i]["url"]} for i in ids if i in EVIDENCE]


def alerts_for_day(astro_id: str, results: dict[str, pd.DataFrame], day: int, p: Params) -> list[dict]:
    status = {k: LEVELS[int(r.loc[day, "level"])] for k, r in results.items()}
    used, alerts = set(), []

    def build(rule_id, nivel, titulo, mensaje, keys, acciones, evid):
        cambios = [change(k, results[k].loc[day]) for k in keys]
        calidad = min((c["calidad_14d_pct"] or 0) for c in cambios)
        acc = list(acciones) + ([RULES["escalado_rojo"]] if nivel == "rojo" else [])
        return {
            "id": f"{astro_id}-{day}-{rule_id}", "astro_id": astro_id, "day": day, "regla": rule_id,
            "nivel": nivel, "titulo": titulo, "que_cambio": mensaje, "cuanto": cambios,
            "como": " ".join(_how(c, p) for c in cambios), "acciones": acc, "evidencia": _evidence(evid),
            "calidad_datos_pct": calidad,
            "fiabilidad": "reducida: faltan datos recientes" if calidad < 70 else "normal",
            "aviso": RULES["aviso"], "indicadores": list(keys),
        }

    for rule in RULES["combinadas"]:
        req = rule["requiere"]
        if all(RANK[status[k]] >= RANK[v] for k, v in req.items()):
            nivel = "rojo" if any(status[k] == "rojo" for k in req) else "amarillo"
            a = build(rule["id"], nivel, rule["titulo"], rule["mensaje"], list(req), rule["acciones"],
                      rule["evidencia"])
            a["que_cambio"] += " " + " ".join(_explain(c) for c in a["cuanto"])
            alerts.append(a)
            used.update(req)

    for k, lvl in status.items():
        if lvl not in ("amarillo", "rojo") or k in used:
            continue
        r = RULES["individuales"][k][lvl]
        a = build(f"{k}_{lvl}", lvl, r["titulo"], "", [k], r["acciones"], r["evidencia"])
        a["que_cambio"] = _explain(a["cuanto"][0])
        alerts.append(a)
    alerts.sort(key=lambda a: -RANK[a["nivel"]])
    return alerts

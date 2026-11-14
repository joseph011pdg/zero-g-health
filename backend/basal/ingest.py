"""Capa de adquisición/datos (F2): validación y almacenamiento de mediciones.

Toda medición (simulador, formulario, CSV o PVT) pasa por `validate()`:
astronauta existente, indicador conocido, unidad aceptada, día dentro de la misión,
valor numérico y físicamente plausible. Los rechazos quedan registrados en ingest_log.
Esquema CSV (cabecera obligatoria):  astro_id,day,indicator,value,unit[,source]
"""
from __future__ import annotations

import csv
import io
import math

from . import db
from .indicators import INDICATORS, canonical_unit

SOURCES = {"sintetico", "manual", "csv", "pvt", "pvt_abreviada", "real"}
CSV_COLUMNS = ["astro_id", "day", "indicator", "value", "unit"]


def validate(rec: dict, astro_ids: set[str], days: int) -> tuple[dict | None, str | None]:
    """Devuelve (registro_normalizado, None) o (None, motivo_de_rechazo)."""
    a = str(rec.get("astro_id", "")).strip()
    if a not in astro_ids:
        return None, f"astronauta desconocido: '{a}'"
    k = str(rec.get("indicator", "")).strip()
    if k not in INDICATORS:
        return None, f"indicador desconocido: '{k}'"
    try:
        day = int(float(rec.get("day")))
    except (TypeError, ValueError):
        return None, "día ausente o no numérico"
    if not 0 <= day < days:
        return None, f"día fuera de la misión (0–{days - 1})"
    raw = rec.get("value")
    if raw is None or str(raw).strip() == "":
        return None, "valor ausente (la falta de dato no se interpreta como normal)"
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None, f"valor no numérico: '{raw}'"
    if math.isnan(value) or math.isinf(value):
        return None, "valor no numérico (NaN/inf)"
    unit = canonical_unit(k, rec.get("unit"))
    if unit is None:
        return None, f"unidad '{rec.get('unit')}' no válida para {k} (se espera {INDICATORS[k]['unidad']})"
    lo, hi = INDICATORS[k]["limits"]
    if not lo <= value <= hi:
        return None, f"valor físicamente imposible para {k}: {value} (rango {lo}–{hi})"
    source = str(rec.get("source") or "manual").strip().lower()
    if source not in SOURCES:
        return None, f"origen desconocido: '{source}'"
    return {"astro_id": a, "day": day, "indicator": k, "value": value, "unit": unit, "source": source}, None


def store(records: list[dict], overwrite: bool = True, log_ok: bool = True) -> dict:
    """Valida y guarda. Duplicados dentro del lote se rechazan; si ya existe un valor en la base,
    se reemplaza solo con overwrite=True (los datos manuales corrigen al sensor)."""
    m = db.get_mission()
    ids = {r["id"] for r in db.query("SELECT id FROM astronauts")}
    seen, ok, rejected, logs = set(), [], [], []
    for rec in records:
        norm, why = validate(rec, ids, m["days"])
        if norm:
            key = (norm["astro_id"], norm["day"], norm["indicator"])
            if key in seen:
                norm, why = None, "duplicado dentro del mismo lote"
            else:
                seen.add(key)
        if norm:
            ok.append(norm)
        else:
            rejected.append({**{k: rec.get(k) for k in ("astro_id", "day", "indicator", "value")}, "motivo": why})
            logs.append((rec.get("astro_id"), rec.get("day"), rec.get("indicator"), str(rec.get("value")),
                         rec.get("source"), "rechazado", why))
    inserted = replaced = duplicates = 0
    with db.tx() as con:
        for r in ok:
            old = con.execute("SELECT value FROM measurements WHERE astro_id=? AND day=? AND indicator=?",
                              (r["astro_id"], r["day"], r["indicator"])).fetchone()
            if old is not None and not overwrite:
                duplicates += 1
                why = "ya existe un valor para ese día (use 'sobrescribir')"
                rejected.append({**{k: r[k] for k in ("astro_id", "day", "indicator", "value")}, "motivo": why})
                logs.append((r["astro_id"], r["day"], r["indicator"], str(r["value"]), r["source"], "duplicado", why))
                continue
            con.execute("INSERT OR REPLACE INTO measurements (astro_id, day, indicator, value, unit, source) "
                        "VALUES (?,?,?,?,?,?)",
                        (r["astro_id"], r["day"], r["indicator"], r["value"], r["unit"], r["source"]))
            if old is None:
                inserted += 1
            else:
                replaced += 1
            if log_ok:
                logs.append((r["astro_id"], r["day"], r["indicator"], str(r["value"]), r["source"],
                             "aceptado" if old is None else "reemplazado", None))
        con.executemany("INSERT INTO ingest_log (astro_id, day, indicator, value, source, estado, motivo) "
                        "VALUES (?,?,?,?,?,?,?)", logs)
        if inserted or replaced:
            db.bump(con)
    return {"recibidos": len(records), "insertados": inserted, "reemplazados": replaced,
            "duplicados": duplicates, "rechazados": rejected}


def parse_csv(text: str, default_source: str = "csv") -> tuple[list[dict], str | None]:
    reader = csv.DictReader(io.StringIO(text.strip().lstrip("﻿")))
    cols = [c.strip() for c in (reader.fieldnames or [])]
    missing = [c for c in CSV_COLUMNS if c not in cols]
    if missing:
        return [], f"faltan columnas en la cabecera: {', '.join(missing)} (esquema: {','.join(CSV_COLUMNS)}[,source])"
    rows = []
    for r in reader:
        r = {(k or "").strip(): (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
        r["source"] = r.get("source") or default_source
        rows.append(r)
    return rows, None

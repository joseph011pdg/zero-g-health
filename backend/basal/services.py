"""Servicios: une datos (db), análisis (detector), decisión (recommender) y simulador.
Las rutas HTTP (main.py) solo llaman a estas funciones; la lógica científica no depende de FastAPI.
"""
from __future__ import annotations

import csv
import io
import json
import math
from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import db, ingest
from .config import load_params
from .detector import LEVELS, RANK, analyze_astronaut, global_level, health_index
from .indicators import INDICATORS, INDICATOR_KEYS
from .recommender import EVIDENCE, alerts_for_day, change
from .simulator import CREW, DEMO_ASSIGNMENTS, DEMO_CREW_EVENTS, POP, SCENARIOS, simulate_mission

MISSION_NAME = "BASAL-M1 · Tránsito a Marte (misión simulada)"
START_DATE = date(2035, 6, 1)
DAYS = 120
DEMO_DAY = 40  # la alarma del día 32 de A4 es un falso positivo del ruido: fuera de la ventana de 7 días
BLACKOUT = (95, 104)
NOMINAL_DOSE = POP["dose"][0]  # mGy/día del escenario simulado (supuesto)

PARAMS = load_params()
_cache: dict = {}
_synced: dict = {}


def reload_params():
    global PARAMS
    PARAMS = load_params()
    _cache.clear()
    _synced.clear()


# ---------------------------------------------------------------- inicialización
def init_db(reset: bool = False, seed: int = 7, assignments: dict | None = None,
            crew_events: list | None = None, blackout=BLACKOUT, current_day: int = DEMO_DAY) -> None:
    con = db.connect()
    if reset:
        db.drop_all(con)
    db.create_schema(con)
    empty = con.execute("SELECT COUNT(*) FROM astronauts").fetchone()[0] == 0
    if empty:
        assignments = assignments if assignments is not None else DEMO_ASSIGNMENTS
        crew_events = crew_events if crew_events is not None else DEMO_CREW_EVENTS
        con.execute("INSERT OR REPLACE INTO mission VALUES (1,?,?,?,?,?,?,?,?,0)",
                    (MISSION_NAME, START_DATE.isoformat(), DAYS, current_day, seed, blackout[0], blackout[1],
                     json.dumps({**assignments, "_crew": crew_events})))
        con.executemany("INSERT INTO astronauts (id, nombre, rol, ficticio) VALUES (?,?,?,1)",
                        [(a["id"], a["nombre"], a["rol"]) for a in CREW])
        ev = json.loads((__import__("pathlib").Path(__file__).parent / "evidence.json").read_text(encoding="utf-8"))
        con.executemany("INSERT OR REPLACE INTO evidence VALUES (?,?,?,?,?,?)",
                        [(e["id"], e["cita"], e["tipo"], e["nivel"], e["url"], e["en_propuesta"]) for e in ev])
        con.commit()
    con.close()
    _cache.clear()
    _synced.clear()
    if empty:
        _load_synthetic([a["id"] for a in CREW], seed)
        # Reporte de ejemplo ya en cola para la demo (última semana)
        create_report(None, max(0, current_day - 6), current_day)


def _load_synthetic(astro_ids: list[str], seed: int) -> dict:
    """Genera datos sintéticos para los astronautas indicados y los pasa por la ingesta (F2)."""
    m = db.get_mission()
    crew = [a for a in db.query("SELECT id, nombre, rol FROM astronauts") if a["id"] in astro_ids]
    assign = {k: v for k, v in m["assignments"].items() if k != "_crew"}
    daily, events, invalid = simulate_mission(days=m["days"], seed=seed, assignments=assign,
                                              crew_events=m["assignments"].get("_crew", []), crew=crew)
    recs = []
    for r in daily.to_dict("records"):
        for k in INDICATOR_KEYS:
            if r[k] is not None and not (isinstance(r[k], float) and math.isnan(r[k])):
                recs.append({"astro_id": r["astro_id"], "day": r["day"], "indicator": k, "value": r[k],
                             "unit": INDICATORS[k]["unidad"], "source": "sintetico"})
    recs += [{**x, "unit": INDICATORS[x["indicator"]]["unidad"], "source": "sintetico"} for x in invalid]
    with db.tx() as con:
        q = ",".join("?" * len(astro_ids))
        con.execute(f"DELETE FROM measurements WHERE source = 'sintetico' AND astro_id IN ({q})", astro_ids)
        con.execute(f"DELETE FROM sim_events WHERE astro_id IN ({q})", astro_ids)
        con.execute(f"DELETE FROM alerts WHERE estado = 'pendiente' AND astro_id IN ({q})", astro_ids)
        if len(events):
            con.executemany('INSERT INTO sim_events VALUES (?,?,?,?,?,?,?)',
                            [tuple(e.values()) for e in events.to_dict("records")])
        db.bump(con)
    return ingest.store(recs, overwrite=False, log_ok=False)


def set_astronaut_scenario(astro_id: str, plan: list[dict], seed: int | None = None) -> dict:
    m = db.get_mission()
    assign = m["assignments"]
    assign[astro_id] = plan
    db.execute("UPDATE mission SET assignments = ? WHERE id = 1", (json.dumps(assign),))
    seed = seed if seed is not None else m["seed"] + sum(map(ord, astro_id))
    # Las mediciones manuales del astronauta se conservan; solo se regeneran las sintéticas.
    return _load_synthetic([astro_id], seed)


# ---------------------------------------------------------------- análisis
def mission() -> dict:
    m = db.get_mission()
    d = m["current_day"]
    return {"nombre": m["nombre"], "dia": d, "dias": m["days"], "semilla": m["seed"],
            "fecha": (date.fromisoformat(m["fecha_inicio"]) + timedelta(days=d)).isoformat(),
            "fecha_inicio": m["fecha_inicio"], "apagon": [m["blackout_start"], m["blackout_end"]],
            "comunicacion": comms(d, m), "escenarios": m["assignments"],
            "parametros": {"yellow": PARAMS.yellow, "red": PARAMS.red, "persist": PARAMS.persist,
                           "window": PARAMS.window, "min_periods": PARAMS.min_periods, "origen": PARAMS.origen}}


def comms(day: int, m: dict) -> dict:
    """Modelo simplificado: retraso de 3 a 20 min por sentido a lo largo de la misión + apagón."""
    delay = round(3 + 17 * day / max(m["days"] - 1, 1), 1)
    forced = bool(m.get("forzar_apagon"))
    off = forced or (m["blackout_start"] is not None and m["blackout_start"] <= day <= m["blackout_end"])
    return {"retraso_min": delay, "ida_vuelta_min": round(2 * delay, 1), "apagon": off,
            "estado": "SIN ENLACE" if off else "Enlace diferido", "simulado": forced,
            "nota": "Simulación: no hay integración real con comunicaciones espaciales."}


def daily_frame(astro_id: str) -> pd.DataFrame:
    m = db.get_mission()
    rows = db.query("SELECT day, indicator, value, source FROM measurements WHERE astro_id = ?", (astro_id,))
    idx = pd.RangeIndex(m["days"], name="day")
    if not rows:
        return pd.DataFrame(np.nan, index=idx, columns=INDICATOR_KEYS)
    df = pd.DataFrame(rows)
    wide = df.pivot(index="day", columns="indicator", values="value").reindex(idx)
    for k in INDICATOR_KEYS:
        if k not in wide:
            wide[k] = np.nan
    return wide[INDICATOR_KEYS].astype(float)


def sources_frame(astro_id: str) -> pd.DataFrame:
    rows = db.query("SELECT day, indicator, source FROM measurements WHERE astro_id = ?", (astro_id,))
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).pivot(index="day", columns="indicator", values="source")


def analysis(astro_id: str) -> dict[str, pd.DataFrame]:
    key = (astro_id, db.data_version(), PARAMS.yellow, PARAMS.red)
    if key not in _cache:
        if len(_cache) > 64:
            _cache.clear()
        _cache[key] = analyze_astronaut(daily_frame(astro_id), PARAMS)
    return _cache[key]


def sync_alerts(astro_id: str) -> None:
    """Materializa las alertas en SQLite conservando el estado de revisión."""
    v = db.data_version()
    if _synced.get(astro_id) == (v, PARAMS.yellow, PARAMS.red):
        return
    res = analysis(astro_id)
    days = len(next(iter(res.values())))
    new = {}
    for d in range(days):
        for a in alerts_for_day(astro_id, res, d, PARAMS):
            new[a["id"]] = a
    with db.tx() as con:
        old = {r["id"]: r["estado"] for r in con.execute("SELECT id, estado FROM alerts WHERE astro_id = ?",
                                                         (astro_id,))}
        for i, a in new.items():
            con.execute("INSERT INTO alerts (id, astro_id, day, regla, nivel, titulo, indicadores, payload) "
                        "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET nivel=excluded.nivel, "
                        "titulo=excluded.titulo, payload=excluded.payload",
                        (i, astro_id, a["day"], a["regla"], a["nivel"], a["titulo"], ",".join(a["indicadores"]),
                         json.dumps(a, ensure_ascii=False)))
        gone = [i for i, st in old.items() if i not in new and st == "pendiente"]
        con.executemany("DELETE FROM alerts WHERE id = ?", [(i,) for i in gone])
    _synced[astro_id] = (v, PARAMS.yellow, PARAMS.red)


def rule_base(regla: str) -> str:
    """Tipo de alerta sin el nivel (fc_rojo -> fc): identifica el episodio."""
    for suf in ("_amarillo", "_rojo"):
        if regla.endswith(suf):
            return regla[: -len(suf)]
    return regla


ACK_STATES = {"reconocida", "revisada", "escalada", "descartada"}


def stored_alerts(astro_id: str | None = None, day_max: int | None = None, day_min: int = 0,
                  estado: str | None = None, day_eq: int | None = None) -> list[dict]:
    """Alertas guardadas con su estado efectivo:
    * una alerta pospuesta vuelve a 'pendiente' cuando pasa el día en que se pospuso;
    * dentro de un episodio (mismo tipo y nivel en días consecutivos) una alerta nueva hereda el
      reconocimiento del día anterior, para no pedir lo mismo cada día."""
    ids = [astro_id] if astro_id else [a["id"] for a in db.query("SELECT id FROM astronauts")]
    for i in ids:
        sync_alerts(i)
    today = db.get_mission()["current_day"]
    sql, args = "SELECT * FROM alerts WHERE 1 = 1", []
    if astro_id:
        sql += " AND astro_id = ?"; args.append(astro_id)
    rows = db.query(sql + " ORDER BY astro_id, regla, day", args)
    out, prev = [], {}
    for r in rows:
        a = json.loads(r["payload"])
        est = r["estado"]
        if est == "pospuesta" and r["revisado_dia"] is not None and today > r["revisado_dia"]:
            est = "pendiente"
        key = (r["astro_id"], rule_base(r["regla"]), r["nivel"])
        p = prev.get(key)
        heredada = False
        if est == "pendiente" and p and p["day"] == r["day"] - 1 and p["estado"] in ACK_STATES | {"pospuesta"}:
            est, heredada = p["estado"], True
        a.update(estado=est, nota=r["nota"] or (p["nota"] if heredada else None), revisado_ts=r["revisado_ts"],
                 revisor=r["revisor"] or (p["revisor"] if heredada else None),
                 revisado_dia=r["revisado_dia"] if r["revisado_dia"] is not None else (p["revisado_dia"] if heredada else None),
                 heredada=heredada, episodio=rule_base(r["regla"]))
        prev[key] = {"day": r["day"], "estado": est, "nota": a["nota"], "revisor": a["revisor"], "revisado_dia": a["revisado_dia"]}
        out.append(a)
    out = [a for a in out if a["day"] >= day_min and (day_max is None or a["day"] <= day_max)
           and (day_eq is None or a["day"] == day_eq) and (estado is None or a["estado"] == estado)]
    out.sort(key=lambda a: (-a["day"], -RANK[a["nivel"]]))
    return out


def review_alert(alert_id: str, estado: str, nota: str | None, revisor: str | None = None,
                 episodio: bool = True) -> dict | None:
    """Cambia el estado de una alerta. Con episodio=True se aplica también a las alertas anteriores del
    mismo tipo y astronauta que sigan pendientes (reconocer el episodio, no cada día por separado)."""
    r = db.one("SELECT * FROM alerts WHERE id = ?", (alert_id,))
    if not r:  # quizá aún no se materializaron (p. ej., justo después de reiniciar)
        for a in db.query("SELECT id FROM astronauts"):
            sync_alerts(a["id"])
        r = db.one("SELECT * FROM alerts WHERE id = ?", (alert_id,))
    if not r:
        return None
    today = db.get_mission()["current_day"]
    with db.tx() as con:
        targets = [alert_id]
        if episodio:
            base = rule_base(r["regla"])
            for o in con.execute("SELECT id, regla FROM alerts WHERE astro_id = ? AND day <= ? AND estado IN ('pendiente', 'pospuesta')",
                                 (r["astro_id"], r["day"])).fetchall():
                if rule_base(o["regla"]) == base:
                    targets.append(o["id"])
        con.executemany("UPDATE alerts SET estado = ?, nota = ?, revisor = ?, revisado_dia = ?, revisado_ts = CURRENT_TIMESTAMP "
                        "WHERE id = ?", [(estado, nota, revisor, today, t) for t in set(targets)])
    return next((a for a in stored_alerts(r["astro_id"]) if a["id"] == alert_id), None)


def _f(x, nd=2):
    return None if x is None or pd.isna(x) else round(float(x), nd)


def indicator_status(res, day: int, src: pd.DataFrame | None = None) -> dict:
    out = {}
    for k, r in res.items():
        row = r.loc[day]
        c = change(k, row) if not pd.isna(row["value"]) else {}
        spread = None if pd.isna(row["mad"]) else max(float(row["mad"]), INDICATORS[k]["min_spread"])
        d = INDICATORS[k]["direction"]
        out[k] = {
            "nivel": LEVELS[int(row["level"])], "valor": _f(row["value"]), "linea_base": _f(row["normal"]),
            "mad": _f(row["mad"]), "n_obs": None if pd.isna(row["n_obs"]) else int(row["n_obs"]),
            "ventana": PARAMS.window, "referencia": row["base_ref"] or None, "z": _f(row["z"]),
            "diferencia": c.get("diferencia"), "diferencia_pct": c.get("diferencia_pct"),
            "tendencia_dia": _f(row["tendencia"], 3), "calidad_14d_pct": _f(100 * row["calidad"], 0),
            "umbral_personal": None if spread is None else _f(row["normal"] + d * PARAMS.yellow * spread),
            "umbral_fijo": PARAMS.fixed[k],
            "fuente": None if src is None or src.empty or k not in src or day not in src.index
            or pd.isna(src.loc[day, k]) else src.loc[day, k],
        }
    return out


def radiation(res, day: int) -> dict:
    x = res["dose"]["value"].iloc[: day + 1]
    measured = float(x.sum(skipna=True))
    missing = int(x.isna().sum())
    expected = NOMINAL_DOSE * (day + 1)
    return {"acumulada_medida_mgy": round(measured, 2), "dias_sin_lectura": missing,
            "presupuesto_escenario_mgy": round(expected, 2),
            "porcentaje_del_presupuesto": round(100 * measured / expected, 1) if expected else None,
            "tasa_nominal": NOMINAL_DOSE, "dias": day + 1,
            "supuesto": f"Esperado a hoy en el escenario simulado: {str(NOMINAL_DOSE).replace('.', ',')} mGy/día × "
                        f"{day + 1} días = {str(round(expected, 1)).replace('.', ',')} mGy. Dosis absorbida (mGy), no dosis "
                        "equivalente (mSv). No es un límite de exposición de NASA; el acumulado se informa y no genera alarma."}


def crew() -> dict:
    m = db.get_mission()
    day = m["current_day"]
    out = []
    for a in db.query("SELECT * FROM astronauts ORDER BY id"):
        res = analysis(a["id"])
        al = stored_alerts(a["id"], day_eq=day)
        pend = sum(1 for x in stored_alerts(a["id"], day_max=day) if x["estado"] == "pendiente")
        st = indicator_status(res, day)
        q = [v["calidad_14d_pct"] for v in st.values() if v["calidad_14d_pct"] is not None]
        out.append({**a, "nivel": LEVELS[global_level(res, day)], "indice": health_index(res, day),
                    "indicadores": st, "alertas_hoy": len(al), "pendientes": pend,
                    "alerta_principal": al[0]["titulo"] if al else None,
                    "calidad_pct": round(sum(q) / len(q)) if q else 0})
    return {"dia": day, "tripulacion": out}


def astronaut(astro_id: str, desde: int = 0) -> dict | None:
    info = db.one("SELECT * FROM astronauts WHERE id = ?", (astro_id,))
    if not info:
        return None
    m = db.get_mission()
    day = m["current_day"]
    res = analysis(astro_id)
    src = sources_frame(astro_id)
    series = {}
    for k, r in res.items():
        d = INDICATORS[k]["direction"]
        pts = []
        for t in range(max(0, desde), day + 1):
            row = r.loc[t]
            spread = None if pd.isna(row["mad"]) else max(float(row["mad"]), INDICATORS[k]["min_spread"])
            pts.append({"day": t, "valor": _f(row["value"]), "normal": _f(row["normal"]), "z": _f(row["z"]),
                        "umbral": None if spread is None else _f(row["normal"] + d * PARAMS.yellow * spread),
                        "nivel": LEVELS[int(row["level"])], "fijo": int(row["fixed_alert"]),
                        "fuente": None if src.empty or k not in src or t not in src.index or pd.isna(src.loc[t, k])
                        else src.loc[t, k]})
        series[k] = pts
    hist = [{"day": t, "nivel": LEVELS[global_level(res, t)], "indice": health_index(res, t)}
            for t in range(max(0, desde), day + 1)]
    return {**info, "dia": day, "nivel": LEVELS[global_level(res, day)], "indice": health_index(res, day),
            "indicadores": indicator_status(res, day, src), "alertas": stored_alerts(astro_id, day_eq=day),
            "historial_alertas": stored_alerts(astro_id, day_max=day)[:60], "series": series, "historial": hist,
            "radiacion": radiation(res, day),
            "checkins": db.query("SELECT * FROM checkins WHERE astro_id=? ORDER BY id DESC LIMIT 30", (astro_id,)),
            "pvt": db.query("SELECT id, day, ts, modo, duracion_s, n_estimulos, rt_media, rt_mediana, lapsos, "
                            "anticipaciones, errores, errores_3min, interrupciones, valido, motivo_invalido "
                            "FROM pvt_tests WHERE astro_id=? ORDER BY id DESC LIMIT 30", (astro_id,))}


# ---------------------------------------------------------------- PVT y check-in
LAPSE_MS, FALSE_START_MS = 355, 100  # definiciones PVT-B (Basner et al., 2011)


def save_pvt(astro_id: str, modo: str, duracion_s: float, rts: list[float], anticipaciones: int,
             interrupciones: int, sin_respuesta: int, persist: bool = True) -> dict:
    day = db.get_mission()["current_day"]
    valid_rts = [r for r in rts if r >= FALSE_START_MS]
    fast = [r for r in rts if r < FALSE_START_MS]  # respuestas < 100 ms = anticipación
    lapsos = sum(1 for r in valid_rts if r >= LAPSE_MS) + sin_respuesta
    antic = anticipaciones + len(fast)
    errores = lapsos + antic
    n = len(rts) + sin_respuesta
    motivo = None
    if interrupciones > 0:
        motivo = f"prueba interrumpida {interrupciones} vez/veces (pérdida de foco)"
    elif n < 5:
        motivo = "muy pocos estímulos para ser interpretable"
    valido = motivo is None
    scale = 180.0 / duracion_s if duracion_s > 0 else 1.0
    errores_3min = round(errores * scale, 1)
    srt = sorted(valid_rts)
    slow10 = float(np.mean(srt[-max(1, len(srt) // 10):])) if srt else None
    if not persist:  # demo pública: se calcula el resultado pero no se guarda
        return {"id": None, "dia": day, "valido": valido, "motivo_invalido": motivo, "lapsos": lapsos,
                "anticipaciones": antic, "errores": errores, "errores_equivalentes_3min": errores_3min,
                "guardado_en_indicador": False, "demo_publica": True}
    with db.tx() as con:
        cur = con.execute(
            "INSERT INTO pvt_tests (astro_id, day, modo, duracion_s, n_estimulos, rt_media, rt_mediana, rt_lenta10, "
            "lapsos, anticipaciones, errores, errores_3min, interrupciones, valido, motivo_invalido, rts) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (astro_id, day, modo, duracion_s, n, _f(np.mean(valid_rts), 1) if valid_rts else None,
             _f(np.median(valid_rts), 1) if valid_rts else None, _f(slow10, 1), lapsos, antic, errores,
             errores_3min, interrupciones, int(valido), motivo, json.dumps(rts)))
        test_id = cur.lastrowid
    stored = None
    if valido:
        source = "pvt" if modo == "pvtb_3min" else "pvt_abreviada"
        stored = ingest.store([{"astro_id": astro_id, "day": day, "indicator": "pvt", "value": errores_3min,
                                "unit": "errores", "source": source}])
    return {"id": test_id, "dia": day, "valido": valido, "motivo_invalido": motivo, "lapsos": lapsos,
            "anticipaciones": antic, "errores": errores, "errores_equivalentes_3min": errores_3min,
            "guardado_en_indicador": bool(stored and (stored["insertados"] or stored["reemplazados"]))}


def save_checkin(astro_id: str, animo: float, calidad_sueno: int, notas: str | None, segundos: float | None) -> dict:
    day = db.get_mission()["current_day"]
    with db.tx() as con:
        con.execute("INSERT INTO checkins (astro_id, day, animo, calidad_sueno, notas, segundos) VALUES (?,?,?,?,?,?)",
                    (astro_id, day, animo, calidad_sueno, notas, segundos))
    r = ingest.store([{"astro_id": astro_id, "day": day, "indicator": "mood", "value": animo,
                       "unit": "/10", "source": "manual"}])
    return {"dia": day, **r}


# ---------------------------------------------------------------- reportes (F10)
def build_report(astro_id: str | None, desde: int, hasta: int) -> dict:
    m = db.get_mission()
    ids = [astro_id] if astro_id else [a["id"] for a in db.query("SELECT id FROM astronauts ORDER BY id")]
    people = []
    for i in ids:
        info = db.one("SELECT id, nombre, rol FROM astronauts WHERE id = ?", (i,))
        res = analysis(i)
        ind = {}
        for k, r in res.items():
            w = r.iloc[desde: hasta + 1]
            vals = w["value"].dropna()
            ind[k] = {"nombre": INDICATORS[k]["nombre"], "unidad": INDICATORS[k]["unidad"],
                      "n_validos": int(len(vals)), "dias": int(len(w)),
                      "completitud_pct": round(100 * len(vals) / max(len(w), 1), 1),
                      "media": _f(vals.mean()), "min": _f(vals.min()), "max": _f(vals.max()),
                      "ultimo_valor": _f(r.loc[hasta, "value"]), "linea_base_final": _f(r.loc[hasta, "normal"]),
                      "z_max": _f(w["z"].max()),
                      "dias_amarillo": int((w["level"] == 1).sum()), "dias_rojo": int((w["level"] == 2).sum())}
        al = [a for a in stored_alerts(i, day_max=hasta, day_min=desde)]
        rejected = db.one("SELECT COUNT(*) n FROM ingest_log WHERE astro_id=? AND estado='rechazado' "
                          "AND day BETWEEN ? AND ?", (i, desde, hasta))["n"]
        cambios = sorted([(k, v["z_max"]) for k, v in ind.items() if v["z_max"] is not None],
                         key=lambda x: -x[1])[:3]
        people.append({
            "astronauta": info, "nivel_final": LEVELS[global_level(res, hasta)],
            "indice_final": health_index(res, hasta), "indicadores": ind,
            "cambios_relevantes": [f"{INDICATORS[k]['nombre']}: z máximo {z}" for k, z in cambios if z >= PARAMS.yellow],
            "alertas": [{"id": a["id"], "dia": a["day"], "nivel": a["nivel"], "titulo": a["titulo"],
                         "estado": a["estado"], "nota": a["nota"]} for a in al],
            "calidad_datos": {"registros_rechazados": rejected,
                              "completitud_media_pct": round(np.mean([v["completitud_pct"] for v in ind.values()]), 1)},
            "seguimiento": {"alertas_revisadas": sum(a["estado"] != "pendiente" for a in al),
                            "alertas_pendientes": sum(a["estado"] == "pendiente" for a in al),
                            "checkins": db.one("SELECT COUNT(*) n FROM checkins WHERE astro_id=? AND day BETWEEN ? AND ?",
                                               (i, desde, hasta))["n"],
                            "pruebas_pvt": db.one("SELECT COUNT(*) n FROM pvt_tests WHERE astro_id=? AND day BETWEEN ? AND ?",
                                                  (i, desde, hasta))["n"]},
            "radiacion": radiation(res, hasta),
        })
    return {"tipo": "Reporte de salud para envío diferido a la Tierra",
            "mision": m["nombre"], "periodo": {"desde": desde, "hasta": hasta},
            "generado_dia": m["current_day"], "parametros_detector": {"yellow": PARAMS.yellow, "red": PARAMS.red,
                                                                      "persist": PARAMS.persist, "window": PARAMS.window},
            "aviso": "Prototipo educativo con datos sintéticos. No es un dispositivo médico.",
            "tripulantes": people}


def create_report(astro_id: str | None, desde: int, hasta: int, persist: bool = True) -> dict:
    m = db.get_mission()
    hasta = min(hasta, m["current_day"])
    desde = max(0, min(desde, hasta))
    content = build_report(astro_id, desde, hasta)
    if not persist:  # demo pública: vista previa sin guardar
        return {"id": None, "astro_id": astro_id, "desde": desde, "hasta": hasta, "dia_creacion": m["current_day"],
                "estado": "vista previa", "dia_envio": None, "contenido": content}
    rid = db.execute("INSERT INTO reports (astro_id, desde, hasta, dia_creacion, contenido) VALUES (?,?,?,?,?)",
                     (astro_id, desde, hasta, m["current_day"], json.dumps(content, ensure_ascii=False)))
    return get_report(rid)


def get_report(rid: int) -> dict | None:
    r = db.one("SELECT * FROM reports WHERE id = ?", (rid,))
    if not r:
        return None
    r["contenido"] = json.loads(r["contenido"])
    return r


def list_reports() -> list[dict]:
    return db.query("SELECT id, creado, astro_id, desde, hasta, dia_creacion, estado, dia_envio FROM reports "
                    "ORDER BY id DESC")


def transmit(dry: bool = False) -> dict:
    m = db.get_mission()
    c = comms(m["current_day"], m)
    pending = db.query("SELECT id FROM reports WHERE estado = 'pendiente'")
    if c["apagon"]:
        return {"enviados": 0, "en_cola": len(pending), "comunicacion": c,
                "mensaje": "Sin enlace con la Tierra: los reportes permanecen en la cola local."}
    if not dry:
        with db.tx() as con:
            con.execute("UPDATE reports SET estado = 'enviado (simulado)', dia_envio = ? WHERE estado = 'pendiente'",
                        (m["current_day"],))
    return {"enviados": len(pending), "en_cola": 0, "comunicacion": c,
            "mensaje": f"Envío SIMULADO: llegarían a la Tierra en ~{c['retraso_min']} min."}


def report_csv(rid: int) -> str | None:
    r = get_report(rid)
    if not r:
        return None
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["seccion", "astro_id", "clave", "campo", "valor"])
    c = r["contenido"]
    w.writerow(["mision", "", "", "nombre", c["mision"]])
    w.writerow(["mision", "", "", "periodo", f"{c['periodo']['desde']}-{c['periodo']['hasta']}"])
    for p in c["tripulantes"]:
        a = p["astronauta"]["id"]
        w.writerow(["estado", a, "", "nivel_final", p["nivel_final"]])
        w.writerow(["estado", a, "", "indice_final", p["indice_final"]])
        for k, v in p["indicadores"].items():
            for f, x in v.items():
                w.writerow(["indicador", a, k, f, x])
        for al in p["alertas"]:
            w.writerow(["alerta", a, al["id"], "nivel|estado|titulo", f"{al['nivel']}|{al['estado']}|{al['titulo']}"])
        for f, x in {**p["calidad_datos"], **p["seguimiento"]}.items():
            w.writerow(["calidad_seguimiento", a, "", f, x])
        w.writerow(["radiacion", a, "", "acumulada_medida_mgy", p["radiacion"]["acumulada_medida_mgy"]])
    return buf.getvalue()


def evidence() -> list[dict]:
    return list(EVIDENCE.values())


def scenarios() -> dict:
    return SCENARIOS


def events(astro_id: str | None = None) -> list[dict]:
    if astro_id:
        return db.query('SELECT * FROM sim_events WHERE astro_id = ? ORDER BY start', (astro_id,))
    return db.query('SELECT * FROM sim_events ORDER BY astro_id, start')


def demo_validation() -> dict:
    """Resultados por astronauta en la misión cargada (datos actuales vs. eventos del simulador)."""
    from .validation import _summ, evaluate
    m = db.get_mission()
    frames = []
    for a in db.query("SELECT id FROM astronauts ORDER BY id"):
        f = daily_frame(a["id"]).reset_index()
        f.insert(0, "astro_id", a["id"])
        frames.append(f)
    ev_rows = events()
    evdf = pd.DataFrame(ev_rows, columns=["astro_id", "escenario", "nombre", "start", "end", "afecta", "intensidad"])
    ev, dy = evaluate([{"seed": m["seed"], "daily": pd.concat(frames), "events": evdf}], PARAMS)
    out = {}
    for a in db.query("SELECT id, nombre FROM astronauts ORDER BY id"):
        e, d = ev[ev.astro_id == a["id"]] if len(ev) else ev, dy[dy.astro_id == a["id"]]
        out[a["id"]] = {"nombre": a["nombre"],
                        "eventos": [x for x in ev_rows if x["astro_id"] == a["id"]],
                        "metodos": {meth: _summ(e[e.metodo == meth] if len(e) else e, d[d.metodo == meth])
                                    for meth in ("A_vigilar", "A_actuar", "B_fijo")}}
    return {"semilla": m["seed"], "dias": m["days"], "por_astronauta": out,
            "nota": "Una sola misión: sirve para ilustrar, no para concluir. La conclusión sale de la evaluación con 40 misiones."}

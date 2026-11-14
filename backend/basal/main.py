"""API local de BASAL (FastAPI). Documentación OpenAPI en /docs.

Ejecutar:  uvicorn basal.main:app --host 127.0.0.1 --port 8000
Por seguridad escucha solo en 127.0.0.1 (no expone datos a la red) y CORS solo admite el
servidor de desarrollo local. Si existe frontend/dist, también sirve la interfaz (un solo origen).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import db, ingest, services
from .config import VALIDATION_PATH
from .indicators import INDICATORS
from .simulator import EVENT_SCENARIOS, SCENARIOS

app = FastAPI(title="BASAL · Monitoreo de salud autónomo", version="2.0",
              description="Prototipo educativo con datos sintéticos. No es un dispositivo médico.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])
services.init_db()

# Modo público (demo en línea, p. ej. Render): BASAL_PUBLIC=1. El estado es compartido entre visitantes,
# así que se bloquean las acciones que alteran la misión para todos y se limita el cómputo pesado.
PUBLIC = os.environ.get("BASAL_PUBLIC", "0") == "1"


def _forbid_in_public(what: str):
    if PUBLIC:
        raise HTTPException(403, f"{what} está deshabilitado en la demo pública en línea. "
                                 "Ejecute BASAL localmente (.\\scripts\\start.ps1) para usarlo.")


def _astro_or_404(astro_id: str):
    if not db.one("SELECT id FROM astronauts WHERE id = ?", (astro_id,)):
        raise HTTPException(404, f"Astronauta '{astro_id}' no encontrado")


# ------------------------------------------------------------------ sistema
@app.get("/api/health", tags=["sistema"])
def health():
    return {"ok": True, "modo": "publico" if PUBLIC else "local", "publico": PUBLIC, "version_datos": db.data_version(),
            "validacion_precalculada": VALIDATION_PATH.exists()}


@app.get("/api/indicators", tags=["sistema"])
def indicators():
    return {k: {**{x: v for x, v in cfg.items() if x != "limits"}, "limites": list(cfg["limits"]),
                "umbral_fijo": services.PARAMS.fixed[k]} for k, cfg in INDICATORS.items()}


@app.get("/api/evidence", tags=["sistema"])
def evidence():
    return services.evidence()


# ------------------------------------------------------------------ misión y simulador (F9)
@app.get("/api/mission", tags=["misión"])
def mission():
    return services.mission()


class DayIn(BaseModel):
    day: int = Field(ge=0)


@app.post("/api/mission/day", tags=["misión"])
def set_day(body: DayIn):
    m = db.get_mission()
    db.execute("UPDATE mission SET current_day = ? WHERE id = 1", (min(body.day, m["days"] - 1),))
    return services.mission()


class AdvanceIn(BaseModel):
    n: int = Field(default=1, ge=-120, le=120)


@app.post("/api/mission/advance", tags=["misión"])
def advance(body: AdvanceIn):
    m = db.get_mission()
    return set_day(DayIn(day=max(0, min(m["current_day"] + body.n, m["days"] - 1))))


class PlanItem(BaseModel):
    escenario: Literal["A", "B", "C", "D", "E", "G"]
    inicio: int | None = Field(default=None, ge=0, le=119)
    intensidad: float | None = Field(default=None, ge=0.2, le=3.0)


class ResetIn(BaseModel):
    seed: int = Field(default=7, ge=0, le=10**6)
    demo: bool = True
    apagon_inicio: int | None = Field(default=95, ge=0, le=119)
    apagon_fin: int | None = Field(default=104, ge=0, le=119)
    dia: int = Field(default=services.DEMO_DAY, ge=0, le=119)


@app.post("/api/sim/reset", tags=["simulador"])
def sim_reset(body: ResetIn):
    """Reinicia la misión de demostración (borra datos manuales, alertas y reportes)."""
    if PUBLIC:  # en la demo pública solo se permite volver al escenario canónico
        body = ResetIn()
    bo = (body.apagon_inicio, body.apagon_fin) if body.apagon_inicio is not None else (None, None)
    services.init_db(reset=True, seed=body.seed, blackout=bo, current_day=body.dia)
    return services.mission()


class ScenarioIn(BaseModel):
    astro_id: str
    plan: list[PlanItem]
    seed: int | None = None


@app.post("/api/sim/astronaut", tags=["simulador"])
def sim_astronaut(body: ScenarioIn):
    """Asigna escenarios a un astronauta y regenera solo sus datos sintéticos."""
    _forbid_in_public("Cambiar escenarios")
    _astro_or_404(body.astro_id)
    r = services.set_astronaut_scenario(body.astro_id, [p.model_dump(exclude_none=True) for p in body.plan],
                                        body.seed)
    return {"ingesta": {k: v for k, v in r.items() if k != "rechazados"}, "rechazados": r["rechazados"][:20],
            "eventos": services.events(body.astro_id)}


class BlackoutIn(BaseModel):
    inicio: int | None = Field(default=None, ge=0, le=119)
    fin: int | None = Field(default=None, ge=0, le=119)


@app.post("/api/sim/blackout", tags=["simulador"])
def sim_blackout(body: BlackoutIn):
    """Escenario F: define (o elimina) la ventana de interrupción de comunicaciones."""
    _forbid_in_public("Cambiar el apagón")
    if body.inicio is not None and (body.fin is None or body.fin < body.inicio):
        raise HTTPException(422, "El fin del apagón debe ser mayor o igual que el inicio")
    db.execute("UPDATE mission SET blackout_start = ?, blackout_end = ? WHERE id = 1", (body.inicio, body.fin))
    return services.mission()


@app.get("/api/sim/scenarios", tags=["simulador"])
def sim_scenarios():
    return {"escenarios": SCENARIOS, "con_evento": EVENT_SCENARIOS,
            "mision": {"F": "Interrupción de comunicaciones (ventana de apagón configurable)"}}


@app.get("/api/events", tags=["simulador"])
def events(astro_id: str | None = None):
    """Eventos inyectados por el simulador (la 'verdad'; solo para la demo y la validación)."""
    return services.events(astro_id)


# ------------------------------------------------------------------ astronautas (F1)
@app.get("/api/crew", tags=["astronautas"])
def crew():
    return services.crew()


class AstronautIn(BaseModel):
    id: str = Field(min_length=2, max_length=8, pattern=r"^[A-Za-z0-9_-]+$")
    nombre: str = Field(min_length=2, max_length=60)
    rol: str = Field(min_length=2, max_length=40)
    edad: int | None = Field(default=None, ge=18, le=80)
    notas: str | None = Field(default=None, max_length=300)
    generar_datos: Literal["ninguno", "A", "B", "C", "E"] = "ninguno"


@app.post("/api/astronauts", tags=["astronautas"], status_code=201)
def create_astronaut(body: AstronautIn):
    _forbid_in_public("Crear perfiles")
    if db.one("SELECT id FROM astronauts WHERE id = ?", (body.id,)):
        raise HTTPException(409, f"Ya existe un astronauta con id '{body.id}'")
    db.execute("INSERT INTO astronauts (id, nombre, rol, edad, notas, ficticio) VALUES (?,?,?,?,?,1)",
               (body.id, body.nombre, body.rol, body.edad, body.notas))
    if body.generar_datos != "ninguno":
        plan = [{"escenario": body.generar_datos}]
        if body.generar_datos != "A":
            plan[0]["inicio"] = 45
        services.set_astronaut_scenario(body.id, plan)
    return services.astronaut(body.id)


@app.get("/api/astronauts/{astro_id}", tags=["astronautas"])
def astronaut(astro_id: str, desde: int = Query(0, ge=0)):
    a = services.astronaut(astro_id, desde)
    if not a:
        raise HTTPException(404, f"Astronauta '{astro_id}' no encontrado")
    return a


# ------------------------------------------------------------------ ingesta (F2)
class MeasurementIn(BaseModel):
    astro_id: str
    indicator: str
    value: float
    unit: str | None = None
    day: int | None = None
    source: Literal["manual", "real", "csv"] = "manual"


@app.post("/api/measurements", tags=["ingesta"])
def post_measurement(body: MeasurementIn):
    rec = body.model_dump()
    if rec["day"] is None:
        rec["day"] = db.get_mission()["current_day"]
    r = ingest.store([rec], overwrite=True)
    if r["rechazados"]:
        raise HTTPException(422, r["rechazados"][0]["motivo"])
    return r


class CsvIn(BaseModel):
    csv: str = Field(max_length=2_000_000)
    sobrescribir: bool = False


@app.post("/api/ingest/csv", tags=["ingesta"])
def ingest_csv(body: CsvIn):
    rows, err = ingest.parse_csv(body.csv)
    if err:
        raise HTTPException(422, err)
    if not rows:
        raise HTTPException(422, "El archivo no contiene filas de datos")
    return ingest.store(rows, overwrite=body.sobrescribir)


@app.get("/api/ingest/log", tags=["ingesta"])
def ingest_log(limit: int = Query(100, ge=1, le=1000), estado: str | None = None):
    sql, args = "SELECT * FROM ingest_log", []
    if estado:
        sql += " WHERE estado = ?"; args.append(estado)
    return db.query(sql + " ORDER BY id DESC LIMIT ?", (*args, limit))


@app.get("/api/ingest/schema", tags=["ingesta"])
def csv_schema():
    return {"columnas": ingest.CSV_COLUMNS + ["source (opcional)"],
            "indicadores": {k: {"unidad": v["unidad"], "alias": v["units"], "rango": list(v["limits"])}
                            for k, v in INDICATORS.items()},
            "origenes": sorted(ingest.SOURCES),
            "ejemplo": "astro_id,day,indicator,value,unit,source\nA1,10,rhr,61,lpm,csv\nA1,10,sleep,6.8,h,csv"}


# ------------------------------------------------------------------ PVT-B (F3) y check-in (F4)
class PvtIn(BaseModel):
    modo: Literal["pvtb_3min", "abreviada_60s"]
    duracion_s: float = Field(gt=0, le=600)
    rts: list[float] = Field(default_factory=list, max_length=500)
    anticipaciones: int = Field(default=0, ge=0, le=500)
    sin_respuesta: int = Field(default=0, ge=0, le=500)
    interrupciones: int = Field(default=0, ge=0, le=100)


@app.post("/api/astronauts/{astro_id}/pvt", tags=["registro"])
def post_pvt(astro_id: str, body: PvtIn):
    _astro_or_404(astro_id)
    if any(r < 0 or r > 30000 for r in body.rts):
        raise HTTPException(422, "Tiempos de reacción fuera de rango")
    return services.save_pvt(astro_id, body.modo, body.duracion_s, body.rts, body.anticipaciones,
                             body.interrupciones, body.sin_respuesta)


class CheckinIn(BaseModel):
    animo: float = Field(ge=1, le=10)
    calidad_sueno: int = Field(ge=1, le=5)
    notas: str | None = Field(default=None, max_length=500)
    segundos: float | None = Field(default=None, ge=0, le=3600)


@app.post("/api/astronauts/{astro_id}/checkin", tags=["registro"])
def post_checkin(astro_id: str, body: CheckinIn):
    _astro_or_404(astro_id)
    return services.save_checkin(astro_id, body.animo, body.calidad_sueno, body.notas, body.segundos)


# ------------------------------------------------------------------ alertas (F7)
@app.get("/api/alerts", tags=["alertas"])
def alerts(astro_id: str | None = None, estado: str | None = None, todas: bool = False):
    day = db.get_mission()["current_day"]
    return services.stored_alerts(astro_id, day_max=day, estado=estado)[: (2000 if todas else 200)]


class ReviewIn(BaseModel):
    estado: Literal["pendiente", "revisada", "escalada", "descartada"]
    nota: str | None = Field(default=None, max_length=500)


@app.patch("/api/alerts/{alert_id}", tags=["alertas"])
def review(alert_id: str, body: ReviewIn):
    a = services.review_alert(alert_id, body.estado, body.nota)
    if not a:
        raise HTTPException(404, "Alerta no encontrada")
    return a


# ------------------------------------------------------------------ reportes (F10)
class ReportIn(BaseModel):
    astro_id: str | None = None
    desde: int = Field(default=0, ge=0)
    hasta: int = Field(default=119, ge=0)


@app.post("/api/reports", tags=["reportes"], status_code=201)
def create_report(body: ReportIn):
    if body.astro_id:
        _astro_or_404(body.astro_id)
    if body.hasta < body.desde:
        raise HTTPException(422, "'hasta' debe ser mayor o igual que 'desde'")
    return services.create_report(body.astro_id, body.desde, body.hasta)


@app.get("/api/reports", tags=["reportes"])
def reports():
    return services.list_reports()


@app.get("/api/reports/{rid}", tags=["reportes"])
def report(rid: int):
    r = services.get_report(rid)
    if not r:
        raise HTTPException(404, "Reporte no encontrado")
    return r


@app.get("/api/reports/{rid}/csv", tags=["reportes"], response_class=PlainTextResponse)
def report_csv(rid: int):
    c = services.report_csv(rid)
    if c is None:
        raise HTTPException(404, "Reporte no encontrado")
    return PlainTextResponse(c, media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="reporte_{rid}.csv"'})


@app.post("/api/reports/transmit", tags=["reportes"])
def transmit():
    return services.transmit()


# ------------------------------------------------------------------ validación
@app.get("/api/validation", tags=["validación"])
def validation():
    if not VALIDATION_PATH.exists():
        raise HTTPException(404, "No hay validación precalculada. Ejecute: python -m basal.validation")
    return json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))


class ValidationRunIn(BaseModel):
    n_misiones: int = Field(default=10, ge=1, le=30)
    semilla_inicial: int = Field(default=3000, ge=0, le=10**6)
    escenario: Literal["B", "C", "D", "E"] | None = None
    heterogeneidad: float = Field(default=1.0, ge=0.1, le=3.0)
    faltantes: float = Field(default=0.0, ge=0.0, le=0.5)
    yellow: float | None = Field(default=None, ge=1.0, le=6.0)
    red: float | None = Field(default=None, ge=1.5, le=8.0)


@app.post("/api/validation/run", tags=["validación"])
def validation_run(body: ValidationRunIn):
    from dataclasses import replace
    from .validation import run_custom
    if PUBLIC and body.n_misiones > 10:
        raise HTTPException(403, "En la demo pública el máximo es 10 misiones por experimento.")
    p = services.PARAMS
    p = replace(p, yellow=body.yellow or p.yellow, red=body.red or p.red)
    if p.red <= p.yellow:
        raise HTTPException(422, "El corte rojo debe ser mayor que el amarillo")
    return run_custom(p, body.n_misiones, body.semilla_inicial, body.escenario, body.heterogeneidad, body.faltantes)


@app.get("/api/validation/demo", tags=["validación"])
def validation_demo():
    return services.demo_validation()


# ------------------------------------------------------------------ interfaz compilada (un solo origen)
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Ruta de API no encontrada")
        f = (DIST / path).resolve()
        if path and f.is_file() and DIST in f.parents and re.match(r"^[\w./-]+$", path):
            return FileResponse(f)
        return FileResponse(DIST / "index.html")

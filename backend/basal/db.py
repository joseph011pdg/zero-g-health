"""Capa de datos: SQLite local (sin servidor, funciona sin conexión).

Inicialización reproducible: `init_db()` crea el esquema si no existe y, si la base está vacía,
carga la misión de demostración generada por el simulador (semilla fija).
Las mediciones se guardan en formato largo (una fila por astronauta, día e indicador) para
poder registrar el ORIGEN de cada dato (sintetico | manual | csv | pvt | real).
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.environ.get("BASAL_DB", Path(__file__).resolve().parent.parent / "basal.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS mission (
    id INTEGER PRIMARY KEY CHECK (id = 1), nombre TEXT, fecha_inicio TEXT, days INTEGER,
    current_day INTEGER, seed INTEGER, blackout_start INTEGER, blackout_end INTEGER,
    assignments TEXT, running INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS astronauts (
    id TEXT PRIMARY KEY, nombre TEXT NOT NULL, rol TEXT, edad INTEGER, notas TEXT,
    ficticio INTEGER DEFAULT 1, creado TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS measurements (
    astro_id TEXT NOT NULL REFERENCES astronauts(id), day INTEGER NOT NULL, indicator TEXT NOT NULL,
    value REAL NOT NULL, unit TEXT NOT NULL, source TEXT NOT NULL, registrado TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (astro_id, day, indicator));
CREATE TABLE IF NOT EXISTS ingest_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT CURRENT_TIMESTAMP, astro_id TEXT, day INTEGER,
    indicator TEXT, value TEXT, source TEXT, estado TEXT, motivo TEXT);
CREATE TABLE IF NOT EXISTS sim_events (
    astro_id TEXT, escenario TEXT, nombre TEXT, start INTEGER, "end" INTEGER, afecta TEXT, intensidad REAL);
CREATE TABLE IF NOT EXISTS pvt_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT, astro_id TEXT, day INTEGER, ts TEXT DEFAULT CURRENT_TIMESTAMP,
    modo TEXT, duracion_s REAL, n_estimulos INTEGER, rt_media REAL, rt_mediana REAL, rt_lenta10 REAL,
    lapsos INTEGER, anticipaciones INTEGER, errores INTEGER, errores_3min REAL, interrupciones INTEGER,
    valido INTEGER, motivo_invalido TEXT, rts TEXT);
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT, astro_id TEXT, day INTEGER, ts TEXT DEFAULT CURRENT_TIMESTAMP,
    animo REAL, calidad_sueno INTEGER, notas TEXT, segundos REAL);
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY, astro_id TEXT, day INTEGER, regla TEXT, nivel TEXT, titulo TEXT,
    indicadores TEXT, payload TEXT, estado TEXT DEFAULT 'pendiente', nota TEXT, revisado_ts TEXT);
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT, creado TEXT DEFAULT CURRENT_TIMESTAMP, astro_id TEXT,
    desde INTEGER, hasta INTEGER, dia_creacion INTEGER, estado TEXT DEFAULT 'pendiente',
    dia_envio INTEGER, contenido TEXT);
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY, cita TEXT, tipo TEXT, nivel TEXT, url TEXT, en_propuesta INTEGER);
"""


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


@contextmanager
def tx():
    con = connect()
    try:
        yield con
        con.commit()
    finally:
        con.close()


def query(sql: str, params=()) -> list[dict]:
    with tx() as con:
        return [dict(r) for r in con.execute(sql, params).fetchall()]


def one(sql: str, params=()) -> dict | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params=(), invalidate: bool = False) -> int:
    """Escritura simple. `invalidate=True` solo si cambian mediciones (invalida la caché del análisis)."""
    with tx() as con:
        cur = con.execute(sql, params)
        if invalidate:
            bump(con)
        return cur.lastrowid


def bump(con) -> None:
    """Incrementa la versión de datos (invalida la caché del análisis)."""
    con.execute("INSERT INTO meta VALUES ('version', '1') ON CONFLICT(key) DO UPDATE SET value = value + 1")


def data_version() -> int:
    r = one("SELECT value FROM meta WHERE key = 'version'")
    return int(r["value"]) if r else 0


def create_schema(con) -> None:
    con.executescript(SCHEMA)


def drop_all(con) -> None:
    for t in ("meta", "mission", "measurements", "ingest_log", "sim_events", "pvt_tests", "checkins",
              "alerts", "reports", "astronauts", "evidence"):
        con.execute(f"DROP TABLE IF EXISTS {t}")


def get_mission() -> dict:
    m = one("SELECT * FROM mission WHERE id = 1")
    if m:
        m["assignments"] = json.loads(m["assignments"] or "{}")
    return m

"""Validación científica: línea base individual (método A) vs. referencia poblacional fija (método B).

Definiciones (también en SCIENTIFIC_METHOD.md):
  * Evento verdadero: desviación inyectada por el simulador (escenarios B, C, D, E) con inicio,
    fin e indicadores afectados conocidos.
  * Detección: al menos una alerta en un indicador afectado entre el inicio y fin + 2 días.
  * Retraso: días desde el inicio del evento hasta la primera alerta (0 = el mismo día).
  * Anticipación A vs B: retraso(B) − retraso(A) en eventos que ambos detectan.
  * Día sano: día ≥ 14 (fin de la calibración) fuera de [inicio − 1, fin + 7] de todo evento.
  * Falsa alarma (día): día sano con alguna alerta.  Episodio de falsa alarma: racha de días
    con alerta que empieza en un día sano; se informa por cada 30 días-astronauta sanos.
Métricas a nivel de EVENTO (sensibilidad, retraso) y a nivel de DÍA (falsas alarmas) por separado.

Protocolo: los cortes (yellow/red) y los umbrales del método B se AJUSTAN con TUNING_SEEDS y se
EVALÚAN con EVALUATION_SEEDS (misiones distintas). Ejecutar:  python -m basal.validation
"""
from __future__ import annotations

import json
import time
from dataclasses import replace

import numpy as np
import pandas as pd

from .config import EVALUATION_SEEDS, TUNING_SEEDS, VALIDATION_PATH, Params, save_params
from .detector import AMARILLO, ROJO, analyze_astronaut
from .indicators import INDICATORS, INDICATOR_KEYS
from .simulator import SCENARIOS, random_assignments, simulate_mission

DAYS = 120
METHODS = {"A_vigilar": "Individual · vigilar (amarillo o rojo)",
           "A_actuar": "Individual · actuar (rojo)",
           "B_fijo": "Referencia poblacional fija"}
YELLOW_GRID = [2.0, 2.5, 3.0]
RED_GRID = [3.0, 3.5, 4.0, 4.5]
MAX_FA_EPISODES_ACTUAR = 1.0  # restricción de ajuste: ≤ 1 episodio "actuar" falso por 30 días-astronauta


def make_missions(seeds, heterogeneity=1.0, missing_rate=0.0, only_scenario=None):
    """Genera misiones de validación reproducibles (una por semilla)."""
    out = []
    for s in seeds:
        rng = np.random.default_rng(10_000 + s)
        assign, crew_ev = random_assignments(rng, days=DAYS)
        if only_scenario:
            assign = {k: [{"escenario": only_scenario, "inicio": int(rng.integers(25, DAYS - 40))}]
                      for k in assign} if only_scenario != "D" else {k: [{"escenario": "A"}] for k in assign}
            crew_ev = [{"escenario": "D", "inicio": int(rng.integers(30, DAYS - 10))}] if only_scenario == "D" else []
        daily, events, _ = simulate_mission(days=DAYS, seed=s, assignments=assign, crew_events=crew_ev,
                                            heterogeneity=heterogeneity, intensity_range=(0.5, 1.5),
                                            missing_rate=missing_rate)
        out.append({"seed": s, "daily": daily, "events": events})
    return out


def population_reference(missions, window: int = 14) -> dict:
    """Método B: percentil 97,5 (si subir es malo) o 2,5 (si bajar es malo) de los días sanos."""
    vals = {k: [] for k in INDICATOR_KEYS}
    for m in missions:
        for astro_id, g in m["daily"].groupby("astro_id"):
            days = g["day"].to_numpy()
            sick = np.zeros(len(days), dtype=bool)
            for _, e in m["events"][m["events"].astro_id == astro_id].iterrows():
                sick |= (days >= e.start - 1) & (days <= e.end + 7)
            for k in INDICATOR_KEYS:
                x = g[k].to_numpy(dtype=float)[~sick]
                vals[k].extend(x[~np.isnan(x)].tolist())
    return {k: round(float(np.percentile(v, 97.5 if INDICATORS[k]["direction"] > 0 else 2.5)), 3)
            for k, v in vals.items()}


def _alerts(res, method):
    if method == "B_fijo":
        return {k: res[k]["fixed_alert"].to_numpy() == 1 for k in INDICATOR_KEYS}
    thr = AMARILLO if method == "A_vigilar" else ROJO
    return {k: res[k]["level"].to_numpy() >= thr for k in INDICATOR_KEYS}


def evaluate(missions, p: Params, methods=tuple(METHODS)) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (eventos, dias): registros detallados para agregar como se quiera."""
    ev_rows, day_rows = [], []
    for m in missions:
        for astro_id, g in m["daily"].groupby("astro_id"):
            g = g.set_index("day").sort_index()
            res = analyze_astronaut(g, p)
            days = g.index.to_numpy()
            evs = m["events"][m["events"].astro_id == astro_id]
            sick = np.zeros(len(days), dtype=bool)
            for _, e in evs.iterrows():
                sick |= (days >= e.start - 1) & (days <= e.end + 7)
            healthy = ~sick & (days >= p.window)
            for meth in methods:
                al = _alerts(res, meth)
                any_al = np.any(np.vstack(list(al.values())), axis=0)
                prev = np.concatenate([[False], any_al[:-1]])
                episodes = any_al & ~prev & healthy
                day_rows.append({"seed": m["seed"], "astro_id": astro_id, "metodo": meth,
                                 "dias_sanos": int(healthy.sum()), "fa_dias": int((any_al & healthy).sum()),
                                 "fa_episodios": int(episodes.sum()),
                                 **{f"fa_{k}": int((al[k] & healthy).sum()) for k in INDICATOR_KEYS}})
                for ei, (_, e) in enumerate(evs.iterrows()):
                    win = (days >= e.start) & (days <= e.end + 2)
                    keys = e.afecta.split(",")
                    hit = np.any(np.vstack([al[k] for k in keys]), axis=0) & win
                    first = int(days[hit][0] - e.start) if hit.any() else None
                    row = {"seed": m["seed"], "astro_id": astro_id, "ev": ei, "metodo": meth, "escenario": e.escenario,
                           "intensidad": e.intensidad, "detectado": first is not None, "retraso": first}
                    for k in INDICATOR_KEYS:  # detección por indicador afectado
                        row[f"det_{k}"] = bool((al[k] & win).any()) if k in keys else None
                    ev_rows.append(row)
    return pd.DataFrame(ev_rows), pd.DataFrame(day_rows)


def _summ(ev: pd.DataFrame, dy: pd.DataFrame) -> dict:
    det = ev[ev.detectado]
    dias = int(dy.dias_sanos.sum())
    return {
        "eventos": int(len(ev)), "detectados": int(len(det)),
        "sensibilidad_pct": round(100 * len(det) / max(len(ev), 1), 1),
        "retraso_medio_dias": round(float(det.retraso.mean()), 2) if len(det) else None,
        "retraso_mediano_dias": float(det.retraso.median()) if len(det) else None,
        "dias_sanos": dias,
        "falsas_alarmas_dias_pct": round(100 * dy.fa_dias.sum() / max(dias, 1), 1),
        "episodios_falsos_por_30_dias": round(30 * dy.fa_episodios.sum() / max(dias, 1), 2),
    }


def summarize(ev: pd.DataFrame, dy: pd.DataFrame) -> dict:
    out = {"global": {}, "por_escenario": {}, "por_indicador": {}, "anticipacion": {}}
    for meth in METHODS:
        e, d = ev[ev.metodo == meth], dy[dy.metodo == meth]
        if e.empty and d.empty:
            continue
        out["global"][meth] = _summ(e, d)
        out["por_escenario"][meth] = {
            sc: {**{k: v for k, v in _summ(g, d.iloc[0:0]).items() if k in
                    ("eventos", "detectados", "sensibilidad_pct", "retraso_medio_dias", "retraso_mediano_dias")}}
            for sc, g in e.groupby("escenario")}
        ind = {}
        dias = max(int(d.dias_sanos.sum()), 1)
        for k in INDICATOR_KEYS:
            col = e[f"det_{k}"].dropna() if f"det_{k}" in e else pd.Series(dtype=bool)
            ind[k] = {"eventos_que_lo_afectan": int(len(col)),
                      "sensibilidad_pct": round(100 * col.astype(bool).mean(), 1) if len(col) else None,
                      "falsas_alarmas_dias_pct": round(100 * d[f"fa_{k}"].sum() / dias, 2)}
        out["por_indicador"][meth] = ind
    # Anticipación: mismos eventos, A frente a B
    key = ["seed", "astro_id", "ev"]
    b = ev[ev.metodo == "B_fijo"].set_index(key)[["detectado", "retraso"]].rename(columns={"detectado": "detectado_b", "retraso": "retraso_b"})
    for meth in ("A_vigilar", "A_actuar"):
        a = ev[ev.metodo == meth].set_index(key)[["detectado", "retraso"]]
        if a.empty or b.empty:
            continue
        j = a.join(b, how="inner")
        both = j[j.detectado & j.detectado_b]
        diff = both.retraso_b - both.retraso
        out["anticipacion"][meth] = {
            "eventos_detectados_por_ambos": int(len(both)),
            "anticipacion_media_dias": round(float(diff.mean()), 2) if len(both) else None,
            "A_antes_que_B": int((diff > 0).sum()), "mismo_dia": int((diff == 0).sum()),
            "B_antes_que_A": int((diff < 0).sum()),
            "solo_A_detecta": int((j.detectado & ~j.detectado_b).sum()),
            "solo_B_detecta": int((~j.detectado & j.detectado_b).sum()),
        }
    return out


def tune(seeds=TUNING_SEEDS, base: Params | None = None, missions=None) -> tuple[Params, list]:
    """Ajusta cortes y umbrales del método B SOLO con las misiones de ajuste."""
    base = base or Params()
    missions = missions or make_missions(seeds)
    fixed = population_reference(missions, base.window)
    grid = []
    for y in YELLOW_GRID:
        for r in RED_GRID:
            if r <= y:
                continue
            p = replace(base, yellow=y, red=r, fixed=fixed)
            ev, dy = evaluate(missions, p, methods=("A_vigilar", "A_actuar"))
            sv = _summ(ev[ev.metodo == "A_vigilar"], dy[dy.metodo == "A_vigilar"])
            sa = _summ(ev[ev.metodo == "A_actuar"], dy[dy.metodo == "A_actuar"])
            grid.append({"yellow": y, "red": r, "vigilar": sv, "actuar": sa,
                         "cumple_restriccion": bool(sa["episodios_falsos_por_30_dias"] <= MAX_FA_EPISODES_ACTUAR)})
    ok = [g for g in grid if g["cumple_restriccion"]] or grid
    best = max(ok, key=lambda g: (g["actuar"]["sensibilidad_pct"], -(g["actuar"]["retraso_medio_dias"] or 99),
                                  -g["vigilar"]["episodios_falsos_por_30_dias"]))
    p = replace(base, yellow=best["yellow"], red=best["red"], fixed=fixed,
                origen=f"ajustado con semillas {seeds[0]}–{seeds[-1]} ({len(seeds)} misiones)")
    return p, grid


def run_custom(p: Params, n_missions=20, seed0=3000, scenario=None, heterogeneity=1.0, missing_rate=0.0) -> dict:
    """Experimento reproducible desde el Validation Lab (semillas elegidas por el usuario)."""
    t0 = time.time()
    seeds = list(range(seed0, seed0 + n_missions))
    missions = make_missions(seeds, heterogeneity, missing_rate, scenario)
    ev, dy = evaluate(missions, p)
    return {"parametros": {"yellow": p.yellow, "red": p.red, "persist": p.persist, "window": p.window,
                           "fixed": p.fixed},
            "semillas": [seeds[0], seeds[-1]], "misiones": n_missions, "astronautas": 4 * n_missions,
            "escenario": scenario or "mixto", "heterogeneidad": heterogeneity, "faltantes": missing_rate,
            "resultados": summarize(ev, dy), "segundos": round(time.time() - t0, 1)}


def heterogeneity_sweep(p: Params, levels=(0.25, 0.5, 1.0, 2.0), n=20) -> list:
    """¿En qué condiciones gana la línea base individual? Se varía la diferencia entre personas.
    El método B se re-estima para cada población (con semillas de ajuste) para ser justos."""
    rows = []
    for h in levels:
        ref = population_reference(make_missions(TUNING_SEEDS[:n], heterogeneity=h), p.window)
        ph = replace(p, fixed=ref)
        ev, dy = evaluate(make_missions(EVALUATION_SEEDS[:n], heterogeneity=h), ph)
        g = summarize(ev, dy)["global"]
        rows.append({"heterogeneidad": h, **{m: g[m] for m in g}})
    return rows


def main():
    t0 = time.time()
    print("1/4 Ajustando cortes con semillas de AJUSTE", TUNING_SEEDS[0], "-", TUNING_SEEDS[-1])
    p, grid = tune()
    for g in grid:
        print("   ", g["yellow"], g["red"], g["vigilar"]["sensibilidad_pct"], g["vigilar"]["episodios_falsos_por_30_dias"], g["actuar"]["sensibilidad_pct"], g["actuar"]["retraso_medio_dias"], g["actuar"]["episodios_falsos_por_30_dias"], g["actuar"]["falsas_alarmas_dias_pct"])
    print(f"    -> amarillo {p.yellow}, rojo {p.red}; método B: {p.fixed}")
    save_params(p, {"grid": grid, "restriccion": f"episodios falsos 'actuar' <= {MAX_FA_EPISODES_ACTUAR} / 30 días"})
    print("2/4 Evaluando con semillas de EVALUACIÓN", EVALUATION_SEEDS[0], "-", EVALUATION_SEEDS[-1])
    missions = make_missions(EVALUATION_SEEDS)
    ev, dy = evaluate(missions, p)
    main_res = summarize(ev, dy)
    print("3/4 Ablación (exclusión de alertas y línea base inicial)")
    abl = {}
    for name, pp in {"completo": p, "sin_excluir_alertas": replace(p, exclude_alerts=False),
                     "sin_linea_inicial": replace(p, use_initial=False),
                     "solo_ventana_movil": replace(p, exclude_alerts=False, use_initial=False)}.items():
        e2, d2 = evaluate(missions, pp, methods=("A_vigilar", "A_actuar"))
        abl[name] = summarize(e2, d2)["global"]
    print("4/4 Barrido de heterogeneidad entre personas")
    sweep = heterogeneity_sweep(p)
    out = {
        "generado": time.strftime("%Y-%m-%d %H:%M"),
        "protocolo": {"semillas_ajuste": [TUNING_SEEDS[0], TUNING_SEEDS[-1]],
                      "semillas_evaluacion": [EVALUATION_SEEDS[0], EVALUATION_SEEDS[-1]],
                      "misiones_evaluacion": len(EVALUATION_SEEDS), "astronautas_por_mision": 4,
                      "dias_por_mision": DAYS, "intensidad_eventos": "uniforme 0,5–1,5",
                      "restriccion_ajuste": f"episodios falsos 'actuar' <= {MAX_FA_EPISODES_ACTUAR} por 30 días-astronauta"},
        "parametros": p.to_dict(), "metodos": METHODS,
        "escenarios": {k: v["nombre"] for k, v in SCENARIOS.items()},
        "ajuste": grid, "evaluacion": main_res, "ablacion": abl, "heterogeneidad": sweep,
        "segundos": round(time.time() - t0, 1),
    }
    VALIDATION_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(main_res["global"], indent=2, ensure_ascii=False))
    print(json.dumps(main_res["anticipacion"], indent=2, ensure_ascii=False))
    print(f"Listo en {out['segundos']} s -> {VALIDATION_PATH}")


if __name__ == "__main__":
    main()

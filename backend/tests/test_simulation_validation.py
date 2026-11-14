"""Simulador reproducible (F9) y métricas de validación."""
import numpy as np
import pandas as pd

from basal.config import EVALUATION_SEEDS, TUNING_SEEDS, Params
from basal.simulator import simulate_mission
from basal.validation import _summ, evaluate, make_missions, population_reference, summarize


def test_simulation_is_reproducible():
    a = simulate_mission(seed=11)
    b = simulate_mission(seed=11)
    pd.testing.assert_frame_equal(a[0], b[0])
    pd.testing.assert_frame_equal(a[1], b[1])
    c = simulate_mission(seed=12)
    assert not a[0].equals(c[0])


def test_incomplete_scenario_has_missing_and_invalid():
    d, _, invalid = simulate_mission(seed=3, assignments={"A1": [{"escenario": "G"}]}, crew_events=[])
    a1 = d[d.astro_id == "A1"]
    assert a1[["rhr", "sleep"]].isna().any().any()
    assert len(invalid) > 0


def test_tuning_and_evaluation_seeds_are_disjoint():
    assert not set(TUNING_SEEDS) & set(EVALUATION_SEEDS)


def test_metrics_on_known_case():
    """Caso construido a mano: un evento evidente y ningún falso positivo esperado."""
    days = 60
    rng = np.random.default_rng(0)
    rows = []
    for d in range(days):
        rhr = 60 + rng.normal(0, 1.0) + (15 if 40 <= d <= 44 else 0)
        rows.append({"astro_id": "A1", "day": d, "rhr": round(rhr), "hrv": 50.0, "sleep": 7.0, "dose": 0.4,
                     "pvt": 1.0, "mood": 7.0})
    ev = pd.DataFrame([{"astro_id": "A1", "escenario": "C", "nombre": "x", "start": 40, "end": 44,
                        "afecta": "rhr,hrv", "intensidad": 1.0}])
    p = Params(yellow=2.5, red=3.5)
    e, dy = evaluate([{"seed": 0, "daily": pd.DataFrame(rows), "events": ev}], p)
    a = e[e.metodo == "A_actuar"].iloc[0]
    assert a.detectado and a.retraso == 0
    s = _summ(e[e.metodo == "A_actuar"], dy[dy.metodo == "A_actuar"])
    assert s["sensibilidad_pct"] == 100.0
    assert s["dias_sanos"] == (days - 14) - (44 + 7 - 39 + 1)


def test_population_reference_direction():
    ref = population_reference(make_missions(TUNING_SEEDS[:2]))
    assert ref["rhr"] > 60          # percentil alto: subir es malo
    assert ref["sleep"] < 6.9       # percentil bajo: bajar es malo


def test_summary_contains_breakdowns():
    ms = make_missions([5000, 5001])
    e, dy = evaluate(ms, Params())
    s = summarize(e, dy)
    assert set(s["global"]) == {"A_vigilar", "A_actuar", "B_fijo"}
    assert "por_escenario" in s and "por_indicador" in s and "anticipacion" in s

"""Pruebas del motor estadístico (F5 línea base, F6 detección)."""
import numpy as np
import pandas as pd
import pytest

from basal.config import Params
from basal.detector import (AMARILLO, CALIBRANDO, MAD_TO_SD, ROJO, SIN_DATO, VERDE, analyze_astronaut,
                            robust_stats, robust_z, score_indicator, theil_sen)
from basal.indicators import INDICATOR_KEYS

P = Params(yellow=2.5, red=3.5, persist=3)


def stable(n=40, base=60.0, seed=0, sd=1.5):
    return base + np.random.default_rng(seed).normal(0, sd, n)


def test_median_and_mad():
    med, mad = robust_stats(np.array([1.0, 2.0, 3.0, 4.0, 100.0]))
    assert med == 3.0
    # |x - 3| = 2,1,0,1,97 -> mediana 1 -> MAD escalado 1,4826
    assert mad == pytest.approx(1.0 * MAD_TO_SD)


def test_robust_z_formula_and_direction():
    assert robust_z(70, 60, 2.0, 1.0, +1) == pytest.approx(5.0)
    assert robust_z(50, 60, 2.0, 1.0, -1) == pytest.approx(5.0)   # bajar es malo -> positivo
    assert robust_z(70, 60, 2.0, 1.0, -1) == pytest.approx(-5.0)


def test_mad_zero_uses_min_spread():
    # Serie constante: MAD = 0. No debe dividir entre cero; usa min_spread (1 lpm para rhr)
    v = np.full(30, 60.0)
    v[25] = 63.0
    r = score_indicator(v, "rhr", P)
    assert np.isfinite(r.loc[25, "z"])
    assert r.loc[25, "z"] == pytest.approx(3.0)
    assert r.loc[25, "level"] == AMARILLO


def test_current_value_not_in_own_baseline():
    v = stable()
    w = v.copy()
    w[30] = 200.0
    a, b = score_indicator(v, "rhr", Params(use_initial=False)), score_indicator(w, "rhr", Params(use_initial=False))
    # La línea base del día 30 es idéntica cambie como cambie el valor del día 30
    assert a.loc[30, "normal"] == b.loc[30, "normal"]
    assert a.loc[30, "mad"] == b.loc[30, "mad"]
    assert b.loc[30, "level"] == ROJO


def test_insufficient_baseline_is_calibrating_not_green():
    v = stable(10)
    r = score_indicator(v, "rhr", P)
    assert (r.loc[:6, "level"] == CALIBRANDO).all()
    assert r.loc[:6, "z"].isna().all()


def test_missing_values_are_not_healthy():
    v = stable()
    v[20] = np.nan
    r = score_indicator(v, "rhr", P)
    assert r.loc[20, "level"] == SIN_DATO
    assert np.isnan(r.loc[20, "z"])


def test_abrupt_change_detected_red():
    v = stable(50)
    v[35:40] += 15
    r = score_indicator(v, "rhr", P)
    assert r.loc[35, "level"] == ROJO


def test_gradual_change_detected_via_initial_baseline():
    v = stable(90, sd=1.0)
    v[30:] += np.linspace(0, 12, 60)  # +0,2 lpm/día: lento
    r = score_indicator(v, "rhr", P)
    assert (r.loc[60:, "level"] >= AMARILLO).any()
    # Sin la línea base inicial, la ventana móvil detecta menos (absorbe la deriva)
    r2 = score_indicator(v, "rhr", Params(yellow=2.5, red=3.5, use_initial=False, exclude_alerts=False))
    assert (r.loc[30:, "level"] >= AMARILLO).sum() > (r2.loc[30:, "level"] >= AMARILLO).sum()


def test_persistent_anomaly_not_absorbed_into_baseline():
    v = stable(60, sd=1.0)
    v[30:] += 8  # deterioro sostenido
    r = score_indicator(v, "rhr", P)
    # Los días en alerta no entran en la línea base: sigue cerca del valor previo
    assert r.loc[50, "normal"] < 62
    assert r.loc[50, "level"] >= AMARILLO


def test_yellow_persistence_escalates_to_red():
    v = np.full(40, 60.0) + np.tile([0.0, 0.5, -0.5, 0.2], 10)
    v[30:34] = v[29] + 3.0  # z ~ entre 2,5 y 3,5 varios días
    r = score_indicator(v, "rhr", Params(yellow=2.5, red=3.5, persist=3, use_initial=False))
    lv = r.loc[30:33, "level"].tolist()
    assert lv[0] == AMARILLO and ROJO in lv[2:]
    assert r.loc[32, "reason"] == "persistencia"


def test_fixed_comparator():
    v = np.array([60.0, 80.0, 70.0])
    r = score_indicator(v, "rhr", Params(fixed={**Params().fixed, "rhr": 72.0}))
    assert r["fixed_alert"].tolist() == [0, 1, 0]


def test_theil_sen_slope():
    assert theil_sen(np.array([1.0, 2.0, 3.0, 100.0, 5.0])) == pytest.approx(1.0)


def test_profiles_are_independent():
    df1 = pd.DataFrame({k: stable(40, seed=i) for i, k in enumerate(INDICATOR_KEYS)})
    df2 = df1.copy()
    df2["rhr"] = df2["rhr"] + 30  # otra persona con FC basal más alta
    r1, r2 = analyze_astronaut(df1, P), analyze_astronaut(df2, P)
    # Desplazar a una persona no cambia sus z: cada uno se compara consigo mismo
    assert np.allclose(r1["rhr"]["z"].dropna(), r2["rhr"]["z"].dropna())

"""Parámetros configurables del motor de detección.

Los cortes del semáforo NO son límites médicos: son parámetros experimentales del prototipo.
Se ajustan con un conjunto de semillas (AJUSTE) y se evalúan con otro distinto (EVALUACIÓN)
mediante `python -m basal.validation`, que escribe data/config.json.
Si el archivo no existe se usan los valores por defecto de abajo.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
CONFIG_PATH = DATA_DIR / "config.json"
VALIDATION_PATH = DATA_DIR / "validation_results.json"

# Semillas separadas: nunca se ajusta y evalúa con las mismas misiones
TUNING_SEEDS = list(range(1000, 1020))      # 20 misiones x 4 astronautas
EVALUATION_SEEDS = list(range(2000, 2040))  # 40 misiones x 4 astronautas


@dataclass
class Params:
    window: int = 14          # días previos en la línea base reciente
    min_periods: int = 7      # observaciones válidas mínimas para evaluar (si no: "calibrando")
    yellow: float = 2.5       # |z| para "vigilar"
    red: float = 3.5          # |z| para "actuar"
    persist: int = 3          # días seguidos en amarillo que escalan a rojo
    exclude_alerts: bool = True   # los días en alerta no entran en la línea base
    use_initial: bool = True      # además, comparar con los primeros 14 días válidos de misión
    # Comparador B: intervalo de referencia poblacional (estimado en el conjunto de ajuste)
    fixed: dict = field(default_factory=lambda: {
        "rhr": 72.0, "hrv": 25.0, "sleep": 6.0, "dose": 0.5, "pvt": 5.0, "mood": 5.5,
    })
    origen: str = "default values (not tuned)"

    def to_dict(self) -> dict:
        return asdict(self)


def load_params() -> Params:
    if CONFIG_PATH.exists():
        try:
            raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            known = {k: v for k, v in raw.get("params", {}).items() if k in Params.__dataclass_fields__}
            return Params(**known)
        except (ValueError, TypeError):
            pass
    return Params()


def save_params(p: Params, extra: dict | None = None) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    CONFIG_PATH.write_text(json.dumps({"params": p.to_dict(), **(extra or {})}, indent=2, ensure_ascii=False),
                           encoding="utf-8")

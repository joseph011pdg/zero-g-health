# BASAL · Monitoreo de salud autónomo para astronautas

Hackatón NASA Space Apps 2026 (reto: health monitoring software). **Entrega: dom 15/11/2026 23:59 (Ecuador).**
Equipo de 2. Todo en español (código, interfaz, docs; resumen en inglés en README).
Avance y pendientes: **PROGRESS.md** (actualizar al terminar cada fase).

## Idea
A bordo y sin conexión: línea base de **cada** astronauta, detecta cuándo un indicador deja de ser lo habitual para
esa persona y explica qué cambió, cuánto, cómo se detectó, qué seguimiento hacer y con qué fuente.

## Decisiones (no cambiar sin consultar)
- Análisis solo con pandas y NumPy. Sin ML ni LLM (no hay datos reales para validarlos). Sin voz (mejora futura).
- Backend FastAPI + SQLite; frontend Vue 3 + Vite (JS) + Pinia + Vue Router + ECharts + vite-plugin-pwa. Sin Docker.
- FastAPI sirve `frontend/dist` en un solo origen; escucha solo en 127.0.0.1.
- Cortes del semáforo = parámetros (`basal/data/config.json`), ajustados con semillas 1000–1019 y evaluados con
  2000–2039 (`python -m basal.validation`). Actuales: vigilar 2,5 · actuar 4,5 o 3 días en vigilar.
- Método B (comparador) = intervalo de referencia poblacional (P2,5/P97,5 de días sanos del conjunto de ajuste).
- Máximo 6 pantallas. Documentación mínima: README, SCIENTIFIC_METHOD, DEMO_SCRIPT, JUDGES_QA (+ PROGRESS).
- No crear subagentes ni skills. P2 (voz, predicción, integraciones) fuera de alcance.

## Mapa del código
- `backend/basal/indicators.py` 6 indicadores (dirección, unidades, rangos plausibles, min_spread, ref. clínica).
- `config.py` Params + semillas. `simulator.py` escenarios A–G, misión demo (4 astronautas ficticios, eventos fijos).
- `detector.py` línea base secuencial (excluye hoy y días en alerta; calibrando/sin_dato; línea inicial; persistencia).
- `ingest.py` validación F2 + CSV. `db.py` esquema SQLite (formato largo con origen). `recommender.py` alertas F7.
- `services.py` une capas (caché por versión de datos, alertas persistentes con estado, reportes y cola, demo).
- `main.py` rutas REST (OpenAPI en /docs). `validation.py` ajuste, evaluación, ablación, barrido de heterogeneidad.
- `frontend/src/views`: Overview (01 + oficial médico), Health (02 + alertas), Registro (03 check-in, PVT-B, ingesta),
  Simulator (04), Validation (05), Reports (06 reportes + ciencia). `components/GuidedDemo.vue` demo de 9 pasos.

## Comandos (Windows, PowerShell)
```powershell
.\scripts\setup.ps1          # venv + pip + npm ci + build (única vez, con Internet)
.\scripts\start.ps1 [-Reset] # http://127.0.0.1:8000 (sin Internet). -Reset recarga la misión demo
.\scripts\test.ps1           # pytest (30) + build
cd backend; .venv\Scripts\python -m basal.validation   # regenera config.json y validation_results.json (~3 min)
```
Pruebas usan base temporal (`BASAL_DB`). La base real es `backend/basal.db` (se crea sola, ignorada por git).

## Reglas
- No inventar datos, umbrales médicos, referencias ni métricas. Toda cifra de docs sale de validation_results.json.
- Recomendaciones = seguimiento conservador; rojas → oficial médico y protocolos. Nunca diagnóstico ni fármacos.
- Niveles nunca solo por color (icono + texto). Ausencia de datos ≠ normal.
- Si se cambia el detector o el simulador: regenerar la validación y actualizar las cifras de README/SCIENTIFIC_METHOD/DEMO_SCRIPT/JUDGES_QA.

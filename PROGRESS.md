# PROGRESS · BASAL

Registro de avance por fases (para retomar si la sesión se interrumpe). Fecha límite: dom 15/11/2026 23:59 (Ecuador).

## Estado: MVP completo y verificado localmente (14/11/2026)

### Fase 0 — Diagnóstico ✅
- Windows 11, Python 3.14.5 (no hay 3.12 instalado; todo funciona con 3.14), Node 24.16, npm 12.2, Git 2.55.
- La carpeta del proyecto **no es un repositorio git** todavía.

### Fase 1–2 — Motor científico ✅
- `detector.py` reescrito: línea base secuencial que excluye el día actual y los días en alerta, amplía la ventana si
  faltan datos, estados `calibrando` / `sin_dato`, línea base inicial, persistencia, Theil–Sen, calidad.
- `simulator.py`: escenarios A–G con semilla, heterogeneidad configurable, misión demo con eventos en días fijos
  (A1 fatiga D44, A3 estrés D70, A4 conductual D52, evento solar D86, apagón D95–104).
- `validation.py`: ajuste (1000–1019) ≠ evaluación (2000–2039); métricas por evento y por día, por escenario,
  indicador, anticipación, ablación y barrido de heterogeneidad. Cortes resultantes 2,5 / 4,5.

### Fase 3 — Backend ✅
- SQLite en formato largo con origen por medición; ingesta validada (`ingest.py`) con log de rechazos; alertas
  persistentes con estado de revisión; reportes con cola diferida que respeta el apagón; CSV export; perfiles nuevos;
  validación a demanda (`POST /api/validation/run`) y por astronauta (`GET /api/validation/demo`).
- Corregido: escribir el día de misión invalidaba la caché del análisis (crew pasaba de 21 ms a 430 ms).

### Fase 4 — Frontend ✅ (6 pantallas)
- 01 Misión + oficial médico · 02 Salud + alertas · 03 Check-in + PVT-B + ingesta manual/CSV · 04 Simulador ·
  05 Validation Lab · 06 Reportes + ciencia. Cabecera de misión (día, fecha simulada, astronauta, enlace, sistema
  local), control de día, demo guiada de 9 pasos, toasts, aviso si el motor local no responde.
- Sistema de diseño propio con la paleta del brief; niveles con icono + texto; sin fuentes ni CDN externos.

### Fase 5–6 — Integración y pruebas ✅
- `scripts/test.ps1`: 30 pruebas pytest pasan + build OK.
- `scripts/setup.ps1` ejecutado de punta a punta en PowerShell 5.1; `scripts/start.ps1` arranca y sirve UI + API.
- Revisado en el navegador: las 6 pantallas sin errores de consola; demo guiada pasos 1–5 con clics reales;
  generación de reporte desde la UI; sin desbordamiento horizontal a 375 px; bundle sin URLs externas.

### Fase 8 — Documentación ✅
- README (con resumen en inglés), SCIENTIFIC_METHOD, DEMO_SCRIPT, JUDGES_QA, CLAUDE.md actualizado.

### Despliegue ✅ preparado
- `render.yaml` (Python 3.12.8, plan free), modo público `BASAL_PUBLIC=1` probado localmente, `frontend/dist` versionado.
- Repositorio git inicializado (rama `main`, autor provisional "Equipo BASAL" <basal-team@users.noreply.github.com>).

## Pendiente (equipo)
- [ ] Crear repositorio en GitHub, `git push`, y en Render: New → Blueprint (requiere iniciar sesión).
- [ ] Ensayar la demo con el guion y grabar el video (2–3 min); capturas para la entrega.
- [ ] Revisar la página oficial del reto y los campos de entrega de Space Apps 2026 (no verificados en esta sesión).
- [ ] Verificar DOIs añadidos (Basner 2011, Watson 2015) y el intervalo 2–5 s de PVT-B en el artículo original.
- [ ] Revisión de las reglas de `recomendaciones.json` por alguien con formación médica, si es posible.
- [ ] Actualizar `docs/propuesta.tex` con los cortes finales (2,5 / 4,5) y la tabla de validación.
- [ ] (Opcional) Integrar algún dataset NASA OSDR real vía CSV si hay variables individuales disponibles.

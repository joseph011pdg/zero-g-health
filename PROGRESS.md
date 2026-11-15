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

### Rediseño ✅ (14/11 noche)
- Tema claro blanco/azul NASA, 2 menús, Check-in/PVT como paneles en Persona, alerta resumida con "¿Por qué?",
  franja Tierra–Marte (fotos NASA de dominio público) que también controla el día, retratos ilustrados.
- Revisado en navegador a 1400 px y 375 px sin desbordamiento ni errores de consola.

### Mejoras profesionales ✅ (14/11 noche)
- Rol Astronauta / Oficial médico; línea de respuesta; alarmas por prioridad con reconocer/posponer por episodio,
  revisor y aviso de escalado (backend + prueba); menos rojo; gráfica con banda normal y frescura del dato;
  franja Tierra–Marte con hitos y cuenta del apagón. 31 pruebas pasan; revisado a 1400 y 375 px.

### Diseño "Informe científico" ✅ (14/11 noche)
- Elegido por el usuario con la skill impeccable: titular serif, botones de acción en lista, foto de cúpula con texto,
  trayectoria, tripulación como filas con figura, alarmas como hallazgos, tabla de enlace. Sin rojo (ámbar oscuro).
- Detector de la skill sin hallazgos en los archivos cambiados; revisado a 1400 y 375 px.
- Foto de la cúpula sustituida por la original de NASA (ISS-43, NASA/Scott Kelly, dominio público, 1600 px),
  con crédito en la imagen y en Ciencia.
- El service worker no se registró en el navegador del panel de pruebas (sí antes); no verificado en un navegador normal.

### Ajustes visuales ✅ (14/11 noche)
- Corregido: el panel de la demo guiada se rompía (choque de nombre de clase con el botón de la cabecera).
- Portada: video real de NASA (“ISS Fly-Through to Cupola”, tramo de la Tierra bajo la estación, 0,7×, 1280×720,
  8,6 MB) en bucle con fundido; foto fija si el sistema pide reducir movimiento. Sin crédito sobre la imagen
  (créditos en Ciencia). Versiones 1080p de las opciones A, B y C en `videos/` (fuera de git).
- Franja Tierra–Marte: globos que giran con planisferios reales (Blue Marble, Viking MDIM21).
- Menú y barras de título en azul marino (#0a1f44); azul NASA para botones y datos.

### Revisión de Katherine aplicada ✅ (15/11)
- P0: titular según alarmas abiertas; "Hoy: normal · alerta del día X sigue abierta"; alarmas con indicador, valor
  frente a su normal, z, desde cuándo, acción y nota al reconocer; demo en el día 40 (el falso positivo del día 32
  queda fuera de la portada y se explica en el guion); coma decimal en toda la interfaz y gráficas; plurales,
  "Lapsos PVT"; etiquetas de la trayectoria en dos filas en móvil (revisado a 360 px); estado por sesión en la demo
  pública (cabeceras `X-Basal-Dia`/`X-Basal-Apagon`, reconocimientos en el navegador, "Restablecer demo");
  keep-alive con GitHub Actions y mensaje "Despertando el servidor…".
- P1: bloque problema/solución/prueba; botones Demo guiada, Simular apagón y escenarios B/C/D; seis puntos por
  tripulante; radiación como % de lo esperado a hoy (mGy vs mSv); reporte de ejemplo precargado y vista previa;
  página `/en` y resumen en inglés del README ampliado.
- P2: respuestas a debilidades en JUDGES_QA (cifras verificadas en validation_results.json).
- P3: título de pestaña por vista.
- 32 pruebas pytest pasan.
- Pendiente: invitar a Katherine (abbydpk-oss) como colaboradora en GitHub (requiere iniciar sesión).

### Todo en inglés ✅ (15/11 tarde)
- Interfaz completa en inglés (sin i18n: solo inglés, por tiempo), textos del backend (alertas, acciones, evidencia,
  escenarios, indicadores, mensajes de error), etiquetas de validación (solo texto; cifras sin cambios), lpm → bpm,
  punto decimal (en-US). Rutas en inglés con redirección de las antiguas.
- Docs en inglés: README, SCIENTIFIC_METHOD, DEMO_SCRIPT, JUDGES_QA (copias en español `*_ES.md`). Falsa alarma del
  día 32 (A4, PVT, z = 4,5, sin evento hasta el día 52) explicada en DEMO_SCRIPT, JUDGES_QA y SCIENTIFIC_METHOD.
- Portada: avisos ordenados por z (2 visibles + "N more notices"), leyenda "Act = notify the Medical Officer · Watch =
  repeat the measurement". Móvil: cabecera compacta, franja de demo en una línea, Check-in/PVT 50/50, tablas con
  scroll horizontal; sin desborde en 360/390/430 px en todas las rutas.
- PWA: skipWaiting + clientsClaim + cleanupOutdatedCaches (autoUpdate); /api fuera del caché.
- Keep-alive de GitHub Actions activo, pero GitHub lo ejecuta con poca frecuencia (2 corridas el 15/11): conviene un
  monitor externo (p. ej. UptimeRobot) además.
- 32 pruebas pytest pasan.

## Pendiente (equipo)
- [x] Publicado: https://github.com/joseph011pdg/basal (público) y https://basal-pxyn.onrender.com (Render, plan free,
      modo público). Cada push a `main` redespliega; recompilar `frontend/dist` antes si cambia la interfaz.
- [ ] Ensayar la demo con el guion y grabar el video (2–3 min); capturas para la entrega.
- [ ] Revisar la página oficial del reto y los campos de entrega de Space Apps 2026 (no verificados en esta sesión).
- [ ] Verificar DOIs añadidos (Basner 2011, Watson 2015) y el intervalo 2–5 s de PVT-B en el artículo original.
- [ ] Revisión de las reglas de `recomendaciones.json` por alguien con formación médica, si es posible.
- [ ] Actualizar `docs/propuesta.tex` con los cortes finales (2,5 / 4,5) y la tabla de validación.
- [ ] (Opcional) Integrar algún dataset NASA OSDR real vía CSV si hay variables individuales disponibles.
